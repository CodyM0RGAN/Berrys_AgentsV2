"""
Routes for the metrics dashboard and alerts.
"""
from flask import render_template, current_app, jsonify, request
from flask_login import login_required

from app.api.clients import get_agent_orchestrator_client
from app.api.base import APIError

def register_routes(app):
    """Register metrics routes with the Flask app."""
    
    @app.route('/metrics')
    @login_required
    def metrics_dashboard():
        """Render the metrics dashboard page."""
        return render_template('metrics/dashboard.html')
    
    @app.route('/metrics/alerts')
    @login_required
    def alerts_dashboard():
        """Render the alerts dashboard page."""
        return render_template('metrics/alerts.html')

    @app.route('/api/metrics/messages')
    @login_required
    def get_message_metrics():
        """API endpoint to get message metrics."""
        try:
            # Get query parameters
            message_id = request.args.get('message_id')
            source_agent_id = request.args.get('source_agent_id')
            destination_agent_id = request.args.get('destination_agent_id')
            topic = request.args.get('topic')
            status = request.args.get('status')
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if message_id:
                params['message_id'] = message_id
            if source_agent_id:
                params['source_agent_id'] = source_agent_id
            if destination_agent_id:
                params['destination_agent_id'] = destination_agent_id
            if topic:
                params['topic'] = topic
            if status:
                params['status'] = status
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            params['limit'] = limit
            params['offset'] = offset
            
            # Get message metrics
            metrics = agent_client.get('/metrics/messages', params=params)
            
            return jsonify(metrics)
        except APIError as e:
            current_app.logger.error(f'Error getting message metrics: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting message metrics: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500

    @app.route('/api/metrics/agents')
    @login_required
    def get_agent_metrics():
        """API endpoint to get agent metrics."""
        try:
            # Get query parameters
            agent_id = request.args.get('agent_id')
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if agent_id:
                params['agent_id'] = agent_id
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            params['limit'] = limit
            params['offset'] = offset
            
            # Get agent metrics
            metrics = agent_client.get('/metrics/agents', params=params)
            
            return jsonify(metrics)
        except APIError as e:
            current_app.logger.error(f'Error getting agent metrics: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting agent metrics: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500

    @app.route('/api/metrics/topics')
    @login_required
    def get_topic_metrics():
        """API endpoint to get topic metrics."""
        try:
            # Get query parameters
            topic = request.args.get('topic')
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if topic:
                params['topic'] = topic
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            params['limit'] = limit
            params['offset'] = offset
            
            # Get topic metrics
            metrics = agent_client.get('/metrics/topics', params=params)
            
            return jsonify(metrics)
        except APIError as e:
            current_app.logger.error(f'Error getting topic metrics: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting topic metrics: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500

    @app.route('/api/metrics/performance')
    @login_required
    def get_performance_metrics():
        """API endpoint to get performance metrics."""
        try:
            # Get query parameters
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            
            # Get performance metrics
            metrics = agent_client.get('/metrics/performance', params=params)
            
            return jsonify(metrics)
        except APIError as e:
            current_app.logger.error(f'Error getting performance metrics: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting performance metrics: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    # Alert API endpoints
    
    @app.route('/api/alerts/configurations')
    @login_required
    def get_alert_configurations():
        """API endpoint to get alert configurations."""
        try:
            # Get query parameters
            metric_type = request.args.get('metric_type')
            severity = request.args.get('severity')
            enabled = request.args.get('enabled')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if metric_type:
                params['metric_type'] = metric_type
            if severity:
                params['severity'] = severity
            if enabled is not None:
                params['enabled'] = enabled
            params['limit'] = limit
            params['offset'] = offset
            
            # Get alert configurations
            configs = agent_client.get('/alerts/configurations', params=params)
            
            return jsonify(configs)
        except APIError as e:
            current_app.logger.error(f'Error getting alert configurations: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting alert configurations: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/configurations/<uuid:alert_id>')
    @login_required
    def get_alert_configuration(alert_id):
        """API endpoint to get an alert configuration by ID."""
        try:
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Get alert configuration
            config = agent_client.get(f'/alerts/configurations/{alert_id}')
            
            return jsonify(config)
        except APIError as e:
            current_app.logger.error(f'Error getting alert configuration {alert_id}: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting alert configuration {alert_id}: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/configurations', methods=['POST'])
    @login_required
    def create_alert_configuration():
        """API endpoint to create an alert configuration."""
        try:
            # Get request data
            data = request.json
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Create alert configuration
            config = agent_client.post('/alerts/configurations', json=data)
            
            return jsonify(config)
        except APIError as e:
            current_app.logger.error(f'Error creating alert configuration: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error creating alert configuration: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/configurations/<uuid:alert_id>', methods=['PUT'])
    @login_required
    def update_alert_configuration(alert_id):
        """API endpoint to update an alert configuration."""
        try:
            # Get request data
            data = request.json
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Update alert configuration
            config = agent_client.put(f'/alerts/configurations/{alert_id}', json=data)
            
            return jsonify(config)
        except APIError as e:
            current_app.logger.error(f'Error updating alert configuration {alert_id}: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error updating alert configuration {alert_id}: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/configurations/<uuid:alert_id>', methods=['DELETE'])
    @login_required
    def delete_alert_configuration(alert_id):
        """API endpoint to delete an alert configuration."""
        try:
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Delete alert configuration
            result = agent_client.delete(f'/alerts/configurations/{alert_id}')
            
            return jsonify(result)
        except APIError as e:
            current_app.logger.error(f'Error deleting alert configuration {alert_id}: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error deleting alert configuration {alert_id}: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/history')
    @login_required
    def get_alert_history():
        """API endpoint to get alert history."""
        try:
            # Get query parameters
            alert_configuration_id = request.args.get('alert_configuration_id')
            alert_id = request.args.get('alert_id')
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            acknowledged = request.args.get('acknowledged')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Build query parameters
            params = {}
            if alert_configuration_id:
                params['alert_configuration_id'] = alert_configuration_id
            if alert_id:
                params['alert_id'] = alert_id
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
            if acknowledged is not None:
                params['acknowledged'] = acknowledged
            params['limit'] = limit
            params['offset'] = offset
            
            # Get alert history
            history = agent_client.get('/alerts/history', params=params)
            
            return jsonify(history)
        except APIError as e:
            current_app.logger.error(f'Error getting alert history: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting alert history: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/active')
    @login_required
    def get_active_alerts():
        """API endpoint to get active alerts."""
        try:
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Get active alerts
            alerts = agent_client.get('/alerts/active')
            
            return jsonify(alerts)
        except APIError as e:
            current_app.logger.error(f'Error getting active alerts: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error getting active alerts: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
    
    @app.route('/api/alerts/acknowledge/<uuid:alert_id>', methods=['POST'])
    @login_required
    def acknowledge_alert(alert_id):
        """API endpoint to acknowledge an alert."""
        try:
            # Get request data
            data = request.json or {}
            
            # Get agent orchestrator client
            agent_client = get_agent_orchestrator_client()
            
            # Acknowledge alert
            result = agent_client.post(f'/alerts/acknowledge/{alert_id}', json=data)
            
            return jsonify(result)
        except APIError as e:
            current_app.logger.error(f'Error acknowledging alert {alert_id}: {e.message}')
            return jsonify({'error': e.message}), e.status_code or 500
        except Exception as e:
            current_app.logger.error(f'Unexpected error acknowledging alert {alert_id}: {str(e)}')
            return jsonify({'error': 'Unexpected error'}), 500
