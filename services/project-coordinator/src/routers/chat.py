"""
Chat router for the Project Coordinator service.

This module provides API endpoints for chat interactions with Berry.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from ..dependencies import get_project_facade, get_model_orchestrator_client, get_db
from ..services.project_facade import ProjectFacade
from ..exceptions import ProjectCoordinatorError
from ..models.api import ChatRequest, ChatResponse, ChatActionData
from ..models.internal import ChatSession, ChatMessage, AgentInstructions
from ..repositories.agent_repository import AgentRepository


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="Send a message to Berry and get a response."
)
async def send_message(
    chat_request: ChatRequest,
    project_facade: ProjectFacade = Depends(get_project_facade),
    model_orchestrator_client = Depends(get_model_orchestrator_client),
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Process a chat message and generate a response using LLM.

    Args:
        chat_request: Chat message request
        project_facade: Project facade service
        model_orchestrator_client: Model orchestrator client
        db: Database session
        
    Returns:
        Chat response with Berry's message and any actions
    """
    logger.info(f"Processing chat message for session {chat_request.session_id}")
    try:
        # Log the incoming message
        logger.debug(f"Received chat message content: {chat_request.message}")

        # Store the user message in the database
        try:
            logger.debug(f"Attempting to get/create session {chat_request.session_id}")
            # Get or create chat session
            chat_session = db.query(ChatSession).filter(ChatSession.id == chat_request.session_id).first()
            if not chat_session:
                logger.info(f"Creating new chat session {chat_request.session_id}")
                chat_session = ChatSession(
                    id=chat_request.session_id,
                    user_id=chat_request.user_id,
                    session_metadata={"source": "web_dashboard"} # Corrected metadata field name
                )
                db.add(chat_session)
                db.flush() # Flush to get session ID if needed, though ID is provided
            else:
                 logger.debug(f"Found existing session {chat_request.session_id}")

            # Add user message
            logger.debug(f"Adding user message to session {chat_request.session_id}")
            user_message = ChatMessage(
                session_id=chat_request.session_id,
                role="user",
                content=chat_request.message,
                timestamp=datetime.utcnow(),
                message_metadata={} # Corrected metadata field name
            )
            db.add(user_message)
            db.commit()
            logger.info(f"User message stored for session {chat_request.session_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error storing user message for session {chat_request.session_id}: {e}", exc_info=True)
            # Decide if we should raise an error or continue with potentially incomplete history
            # For now, let's raise to make the failure clear
            raise HTTPException(status_code=500, detail=f"Database error storing user message: {e}")
        except Exception as e:
             db.rollback()
             logger.error(f"Unexpected error storing user message for session {chat_request.session_id}: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Unexpected error storing user message: {e}")

        # Get Berry's configuration from the repository
        logger.debug("Fetching Berry's configuration")
        agent_repository = AgentRepository(db)
        try:
            berry_config = agent_repository.get_complete_agent_configuration("Berry")
        except Exception as e:
             logger.error(f"Error fetching Berry configuration: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Error fetching agent configuration: {e}")

        # If Berry's configuration doesn't exist yet, the migration script should have created it
        if not berry_config:
            logger.error("Berry configuration not found in database. Check migrations.")
            raise HTTPException(status_code=500, detail="Agent configuration not found.")
        logger.debug("Berry configuration fetched successfully.")

        # Get chat history from the database
        logger.debug(f"Fetching chat history for session {chat_request.session_id}")
        try:
            chat_history = []
            db_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == chat_request.session_id
            ).order_by(ChatMessage.timestamp.asc()).all() # Fetch ascending for correct order

            for msg in db_messages:
                chat_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() + "Z" # Ensure ISO format
                })
            logger.debug(f"Fetched {len(chat_history)} messages for history.")
        except SQLAlchemyError as e:
             logger.error(f"Database error fetching history for session {chat_request.session_id}: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Database error fetching history: {e}")
        except Exception as e:
             logger.error(f"Unexpected error fetching history for session {chat_request.session_id}: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Unexpected error fetching history: {e}")

        # Prepare context for the model orchestrator
        logger.debug("Preparing context for model orchestrator")
        context = {
            "agent_configuration": berry_config, # Send the fetched config
            "chat_history": chat_history,
            "user_id": chat_request.user_id,
            "session_id": chat_request.session_id
        }

        # Get response from model orchestrator (SIMULATED)
        logger.info("Simulating model orchestrator response generation")
        try:
            # Determine which prompt template to use based on the conversation context (SIMULATED)
            # For now, we'll use a simple approach, but in a real implementation,
            # this would be more sophisticated (e.g., using an LLM call for intent detection)
            logger.debug("Determining prompt template (simulated)")
            prompt_template_name = "mental_model_building" # Default
            if len(chat_history) <= 1: # Includes the user message just added
                 prompt_template_name = "conversation_intent_recognition"
            elif any(keyword in chat_request.message.lower() for keyword in ["create", "build", "develop", "project", "idea", "make"]):
                 prompt_template_name = "project_potential_detection"

            prompt_template = None
            # Access prompt templates correctly from the fetched config structure
            if berry_config.get("prompt_templates") and prompt_template_name in berry_config["prompt_templates"]:
                 prompt_template = berry_config["prompt_templates"][prompt_template_name]
                 logger.debug(f"Selected prompt template: {prompt_template_name}")
            else:
                 logger.warning(f"Prompt template '{prompt_template_name}' not found in Berry's config.")

            # Add the selected prompt template to the context if found
            if prompt_template:
                context["selected_prompt_template"] = prompt_template

            # SIMULATED Call to the model orchestrator
            logger.debug(f"Simulating call to model orchestrator with context keys: {list(context.keys())}")
            # In a real implementation:
            # response_content, response_actions = await model_orchestrator_client.generate_response(
            #     message=chat_request.message,
            #     context=context
            # )

            # SIMULATED RESPONSE LOGIC:
            message_lower = chat_request.message.lower()
            actions = []
            response = "" # Initialize response

            # Check if this looks like a project creation request
            if any(keyword in message_lower for keyword in ["create", "new project", "start project", "build", "develop"]):
                logger.info("Detected potential project creation request.")
                # Extract a project name - simple simulation
                project_name = "New Project"
                try:
                    if "called" in message_lower or "named" in message_lower:
                        parts = message_lower.split("called" if "called" in message_lower else "named")
                        if len(parts) > 1:
                            # Basic extraction, might need refinement
                            extracted_name = parts[1].strip().split(".")[0].split(",")[0].strip()
                            if extracted_name: # Ensure we got something
                                project_name = " ".join(word.capitalize() for word in extracted_name.split())
                except Exception as name_ex:
                     logger.warning(f"Could not extract project name: {name_ex}")

                logger.info(f"Simulating project creation action for '{project_name}'")
                # Create a project creation action
                actions.append(ChatActionData(
                    type="create_project",
                    data={
                        "name": project_name,
                        "description": f"Project created from chat: {chat_request.message}",
                        "status": "PLANNING",
                        "metadata": { # Ensure metadata structure matches Pydantic model if defined
                            "source": "chat",
                            "session_id": chat_request.session_id,
                            "user_id": chat_request.user_id # Will be None if auth is bypassed
                        }
                    }
                ))

                # Generate a response about creating the project
                response = f"I'd be happy to help you create a new project! Based on what you've told me, I'll set up a project called '{project_name}'. Is there anything specific you'd like me to focus on for this project?"

            # Check if this is about assigning agents
            elif any(keyword in message_lower for keyword in ["assign", "agent", "team", "work on"]):
                logger.info("Detected potential agent assignment request.")
                # In a real implementation, determine which project ID
                simulated_project_id = "project-uuid-placeholder" # Placeholder
                simulated_agent_ids = ["agent-uuid-1", "agent-uuid-2"] # Placeholders
                logger.info(f"Simulating agent assignment action for project '{simulated_project_id}'")
                # Create an agent assignment action
                actions.append(ChatActionData(
                    type="assign_agents",
                    data={
                        "project_id": simulated_project_id,
                        "agent_ids": simulated_agent_ids
                    }
                ))

                # Generate a response about assigning agents
                response = "I'll assign a team of specialized agents to work on your project. They'll handle different aspects like research, development, and testing. Is there anything specific you'd like the agents to focus on?"

            # Default friendly response based on Berry's personality
            else:
                logger.info("Generating default response.")
                # Use a response template if available and configured
                default_response = "Hi there! I'm Berry, your friendly project assistant. How can I help you today?"
                if berry_config.get("response_templates"):
                    if len(chat_history) <= 1 and "greeting" in berry_config["response_templates"]: # History includes current user message
                        response = berry_config["response_templates"]["greeting"]
                    # Add more template logic here if needed
                    else:
                         response = default_response # Fallback if no specific template matches
                else:
                    response = default_response # Fallback if no templates defined

            logger.info("Simulated response generation complete.")

        except Exception as e:
            logger.error(f"Error during simulated response generation: {e}", exc_info=True)
            # Fallback response in case of simulation error
            response = "I'm sorry, I encountered an internal error while thinking of a response. Please try again."
            actions = []

        # Store the bot response in the database
        logger.debug(f"Attempting to store bot response for session {chat_request.session_id}")
        try:
            bot_message = ChatMessage(
                session_id=chat_request.session_id,
                role="bot",
                content=response,
                timestamp=datetime.utcnow(),
                # Ensure actions are serializable if using JSON field
                message_metadata={"actions": [action.model_dump() for action in actions] if actions else []} # Use model_dump for Pydantic V2
            )
            db.add(bot_message)
            db.commit()
            logger.info(f"Bot response stored for session {chat_request.session_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error storing bot response for session {chat_request.session_id}: {e}", exc_info=True)
            # Raise an error here as failing to store the bot response is problematic
            raise HTTPException(status_code=500, detail=f"Database error storing bot response: {e}")
        except Exception as e:
             db.rollback()
             logger.error(f"Unexpected error storing bot response for session {chat_request.session_id}: {e}", exc_info=True)
             raise HTTPException(status_code=500, detail=f"Unexpected error storing bot response: {e}")

        # Return the final response and actions
        logger.info(f"Sending response for session {chat_request.session_id}")
        return ChatResponse(
            response=response,
            actions=actions if actions else [] # Return empty list instead of None for consistency
        )

    except HTTPException as http_exc:
         # Re-raise HTTPExceptions to let FastAPI handle them
         raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error processing chat message for session {chat_request.session_id}: {e}", exc_info=True)
        # Return a generic 500 error for unhandled exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {e}"
        )


@router.get(
    "/sessions/{session_id}",
    # Ensure response_model matches what's returned, including metadata if needed
    response_model=List[Dict[str, Any]], 
    summary="Get chat history",
    description="Get the chat history for a specific session."
)
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get chat history for a session.

    Args:
        session_id: Chat session ID
        db: Database session

    Returns:
        List of chat messages
    """
    logger.info(f"Fetching chat history for session {session_id}")
    try:
        # Get chat messages from the database
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc()).all() # Fetch ascending

        # Format messages for response
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() + "Z", # Ensure ISO format
                "metadata": msg.message_metadata # Correct metadata field name
            })
        
        logger.info(f"Returning {len(formatted_messages)} messages for session {session_id}")
        return formatted_messages

    except SQLAlchemyError as e:
         logger.error(f"Database error fetching history for session {session_id}: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail=f"Database error fetching history: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting chat history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting chat history: {e}"
        )


@router.delete(
    "/sessions/{session_id}",
    summary="Clear chat history",
    description="Clear the chat history for a specific session."
)
async def clear_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear chat history for a session.

    Args:
        session_id: Chat session ID
        db: Database session
    """
    logger.info(f"Clearing chat history for session {session_id}")
    try:
        # Delete chat messages from the database
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        for msg in messages:
            db.delete(msg)
        
        # Delete chat session
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if chat_session:
            db.delete(chat_session)

        db.commit()
        logger.info(f"Successfully cleared chat history for session {session_id}")
        return {"status": "success"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error clearing history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error clearing history: {e}")
    except Exception as e:
        logger.error(f"Unexpected error clearing chat history for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error clearing chat history: {e}"
        )
