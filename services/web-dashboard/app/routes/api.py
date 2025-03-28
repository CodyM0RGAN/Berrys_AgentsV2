"""
API routes for the web dashboard, exempt from CSRF.
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app

# Removed flask_login imports as auth is bypassed for now
# Removed DB imports as these routes use the API client

from app.api.clients import get_project_coordinator_client
from app.api.base import APIError

# Create Blueprint
# Use url_prefix='/api' to automatically prefix all routes in this blueprint
api_blueprint = Blueprint('api', __name__, url_prefix='/api')

@api_blueprint.route('/chat/message', methods=['POST'])
# Removed @login_required
def send_message():
    """API endpoint to send a message to the chatbot via Project Coordinator."""
    current_app.logger.info(f"Received request for /api/chat/message")
    data = request.json
    if not data:
         current_app.logger.error("Request received without JSON data.")
         return jsonify({'error': 'Request must be JSON'}), 400
         
    message_content = data.get('message')
    session_id = data.get('session_id')
    current_app.logger.info(f"Processing message for session_id: {session_id}")
    # user_id = str(current_user.id) if hasattr(current_user, 'id') else None # Removed current_user reference
    user_id = None # Bypass user ID for now

    if not message_content or not session_id:
        current_app.logger.error("Missing message or session_id in request.")
        return jsonify({'error': 'Missing message or session ID'}), 400

    try:
        current_app.logger.debug("Attempting to get project_coordinator_client.")
        project_client = get_project_coordinator_client()
        current_app.logger.debug(f"Project Coordinator client obtained. Base URL: {project_client.base_url}")
        
        # Fetch history via API before sending the new message
        current_app.logger.debug(f"Attempting to fetch history for session {session_id}.")
        try:
            # Use the correct endpoint path: /chat/sessions/{session_id}
            # The base_url is now http://project-coordinator:8000 (no /api suffix)
            history_data = project_client.get(f'/chat/sessions/{session_id}')
            formatted_history = history_data if isinstance(history_data, list) else []
            current_app.logger.debug(f"Fetched history for session {session_id}. Length: {len(formatted_history)}")
        except APIError as e:
             current_app.logger.error(f"API Error fetching history for session {session_id}: {e.message} (Status: {e.status_code})", exc_info=True)
             formatted_history = []
        except Exception as e:
             current_app.logger.error(f"Unexpected error fetching chat history for session {session_id}: {e}", exc_info=True)
             formatted_history = []

        # Send the message and history to the Project Coordinator's chat endpoint
        current_app.logger.debug(f"Attempting to send message to Project Coordinator for session {session_id}.")
        # The base_url is now http://project-coordinator:8000 (no /api suffix)
        response_data = project_client.send_chat_message(
            message=message_content,
            session_id=session_id,
            user_id=user_id, # Will be None
            history=formatted_history
        )
        current_app.logger.debug(f"Received response from Project Coordinator for session {session_id}.")

        # Extract the response content and actions
        bot_response_content = response_data.get('response', "I'm sorry, I couldn't process your request at this time. Please try again.")
        bot_actions = response_data.get('actions', [])
        current_app.logger.debug(f"Bot response content: {bot_response_content[:100]}...")
        current_app.logger.debug(f"Bot actions received: {bot_actions}")

        # Process actions returned by the Project Coordinator
        if bot_actions:
            current_app.logger.info(f"Processing {len(bot_actions)} actions for session {session_id}.")
            updated_content = bot_response_content # Start with original content
            for action in bot_actions:
                action_type = action.get('type')
                action_data = action.get('data', {})
                current_app.logger.debug(f"Processing action type: {action_type}")

                if action_type == 'create_project':
                    try:
                        current_app.logger.info(f"Executing create_project action: {action_data.get('name')}")
                        project = project_client.create_project(
                            name=action_data.get('name'),
                            description=action_data.get('description'),
                            status=action_data.get('status'),
                            metadata=action_data.get('metadata')
                        )
                        project_id = project.get('id')
                        if project_id:
                            current_app.logger.info(f"Project created successfully: {project_id}")
                            additional_info = f"\n\n🎉 Great news! I've created a new project called **{action_data.get('name')}** for you! You can view it [here](/projects/{project_id})."
                            updated_content += additional_info
                        else:
                             current_app.logger.warning("Create project action executed but no project ID returned.")
                    except APIError as e:
                        current_app.logger.error(f"API Error executing create_project action: {e.message} (Status: {e.status_code})", exc_info=True)
                        updated_content += f"\n\n⚠️ Error creating project: {e.message}"
                    except Exception as e:
                         current_app.logger.error(f"Unexpected error executing create_project action: {e}", exc_info=True)
                         updated_content += f"\n\n⚠️ Unexpected error creating project."

                elif action_type == 'assign_agents':
                    project_id = action_data.get('project_id')
                    agent_ids = action_data.get('agent_ids', [])
                    if project_id and agent_ids:
                        try:
                            current_app.logger.info(f"Executing assign_agents action for project {project_id}: {agent_ids}")
                            for agent_id in agent_ids:
                                project_client.assign_agent_to_project(project_id, agent_id)
                            current_app.logger.info(f"Agents assigned successfully for project {project_id}.")
                            additional_info = f"\n\n🤖 I've assigned {len(agent_ids)} agent(s) to your project!"
                            updated_content += additional_info
                        except APIError as e:
                            current_app.logger.error(f"API Error executing assign_agents action: {e.message} (Status: {e.status_code})", exc_info=True)
                            updated_content += f"\n\n⚠️ Error assigning agents: {e.message}"
                        except Exception as e:
                             current_app.logger.error(f"Unexpected error executing assign_agents action: {e}", exc_info=True)
                             updated_content += f"\n\n⚠️ Unexpected error assigning agents."
                    else:
                         current_app.logger.warning(f"Assign agents action missing project_id or agent_ids: {action_data}")

            bot_response_content = updated_content
        else:
             current_app.logger.debug("No actions to process.")

        current_app.logger.info(f"Successfully processed message for session {session_id}. Sending response.")
        return jsonify({'response': bot_response_content})

    except APIError as e:
        current_app.logger.error(f'API Error calling Project Coordinator for session {session_id}: {e.message} (Status: {e.status_code})', exc_info=True)
        fallback_response = "I'm sorry, I'm having trouble connecting to the chat service. Please try again later."
        return jsonify({'response': fallback_response}), e.status_code or 500
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.error(f'Unexpected {error_type} processing chat message for session {session_id}: {e}', exc_info=True)
        fallback_response = "Oh dear! Something unexpected happened. Please try again shortly."
        return jsonify({'response': fallback_response}), 500


@api_blueprint.route('/chat/history/<session_id>')
# Removed @login_required
def get_chat_history(session_id):
    """API endpoint to get chat history for a session via Project Coordinator."""
    current_app.logger.info(f"Received request for /api/chat/history/{session_id}")
    try:
        current_app.logger.debug(f"Attempting to get project_coordinator_client for history.")
        project_client = get_project_coordinator_client()
        current_app.logger.debug(f"Calling project_client.get for history of session {session_id}.")
        # The base_url is now http://project-coordinator:8000 (no /api suffix)
        history_data = project_client.get(f'/chat/sessions/{session_id}')
        
        history_list = history_data if isinstance(history_data, list) else []
        current_app.logger.debug(f"Fetched history list length: {len(history_list)}")

        return jsonify({'history': history_list})

    except APIError as e:
         current_app.logger.error(f'API Error fetching history for session {session_id}: {e.message} (Status: {e.status_code})', exc_info=True)
         return jsonify({'history': [], 'error': f'API error fetching history: {e.message}'})
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.error(f'Unexpected {error_type} fetching chat history for session {session_id}: {e}', exc_info=True)
        return jsonify({'history': [], 'error': 'Unexpected error fetching history'})


@api_blueprint.route('/chat/clear/<session_id>', methods=['POST'])
# Removed @login_required
def clear_chat_history(session_id):
    """API endpoint to clear chat history for a session."""
    current_app.logger.info(f"Received request to clear chat history for session {session_id}")
    try:
        project_client = get_project_coordinator_client()
        # The base_url is now http://project-coordinator:8000 (no /api suffix)
        project_client.delete(f'/chat/sessions/{session_id}')
        current_app.logger.info(f"Successfully cleared chat history for session {session_id}")
        return jsonify({'status': 'success'}), 200
    except APIError as e:
        current_app.logger.error(f'API Error clearing history for session {session_id}: {e.message} (Status: {e.status_code})', exc_info=True)
        return jsonify({'status': 'error', 'error': f'API error clearing history: {e.message}'}), e.status_code or 500
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.error(f'Unexpected {error_type} clearing chat history for session {session_id}: {e}', exc_info=True)
        return jsonify({'status': 'error', 'error': 'Unexpected error clearing history'}), 500
