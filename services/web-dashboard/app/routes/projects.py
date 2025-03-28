from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from uuid import UUID
from datetime import datetime, timedelta

from app.api.clients import get_project_coordinator_client, get_agent_orchestrator_client, get_planning_system_client
from app.api.base import APIError

def calculate_project_health(project):
    """
    Calculate project health indicators based on project data.
    
    Args:
        project (dict): Project data
        
    Returns:
        dict: Project health indicators
    """
    # Get project metadata
    metadata = project.get('metadata', {})
    progress = metadata.get('progress', 0)
    deadline_str = metadata.get('deadline', '')
    
    # Calculate schedule health
    schedule_health = {
        'status': 'On Track',
        'color': 'green'
    }
    
    if deadline_str:
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            today = datetime.now()
            days_remaining = (deadline - today).days
            
            # Calculate expected progress based on time elapsed
            created_at = datetime.fromisoformat(project.get('created_at', today.isoformat()).replace('Z', '+00:00'))
            total_days = (deadline - created_at).days
            days_elapsed = (today - created_at).days
            
            if total_days > 0:
                expected_progress = min(100, max(0, (days_elapsed / total_days) * 100))
                
                # If progress is significantly behind schedule
                if progress < expected_progress - 20:
                    schedule_health = {
                        'status': 'Behind Schedule',
                        'color': 'red'
                    }
                # If progress is slightly behind schedule
                elif progress < expected_progress - 10:
                    schedule_health = {
                        'status': 'At Risk',
                        'color': 'yellow'
                    }
            
            # If deadline is very close but progress is not near completion
            if days_remaining < 3 and progress < 90:
                schedule_health = {
                    'status': 'Critical',
                    'color': 'red'
                }
            # If deadline is close but progress is not on track
            elif days_remaining < 7 and progress < 70:
                schedule_health = {
                    'status': 'At Risk',
                    'color': 'yellow'
                }
        except (ValueError, TypeError):
            # If deadline is not a valid date
            schedule_health = {
                'status': 'Unknown',
                'color': 'yellow'
            }
    
    # Calculate resource health based on assigned agents
    agents = project.get('agents', [])
    resource_health = {
        'status': 'Adequate',
        'color': 'green'
    }
    
    if len(agents) == 0:
        resource_health = {
            'status': 'No Resources',
            'color': 'red'
        }
    elif len(agents) < 2:
        resource_health = {
            'status': 'Limited',
            'color': 'yellow'
        }
    
    # Calculate quality health based on task completion
    tasks = project.get('tasks', [])
    completed_tasks = sum(1 for task in tasks if task.get('status') == 'COMPLETED')
    total_tasks = len(tasks)
    
    quality_health = {
        'status': 'Good',
        'color': 'green'
    }
    
    if total_tasks > 0:
        completion_rate = completed_tasks / total_tasks
        if completion_rate < 0.3:
            quality_health = {
                'status': 'Poor',
                'color': 'red'
            }
        elif completion_rate < 0.6:
            quality_health = {
                'status': 'Fair',
                'color': 'yellow'
            }
    
    # Calculate overall health
    overall_color = 'green'
    if schedule_health['color'] == 'red' or resource_health['color'] == 'red' or quality_health['color'] == 'red':
        overall_color = 'red'
    elif schedule_health['color'] == 'yellow' or resource_health['color'] == 'yellow' or quality_health['color'] == 'yellow':
        overall_color = 'yellow'
    
    overall_status = 'Healthy'
    if overall_color == 'red':
        overall_status = 'Critical'
    elif overall_color == 'yellow':
        overall_status = 'At Risk'
    
    return {
        'schedule': schedule_health,
        'resources': resource_health,
        'quality': quality_health,
        'overall': {
            'status': overall_status,
            'color': overall_color
        }
    }

def generate_progress_data(project, tasks):
    """
    Generate progress data for the chart.
    
    Args:
        project (dict): Project data
        tasks (list): Project tasks
        
    Returns:
        dict: Progress data for the chart
    """
    # Get project metadata
    metadata = project.get('metadata', {})
    current_progress = metadata.get('progress', 0)
    deadline_str = metadata.get('deadline', '')
    created_at_str = project.get('created_at')
    
    # Parse dates
    today = datetime.now()
    
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        created_at = today - timedelta(days=30)  # Default to 30 days ago
    
    try:
        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        deadline = today + timedelta(days=30)  # Default to 30 days from now
    
    # Generate dates between created_at and deadline
    dates = []
    current_date = created_at
    while current_date <= deadline:
        dates.append(current_date.isoformat())
        current_date += timedelta(days=1)
    
    # Generate planned progress (linear from 0 to 100)
    total_days = (deadline - created_at).days
    if total_days <= 0:
        total_days = 1  # Avoid division by zero
    
    planned_progress = []
    for i, date in enumerate(dates):
        day = i
        progress = min(100, max(0, (day / total_days) * 100))
        planned_progress.append(progress)
    
    # Generate actual progress based on task completion
    actual_progress = []
    
    # Sort tasks by completion date
    completed_tasks = [task for task in tasks if task.get('status') == 'COMPLETED']
    completed_tasks.sort(key=lambda x: x.get('completed_at', ''))
    
    # Calculate progress over time
    progress_over_time = {}
    cumulative_progress = 0
    
    for task in completed_tasks:
        completed_at = task.get('completed_at')
        if completed_at:
            try:
                completed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).date().isoformat()
                task_progress = task.get('metadata', {}).get('progress_contribution', 1)
                
                if completed_date in progress_over_time:
                    progress_over_time[completed_date] += task_progress
                else:
                    progress_over_time[completed_date] = task_progress
            except (ValueError, TypeError):
                pass
    
    # Fill in actual progress
    for date in dates:
        date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
        date_str = date_obj.date().isoformat()
        
        if date_str in progress_over_time:
            cumulative_progress += progress_over_time[date_str]
        
        # Scale cumulative progress to 0-100 range
        scaled_progress = min(100, max(0, (cumulative_progress / len(tasks)) * 100)) if tasks else 0
        
        # If date is in the future, use current progress
        if date_obj.date() > today.date():
            actual_progress.append(current_progress)
        else:
            actual_progress.append(scaled_progress)
    
    # Ensure the last actual progress matches the current progress
    if actual_progress:
        actual_progress[-1] = current_progress
    
    return {
        'dates': dates,
        'planned': planned_progress,
        'actual': actual_progress
    }

def generate_agent_timeline(agents, tasks):
    """
    Generate agent timeline data for the chart.
    
    Args:
        agents (list): Project agents
        tasks (list): Project tasks
        
    Returns:
        list: Agent timeline data for the chart
    """
    # Create a map of agent IDs to names
    agent_map = {agent.get('id'): agent.get('name') for agent in agents}
    
    # Filter tasks with assigned agents and start/end dates
    agent_tasks = []
    
    for task in tasks:
        agent_id = task.get('assigned_agent_id')
        if not agent_id:
            continue
        
        agent_name = agent_map.get(agent_id, f"Agent {agent_id}")
        
        # Get task start and end dates
        start_date = task.get('created_at')
        if not start_date:
            continue
        
        # Use completed_at as end date if available, otherwise use deadline or today
        end_date = task.get('completed_at')
        if not end_date:
            end_date = task.get('metadata', {}).get('deadline')
        
        if not end_date:
            end_date = datetime.now().isoformat()
        
        # Add task to agent tasks
        agent_tasks.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'task_id': task.get('id'),
            'task_name': task.get('name'),
            'start_date': start_date,
            'end_date': end_date
        })
    
    # Generate timeline data
    timeline_data = []
    
    for i, agent in enumerate(agents):
        agent_id = agent.get('id')
        agent_name = agent.get('name')
        
        # Get tasks for this agent
        agent_task_list = [task for task in agent_tasks if task.get('agent_id') == agent_id]
        
        # Add tasks to timeline
        for task in agent_task_list:
            timeline_data.append({
                'label': agent_name,
                'data': [{
                    'x': [task.get('start_date'), task.get('end_date')],
                    'y': agent_name,
                    'task': task.get('task_name')
                }],
                'backgroundColor': f'hsl({(i * 137) % 360}, 70%, 60%)'
            })
    
    return timeline_data

def get_recent_agent_activities(activities, agents):
    """
    Get recent agent activities.
    
    Args:
        activities (list): Project activities
        agents (list): Project agents
        
    Returns:
        list: Recent agent activities
    """
    # Create a map of agent IDs to names
    agent_map = {agent.get('id'): agent.get('name') for agent in agents}
    
    # Filter activities related to agents
    agent_activities = []
    
    for activity in activities:
        agent_id = activity.get('agent_id')
        if not agent_id:
            continue
        
        agent_name = agent_map.get(agent_id, f"Agent {agent_id}")
        
        # Format timestamp
        timestamp = activity.get('timestamp')
        if timestamp:
            try:
                timestamp_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = timestamp_obj.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = 'Unknown'
        
        # Add activity to agent activities
        agent_activities.append({
            'agent_id': agent_id,
            'agent_name': agent_name,
            'description': activity.get('description', 'Unknown activity'),
            'timestamp': formatted_timestamp
        })
    
    # Sort activities by timestamp (newest first) and limit to 10
    agent_activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return agent_activities[:10]

def register_routes(app):
    """Register project routes with the Flask app."""
    
    @app.route('/projects/<uuid:project_id>/progress')
    @login_required
    def project_progress(project_id):
        """Render the project progress visualization page."""
        try:
            # Get project details from the API
            project_client = get_project_coordinator_client()
            project = project_client.get_project(project_id)
            
            # Get project tasks
            tasks = project_client.get_project_tasks(project_id)
            
            # Get agents assigned to the project
            agents = project_client.get_project_agents(project_id)
            
            # Get project activities
            activities = project_client.get_project_activities(project_id).get('items', [])
            
            # Add tasks and agents to the project data
            project['tasks'] = tasks
            project['agents'] = agents
            
            # Get project alerts from the agent orchestrator
            agent_client = get_agent_orchestrator_client()
            project_alerts = []
            try:
                alerts_response = agent_client.get(f'/alerts/active', params={'project_id': str(project_id)})
                if alerts_response:
                    project_alerts = alerts_response
                    
                    # Add severity class for styling
                    for alert in project_alerts:
                        severity = alert.get('alert_configuration', {}).get('severity', 'INFO')
                        if severity == 'INFO':
                            alert['severity_class'] = 'info'
                        elif severity == 'WARNING':
                            alert['severity_class'] = 'warning'
                        elif severity == 'ERROR':
                            alert['severity_class'] = 'danger'
                        elif severity == 'CRITICAL':
                            alert['severity_class'] = 'dark'
                        else:
                            alert['severity_class'] = 'secondary'
            except APIError as e:
                current_app.logger.error(f'Error loading project alerts: {e.message}')
            
            # Calculate project health indicators
            project_health = calculate_project_health(project)
            
            # Count completed and pending tasks
            completed_tasks = sum(1 for task in tasks if task.get('status') == 'COMPLETED')
            pending_tasks = len(tasks) - completed_tasks
            
            # Generate progress data for the chart
            progress_data = generate_progress_data(project, tasks)
            
            # Generate agent timeline data
            agent_timeline = generate_agent_timeline(agents, tasks)
            
            # Get recent agent activities
            agent_activities = get_recent_agent_activities(activities, agents)
            
            return render_template('projects/project_progress.html', 
                                  project=project,
                                  project_alerts=project_alerts,
                                  project_health=project_health,
                                  completed_tasks=completed_tasks,
                                  pending_tasks=pending_tasks,
                                  progress_data=progress_data,
                                  agent_timeline=agent_timeline,
                                  agent_activities=agent_activities)
        
        except APIError as e:
            flash(f'Error loading project: {e.message}', 'danger')
            return redirect(url_for('projects_list'))
    
    @app.route('/projects')
    @login_required
    def projects_list():
        """Render the projects list page."""
        # Get query parameters for filtering and sorting
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort = request.args.get('sort', 'updated_desc')
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
        
        try:
            # Get projects from the API
            client = get_project_coordinator_client()
            result = client.get_projects(search=search, status=status, sort=sort, page=page, per_page=per_page)
            
            # Extract projects and pagination data
            projects = result.get('items', [])
            pagination = {
                'page': result.get('page', 1),
                'per_page': result.get('per_page', per_page),
                'total': result.get('total', 0),
                'pages': result.get('pages', 1)
            }
            
            return render_template('projects/index.html', projects=projects, pagination=pagination, 
                                search=search, status=status, sort=sort)
        
        except APIError as e:
            flash(f'Error loading projects: {e.message}', 'danger')
            return render_template('projects/index.html', projects=[], pagination={
                'page': 1, 'per_page': per_page, 'total': 0, 'pages': 1
            })

    @app.route('/projects/<uuid:project_id>')
    @login_required
    def project_detail(project_id):
        """Render the project detail page."""
        try:
            # Get project details from the API
            project_client = get_project_coordinator_client()
            project = project_client.get_project(project_id)
            
            # Get project tasks
            tasks = project_client.get_project_tasks(project_id)
            
            # Get agents assigned to the project
            agents = project_client.get_project_agents(project_id)
            
            # Get project activities
            activities = project_client.get_project_activities(project_id).get('items', [])
            
            # Add tasks and agents to the project data
            project['tasks'] = tasks
            project['agents'] = agents
            project['activities'] = activities
            
            return render_template('projects/detail.html', project=project)
        
        except APIError as e:
            flash(f'Error loading project: {e.message}', 'danger')
            return redirect(url_for('projects_list'))

    @app.route('/projects/new', methods=['GET', 'POST'])
    @login_required
    def new_project():
        """Render the new project request form and handle form submission."""
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            project_type = request.form.get('project_type')
            goals = request.form.get('goals')
            constraints = request.form.get('constraints')
            requirements = request.form.get('requirements')
            status = request.form.get('status')
            priority = request.form.get('priority')
            tags = request.form.get('tags')
            deadline = request.form.get('deadline')
            agent_ids = request.form.getlist('agents')
            
            # Validate form data
            if not name or not description or not goals:
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('new_project'))
            
            try:
                # Create metadata with additional fields
                metadata = {
                    'priority': priority,
                    'tags': tags.split(',') if tags else [],
                    'deadline': deadline,
                    'progress': request.form.get('progress', 0, type=int),
                    'project_type': project_type,
                    'goals': goals,
                    'constraints': constraints,
                    'requirements': requirements
                }
                
                # Create project via the API
                client = get_project_coordinator_client()
                project = client.create_project(
                    name=name,
                    description=description,
                    status=status,
                    metadata=metadata
                )
                
                # Assign agents to the project if any were selected
                project_id = project.get('id')
                if project_id and agent_ids:
                    for agent_id in agent_ids:
                        try:
                            client.assign_agent_to_project(project_id, agent_id)
                        except APIError as e:
                            current_app.logger.error(f'Error assigning agent {agent_id} to project {project_id}: {e.message}')
                
                flash('Project created successfully!', 'success')
                return redirect(url_for('project_detail', project_id=project_id))
            
            except APIError as e:
                flash(f'Error creating project: {e.message}', 'danger')
                return redirect(url_for('new_project'))
        
        # GET request - render the form
        try:
            # Get available agents from the API
            agent_client = get_agent_orchestrator_client()
            agents = agent_client.get_available_agents()
            
            return render_template('projects/new_project_request.html', agents=agents)
        
        except APIError as e:
            flash(f'Error loading agents: {e.message}', 'warning')
            return render_template('projects/new_project_request.html', agents=[])

    @app.route('/projects/<uuid:project_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_project(project_id):
        """Render the edit project form and handle form submission."""
        try:
            # Get project details from the API
            project_client = get_project_coordinator_client()
            project = project_client.get_project(project_id)
            
            if request.method == 'POST':
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                status = request.form.get('status')
                priority = request.form.get('priority')
                tags = request.form.get('tags')
                deadline = request.form.get('deadline')
                agent_ids = request.form.getlist('agents')
                progress = request.form.get('progress', 0, type=int)
                
                # Validate form data
                if not name or not description:
                    flash('Please fill in all required fields.', 'danger')
                    return redirect(url_for('edit_project', project_id=project_id))
                
                try:
                    # Update metadata with additional fields
                    metadata = project.get('metadata', {})
                    metadata.update({
                        'priority': priority,
                        'tags': tags.split(',') if tags else [],
                        'deadline': deadline,
                        'progress': progress
                    })
                    
                    # Update project via the API
                    project_client.update_project(
                        project_id=project_id,
                        name=name,
                        description=description,
                        status=status,
                        metadata=metadata
                    )
                    
                    # Get current agents assigned to the project
                    current_agents = project_client.get_project_agents(project_id)
                    current_agent_ids = [str(agent.get('id')) for agent in current_agents]
                    
                    # Determine agents to add and remove
                    agents_to_add = [agent_id for agent_id in agent_ids if agent_id not in current_agent_ids]
                    agents_to_remove = [agent_id for agent_id in current_agent_ids if agent_id not in agent_ids]
                    
                    # Assign new agents to the project
                    for agent_id in agents_to_add:
                        try:
                            project_client.assign_agent_to_project(project_id, agent_id)
                        except APIError as e:
                            current_app.logger.error(f'Error assigning agent {agent_id} to project {project_id}: {e.message}')
                    
                    # Remove agents from the project
                    for agent_id in agents_to_remove:
                        try:
                            project_client.remove_agent_from_project(project_id, agent_id)
                        except APIError as e:
                            current_app.logger.error(f'Error removing agent {agent_id} from project {project_id}: {e.message}')
                    
                    flash('Project updated successfully!', 'success')
                    return redirect(url_for('project_detail', project_id=project_id))
                
                except APIError as e:
                    flash(f'Error updating project: {e.message}', 'danger')
                    return redirect(url_for('edit_project', project_id=project_id))
            
            # GET request - render the form
            try:
                # Get available agents from the API
                agent_client = get_agent_orchestrator_client()
                all_agents = agent_client.get_available_agents()
                
                # Get agents assigned to the project
                project_agents = project_client.get_project_agents(project_id)
                project_agent_ids = [str(agent.get('id')) for agent in project_agents]
                
                # Extract metadata fields
                metadata = project.get('metadata', {})
                project['priority'] = metadata.get('priority', 'Medium')
                project['tags'] = ','.join(metadata.get('tags', []))
                project['deadline'] = metadata.get('deadline', '')
                project['progress'] = metadata.get('progress', 0)
                project['agent_ids'] = project_agent_ids
                
                return render_template('projects/edit.html', project=project, agents=all_agents)
            
            except APIError as e:
                flash(f'Error loading agents: {e.message}', 'warning')
                return render_template('projects/edit.html', project=project, agents=[])
        
        except APIError as e:
            flash(f'Error loading project: {e.message}', 'danger')
            return redirect(url_for('projects_list'))

    @app.route('/projects/<uuid:project_id>/initiate', methods=['POST'])
    @login_required
    def initiate_project(project_id):
        """Initiate a project."""
        try:
            # Get project details from the API
            project_client = get_project_coordinator_client()
            project = project_client.get_project(project_id)
            
            # Check if the project is already initiated
            if project.get('status') == 'In Progress':
                flash('Project is already initiated.', 'warning')
                return redirect(url_for('project_detail', project_id=project_id))
            
            # Update project status to "In Progress"
            metadata = project.get('metadata', {})
            project_client.update_project(
                project_id=project_id,
                name=project.get('name'),
                description=project.get('description'),
                status='In Progress',
                metadata=metadata
            )
            
            # Create a strategic plan for the project
            planning_client = get_planning_system_client()
            plan_data = {
                'name': f"Strategic Plan for {project.get('name')}",
                'description': f"Auto-generated strategic plan for {project.get('name')}",
                'project_id': str(project_id),
                'status': 'ACTIVE',
                'metadata': {
                    'project_type': metadata.get('project_type', 'Software Development'),
                    'goals': metadata.get('goals', ''),
                    'constraints': metadata.get('constraints', '')
                }
            }
            plan = planning_client.create_plan(plan_data)
            
            # Generate specialized agents for the project
            agent_client = get_agent_orchestrator_client()
            agent_generation_data = {
                'project_id': str(project_id),
                'project_type': metadata.get('project_type', 'Software Development'),
                'requirements': metadata.get('requirements', ''),
                'plan_id': plan.get('id')
            }
            agents = agent_client.generate_agents(agent_generation_data)
            
            flash('Project initiated successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
        
        except APIError as e:
            flash(f'Error initiating project: {e.message}', 'danger')
            return redirect(url_for('project_detail', project_id=project_id))

    @app.route('/projects/<uuid:project_id>/deploy', methods=['POST'])
    @login_required
    def deploy_project(project_id):
        """Deploy a project."""
        try:
            # Get project details from the API
            project_client = get_project_coordinator_client()
            project = project_client.get_project(project_id)
            
            # Check if the project is already deployed
            if project.get('status') == 'Deployed':
                flash('Project is already deployed.', 'warning')
                return redirect(url_for('project_detail', project_id=project_id))
            
            # Check if the project is initiated
            if project.get('status') != 'In Progress':
                flash('Project must be initiated before it can be deployed.', 'warning')
                return redirect(url_for('project_detail', project_id=project_id))
            
            # Update project status to "Deployed"
            metadata = project.get('metadata', {})
            project_client.update_project(
                project_id=project_id,
                name=project.get('name'),
                description=project.get('description'),
                status='Deployed',
                metadata=metadata
            )
            
            flash('Project deployed successfully!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
        
        except APIError as e:
            flash(f'Error deploying project: {e.message}', 'danger')
            return redirect(url_for('project_detail', project_id=project_id))

    @app.route('/projects/<uuid:project_id>/delete', methods=['POST'])
    @login_required
    def delete_project(project_id):
        """Delete a project."""
        try:
            # Delete project via the API
            client = get_project_coordinator_client()
            client.delete_project(project_id)
            
            flash('Project deleted successfully!', 'success')
        except APIError as e:
            flash(f'Error deleting project: {e.message}', 'danger')
        
        return redirect(url_for('projects_list'))

    @app.route('/api/projects')
    @login_required
    def api_projects():
        """API endpoint to get projects for AJAX requests."""
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort = request.args.get('sort', 'updated_desc')
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
        
        try:
            # Get projects from the API
            client = get_project_coordinator_client()
            result = client.get_projects(search=search, status=status, sort=sort, page=page, per_page=per_page)
            
            return jsonify(result)
        except APIError as e:
            return jsonify({'error': e.message}), e.status_code or 500

    @app.route('/api/projects/<uuid:project_id>')
    @login_required
    def api_project_detail(project_id):
        """API endpoint to get project details for AJAX requests."""
        try:
            # Get project details from the API
            client = get_project_coordinator_client()
            project = client.get_project(project_id)
            
            return jsonify(project)
        except APIError as e:
            return jsonify({'error': e.message}), e.status_code or 500
