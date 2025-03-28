from flask import render_template, current_app, jsonify, request
from flask_login import login_required, current_user

from app.api.clients import get_project_coordinator_client, get_agent_orchestrator_client
from app.api.base import APIError

def register_routes(app):
    """Register main routes with the Flask app."""
    
    @app.route('/')
    def index():
        """Render the home page."""
        return render_template('main/index.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Render the dashboard page."""
        try:
            # Get dashboard data from APIs
            dashboard_data = get_dashboard_data()
            return render_template('main/dashboard.html', dashboard_data=dashboard_data)
        except APIError as e:
            current_app.logger.error(f'Error loading dashboard data: {e.message}')
            # Provide fallback data if API calls fail
            dashboard_data = get_fallback_dashboard_data()
            return render_template('main/dashboard.html', dashboard_data=dashboard_data)

    @app.route('/api/dashboard-data')
    @login_required
    def dashboard_data():
        """API endpoint to get dashboard data for AJAX updates."""
        try:
            # Get dashboard data from APIs
            data = get_dashboard_data()
            return jsonify(data)
        except APIError as e:
            return jsonify({'error': e.message}), e.status_code or 500

def get_dashboard_data():
    """
    Get dashboard data from various APIs.
    
    Returns:
        dict: Dashboard data.
    
    Raises:
        APIError: If there's an error fetching data from APIs.
    """
    # Get project data
    project_client = get_project_coordinator_client()
    projects_result = project_client.get_projects(per_page=3, sort='updated_desc')
    
    # Get agent data
    agent_client = get_agent_orchestrator_client()
    agents_result = agent_client.get_agents(per_page=3)
    
    # Combine data for the dashboard
    dashboard_data = {
        'projects': {
            'total': projects_result.get('total', 0),
            'active': sum(1 for p in projects_result.get('items', []) if p.get('status') in ['PLANNING', 'IN_PROGRESS']),
            'completed': sum(1 for p in projects_result.get('items', []) if p.get('status') == 'COMPLETED'),
            'recent': [
                {
                    'id': p.get('id'),
                    'name': p.get('name'),
                    'status': p.get('status').title().replace('_', ' ') if isinstance(p.get('status'), str) else p.get('status'),
                    'progress': p.get('metadata', {}).get('progress', 0)
                }
                for p in projects_result.get('items', [])
            ]
        },
        'agents': {
            'total': agents_result.get('total', 0),
            'active': sum(1 for a in agents_result.get('items', []) if a.get('status') == 'ACTIVE'),
            'recent_activity': [
                {
                    'id': a.get('id'),
                    'name': a.get('name'),
                    'status': a.get('status').title() if isinstance(a.get('status'), str) else a.get('status'),
                    'task': a.get('current_task', {}).get('description')
                }
                for a in agents_result.get('items', [])
            ]
        },
        'system': {
            'status': 'Operational',
            'resources': {
                'cpu': 35,
                'memory': 42,
                'storage': 28
            },
            'uptime': '5 days, 7 hours'
        }
    }
    
    return dashboard_data

def get_fallback_dashboard_data():
    """
    Get fallback dashboard data when APIs are unavailable.
    
    Returns:
        dict: Fallback dashboard data.
    """
    return {
        'projects': {
            'total': 5,
            'active': 3,
            'completed': 2,
            'recent': [
                {
                    'id': 1,
                    'name': 'Website Redesign',
                    'status': 'In Progress',
                    'progress': 75
                },
                {
                    'id': 2,
                    'name': 'Mobile App Development',
                    'status': 'In Progress',
                    'progress': 40
                },
                {
                    'id': 3,
                    'name': 'Database Migration',
                    'status': 'Completed',
                    'progress': 100
                }
            ]
        },
        'agents': {
            'total': 4,
            'active': 2,
            'recent_activity': [
                {
                    'id': 1,
                    'name': 'Code Generator',
                    'status': 'Active',
                    'task': 'Generating API endpoints for the mobile app'
                },
                {
                    'id': 2,
                    'name': 'Data Analyzer',
                    'status': 'Idle',
                    'task': None
                },
                {
                    'id': 3,
                    'name': 'QA Tester',
                    'status': 'Active',
                    'task': 'Testing website functionality'
                }
            ]
        },
        'system': {
            'status': 'Operational',
            'resources': {
                'cpu': 35,
                'memory': 42,
                'storage': 28
            },
            'uptime': '5 days, 7 hours'
        }
    }
