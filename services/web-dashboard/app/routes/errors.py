from flask import render_template, Blueprint, current_app, jsonify, request
from werkzeug.exceptions import HTTPException
from app.api.base import APIError

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found', 'message': str(error)}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        current_app.logger.error(f'Server Error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors."""
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(APIError)
    def api_error(error):
        """Handle API errors."""
        status_code = error.status_code or 500
        current_app.logger.error(f'API Error: {error.message}, Status: {status_code}')
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'API Error',
                'message': error.message,
                'details': error.response
            }), status_code
        
        # For non-API routes, render an appropriate error template
        if status_code == 404:
            return render_template('errors/404.html'), 404
        elif status_code == 403:
            return render_template('errors/403.html'), 403
        elif status_code == 400:
            return render_template('errors/400.html'), 400
        else:
            return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        """Handle unhandled exceptions."""
        current_app.logger.error(f'Unhandled Exception: {error}', exc_info=True)
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500
        
        return render_template('errors/500.html'), 500
