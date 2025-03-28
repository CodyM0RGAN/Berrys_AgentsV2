import uuid
from datetime import datetime
from flask import render_template, request, jsonify, session, current_app, flash
# Removed flask_login imports

from app.api.clients import get_project_coordinator_client
from app.api.base import APIError

# Removed DB imports and in-memory storage

def register_routes(app):
    """Register chat routes with the Flask app."""

    @app.route('/chat')
    # Removed @login_required
    def chat():
        """Render the chat interface."""
        # Generate a unique session ID if one doesn't exist in the Flask session
        if 'chat_session_id' not in session:
            session['chat_session_id'] = str(uuid.uuid4())
            current_app.logger.info(f"Generated new Flask session chat_session_id: {session['chat_session_id']}")

        session_id = session['chat_session_id']
        
        # Just render the template. The JS will fetch history via the API.
        # No need to interact with DB or Project Coordinator here just to load the page.
        return render_template('chat/index.html', session_id=session_id)

    # Removed the /api/chat/message route as it's now in api.py
