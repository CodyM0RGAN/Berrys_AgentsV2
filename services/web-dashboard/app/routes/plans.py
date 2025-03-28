from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from uuid import UUID
from datetime import datetime, timedelta

from app.api.clients import get_planning_system_client, get_project_coordinator_client, get_agent_orchestrator_client
from app.api.base import APIError

def register_routes(app):
    """Register planning routes with the Flask app."""
    
    @app.route('/plans')
    @login_required
    def plans_list():
        """Render the plans list page."""
        # Get query parameters for filtering and sorting
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        sort = request.args.get('sort', 'updated_desc')
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('ITEMS_PER_PAGE', 10)
        
        try:
            # Get plans from the API
            client = get_planning_system_client()
            result = client.get_plans(search=search, status=status, sort=sort, page=page, per_page=per_page)
            
            # Extract plans and pagination data
            plans = result.get('items', [])
            pagination = {
                'page': result.get('page', 1),
                'per_page': result.get('per_page', per_page),
                'total': result.get('total', 0),
                'pages': result.get('pages', 1)
            }
            
            return render_template('projects/plans_list.html', plans=plans, pagination=pagination, 
                                search=search, status=status, sort=sort)
        
        except APIError as e:
            flash(f'Error loading plans: {e.message}', 'danger')
            return render_template('projects/plans_list.html', plans=[], pagination={
                'page': 1, 'per_page': per_page, 'total': 0, 'pages': 1
            })

    @app.route('/plans/<uuid:plan_id>')
    @login_required
    def plan_detail(plan_id):
        """Render the plan detail page."""
        try:
            # Get plan details from the API
            planning_client = get_planning_system_client()
            plan = planning_client.get_plan(plan_id)
            
            # Get plan tasks
            tasks = planning_client.get_plan_tasks(plan_id)
            
            # Get critical path
            try:
                critical_path = planning_client.get_critical_path(plan_id)
                plan['critical_path'] = critical_path
            except APIError:
                plan['critical_path'] = None
            
            # Get timeline forecast
            try:
                forecast = planning_client.get_timeline_forecast(plan_id)
                plan['forecast'] = forecast
            except APIError:
                plan['forecast'] = None
            
            # Get bottlenecks
            try:
                bottlenecks = planning_client.get_bottlenecks(plan_id)
                plan['bottlenecks'] = bottlenecks
            except APIError:
                plan['bottlenecks'] = None
            
            # Add tasks to the plan data
            plan['tasks'] = tasks
            
            return render_template('projects/plan.html', plan=plan)
        
        except APIError as e:
            flash(f'Error loading plan: {e.message}', 'danger')
            return redirect(url_for('plans_list'))

    @app.route('/plans/new', methods=['GET', 'POST'])
    @login_required
    def new_plan():
        """Render the new plan form and handle form submission."""
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            project_id = request.form.get('project_id')
            status = request.form.get('status')
            project_type = request.form.get('project_type')
            goals = request.form.get('goals')
            constraints = request.form.get('constraints')
            
            # Validate form data
            if not name or not description or not project_id:
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('new_plan'))
            
            try:
                # Create metadata with additional fields
                metadata = {
                    'project_type': project_type,
                    'goals': goals,
                    'constraints': constraints
                }
                
                # Create plan via the API
                client = get_planning_system_client()
                plan = client.create_plan(
                    name=name,
                    description=description,
                    project_id=project_id,
                    status=status,
                    metadata=metadata
                )
                
                flash('Plan created successfully!', 'success')
                return redirect(url_for('plan_detail', plan_id=plan.get('id')))
            
            except APIError as e:
                flash(f'Error creating plan: {e.message}', 'danger')
                return redirect(url_for('new_plan'))
        
        # GET request - render the form
        try:
            # Get projects from the API
            project_client = get_project_coordinator_client()
            projects = project_client.get_projects().get('items', [])
            
            # Get project_id from query parameter if provided
            project_id = request.args.get('project_id')
            
            return render_template('projects/new_plan.html', projects=projects, project_id=project_id)
        
        except APIError as e:
            flash(f'Error loading projects: {e.message}', 'warning')
            return render_template('projects/new_plan.html', projects=[])

    @app.route('/plans/<uuid:plan_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_plan(plan_id):
        """Render the edit plan form and handle form submission."""
        try:
            # Get plan details from the API
            planning_client = get_planning_system_client()
            plan = planning_client.get_plan(plan_id)
            
            if request.method == 'POST':
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                status = request.form.get('status')
                project_type = request.form.get('project_type')
                goals = request.form.get('goals')
                constraints = request.form.get('constraints')
                
                # Validate form data
                if not name or not description:
                    flash('Please fill in all required fields.', 'danger')
                    return redirect(url_for('edit_plan', plan_id=plan_id))
                
                try:
                    # Update metadata with additional fields
                    metadata = plan.get('metadata', {})
                    metadata.update({
                        'project_type': project_type,
                        'goals': goals,
                        'constraints': constraints
                    })
                    
                    # Update plan via the API
                    planning_client.update_plan(
                        plan_id=plan_id,
                        name=name,
                        description=description,
                        status=status,
                        metadata=metadata
                    )
                    
                    flash('Plan updated successfully!', 'success')
                    return redirect(url_for('plan_detail', plan_id=plan_id))
                
                except APIError as e:
                    flash(f'Error updating plan: {e.message}', 'danger')
                    return redirect(url_for('edit_plan', plan_id=plan_id))
            
            # GET request - render the form
            return render_template('projects/edit_plan.html', plan=plan)
        
        except APIError as e:
            flash(f'Error loading plan: {e.message}', 'danger')
            return redirect(url_for('plans_list'))

    @app.route('/plans/<uuid:plan_id>/delete', methods=['POST'])
    @login_required
    def delete_plan(plan_id):
        """Delete a plan."""
        try:
            # Delete plan via the API
            client = get_planning_system_client()
            client.delete_plan(plan_id)
            
            flash('Plan deleted successfully!', 'success')
        except APIError as e:
            flash(f'Error deleting plan: {e.message}', 'danger')
        
        return redirect(url_for('plans_list'))

    @app.route('/plans/<uuid:plan_id>/generate-forecast', methods=['GET', 'POST'])
    @login_required
    def generate_forecast(plan_id):
        """Generate a timeline forecast for a plan."""
        try:
            # Generate forecast via the API
            client = get_planning_system_client()
            forecast = client.generate_timeline_forecast(plan_id)
            
            flash('Timeline forecast generated successfully!', 'success')
        except APIError as e:
            flash(f'Error generating forecast: {e.message}', 'danger')
        
        return redirect(url_for('plan_detail', plan_id=plan_id))

    @app.route('/plans/<uuid:plan_id>/analyze-bottlenecks', methods=['GET', 'POST'])
    @login_required
    def analyze_bottlenecks(plan_id):
        """Analyze bottlenecks in a plan."""
        try:
            # Analyze bottlenecks via the API
            client = get_planning_system_client()
            bottlenecks = client.analyze_bottlenecks(plan_id)
            
            flash('Bottleneck analysis completed successfully!', 'success')
        except APIError as e:
            flash(f'Error analyzing bottlenecks: {e.message}', 'danger')
        
        return redirect(url_for('plan_detail', plan_id=plan_id))

    @app.route('/tasks/new', methods=['GET', 'POST'])
    @login_required
    def new_task():
        """Render the new task form and handle form submission."""
        plan_id = request.args.get('plan_id') or request.form.get('plan_id')
        if not plan_id:
            flash('Plan ID is required.', 'danger')
            return redirect(url_for('plans_list'))
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            status = request.form.get('status')
            priority = request.form.get('priority')
            estimated_duration = request.form.get('estimated_duration')
            due_date = request.form.get('due_date')
            assigned_to = request.form.get('assigned_to')
            dependencies = request.form.getlist('dependencies')
            acceptance_criteria = request.form.get('acceptance_criteria')
            tags = request.form.get('tags')
            
            # Validate form data
            if not name or not description:
                flash('Please fill in all required fields.', 'danger')
                return redirect(url_for('new_task', plan_id=plan_id))
            
            try:
                # Create metadata with additional fields
                metadata = {
                    'priority': priority,
                    'tags': tags.split(',') if tags else [],
                    'acceptance_criteria': acceptance_criteria,
                    'due_date': due_date
                }
                
                # Create task via the API
                client = get_planning_system_client()
                task = client.create_task(
                    name=name,
                    description=description,
                    plan_id=plan_id,
                    status=status,
                    estimated_duration=float(estimated_duration),
                    assigned_agent_id=assigned_to if assigned_to else None,
                    metadata=metadata
                )
                
                # Add dependencies if any were selected
                task_id = task.get('id')
                if task_id and dependencies:
                    for dependency_id in dependencies:
                        try:
                            client.create_dependency(task_id, dependency_id)
                        except APIError as e:
                            current_app.logger.error(f'Error creating dependency between {task_id} and {dependency_id}: {e.message}')
                
                flash('Task created successfully!', 'success')
                return redirect(url_for('plan_detail', plan_id=plan_id))
            
            except APIError as e:
                flash(f'Error creating task: {e.message}', 'danger')
                return redirect(url_for('new_task', plan_id=plan_id))
        
        # GET request - render the form
        try:
            # Get plan details from the API
            planning_client = get_planning_system_client()
            plan = planning_client.get_plan(plan_id)
            
            # Get plan tasks
            tasks = planning_client.get_plan_tasks(plan_id)
            
            # Get available agents
            agent_client = get_agent_orchestrator_client()
            agents = agent_client.get_available_agents()
            
            return render_template('projects/task_form.html', plan_id=plan_id, tasks=tasks, agents=agents)
        
        except APIError as e:
            flash(f'Error loading plan data: {e.message}', 'warning')
            return redirect(url_for('plan_detail', plan_id=plan_id))

    @app.route('/tasks/<uuid:task_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_task(task_id):
        """Render the edit task form and handle form submission."""
        try:
            # Get task details from the API
            planning_client = get_planning_system_client()
            task = planning_client.get_task(task_id)
            plan_id = task.get('plan_id')
            
            if request.method == 'POST':
                # Get form data
                name = request.form.get('name')
                description = request.form.get('description')
                status = request.form.get('status')
                priority = request.form.get('priority')
                estimated_duration = request.form.get('estimated_duration')
                due_date = request.form.get('due_date')
                assigned_to = request.form.get('assigned_to')
                dependencies = request.form.getlist('dependencies')
                acceptance_criteria = request.form.get('acceptance_criteria')
                tags = request.form.get('tags')
                
                # Validate form data
                if not name or not description:
                    flash('Please fill in all required fields.', 'danger')
                    return redirect(url_for('edit_task', task_id=task_id))
                
                try:
                    # Update metadata with additional fields
                    metadata = task.get('metadata', {})
                    metadata.update({
                        'priority': priority,
                        'tags': tags.split(',') if tags else [],
                        'acceptance_criteria': acceptance_criteria,
                        'due_date': due_date
                    })
                    
                    # Update task via the API
                    planning_client.update_task(
                        task_id=task_id,
                        name=name,
                        description=description,
                        status=status,
                        estimated_duration=float(estimated_duration),
                        assigned_agent_id=assigned_to if assigned_to else None,
                        metadata=metadata
                    )
                    
                    # Get current dependencies
                    current_dependencies = planning_client.get_task_dependencies(task_id)
                    current_dependency_ids = [str(dep.get('dependency_id')) for dep in current_dependencies]
                    
                    # Determine dependencies to add and remove
                    deps_to_add = [dep_id for dep_id in dependencies if dep_id not in current_dependency_ids]
                    deps_to_remove = [dep_id for dep_id in current_dependency_ids if dep_id not in dependencies]
                    
                    # Add new dependencies
                    for dependency_id in deps_to_add:
                        try:
                            planning_client.create_dependency(task_id, dependency_id)
                        except APIError as e:
                            current_app.logger.error(f'Error creating dependency between {task_id} and {dependency_id}: {e.message}')
                    
                    # Remove dependencies
                    for dependency_id in deps_to_remove:
                        try:
                            # Find the dependency ID in the current dependencies
                            dep_obj = next((dep for dep in current_dependencies if str(dep.get('dependency_id')) == dependency_id), None)
                            if dep_obj:
                                planning_client.delete_dependency(dep_obj.get('id'))
                        except APIError as e:
                            current_app.logger.error(f'Error removing dependency between {task_id} and {dependency_id}: {e.message}')
                    
                    flash('Task updated successfully!', 'success')
                    return redirect(url_for('plan_detail', plan_id=plan_id))
                
                except APIError as e:
                    flash(f'Error updating task: {e.message}', 'danger')
                    return redirect(url_for('edit_task', task_id=task_id))
            
            # GET request - render the form
            try:
                # Get plan details from the API
                plan = planning_client.get_plan(plan_id)
                
                # Get plan tasks
                tasks = planning_client.get_plan_tasks(plan_id)
                
                # Get task dependencies
                dependencies = planning_client.get_task_dependencies(task_id)
                task['dependencies'] = [str(dep.get('dependency_id')) for dep in dependencies]
                
                # Get available agents
                agent_client = get_agent_orchestrator_client()
                agents = agent_client.get_available_agents()
                
                return render_template('projects/task_form.html', task=task, plan_id=plan_id, tasks=tasks, agents=agents)
            
            except APIError as e:
                flash(f'Error loading task data: {e.message}', 'warning')
                return redirect(url_for('plan_detail', plan_id=plan_id))
        
        except APIError as e:
            flash(f'Error loading task: {e.message}', 'danger')
            return redirect(url_for('plans_list'))

    @app.route('/tasks/<uuid:task_id>/delete', methods=['POST'])
    @login_required
    def delete_task(task_id):
        """Delete a task."""
        try:
            # Get task details from the API
            planning_client = get_planning_system_client()
            task = planning_client.get_task(task_id)
            plan_id = task.get('plan_id')
            
            # Delete task via the API
            planning_client.delete_task(task_id)
            
            flash('Task deleted successfully!', 'success')
            return redirect(url_for('plan_detail', plan_id=plan_id))
        except APIError as e:
            flash(f'Error deleting task: {e.message}', 'danger')
            return redirect(url_for('plans_list'))
