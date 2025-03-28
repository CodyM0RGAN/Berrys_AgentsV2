"""
Human Interaction service.

This service handles human interaction functionality, including approval requests,
feedback collection, and notifications.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    ExecutionNotFoundError,
    HumanInteractionError,
    DatabaseError,
)
from ..models.api import (
    HumanInteractionRequest,
    HumanInteractionResponse,
    HumanApprovalRequest,
    HumanApprovalResponse,
    HumanFeedbackRequest,
    HumanFeedbackResponse,
)
from ..models.internal import (
    AgentModel,
    AgentExecutionModel,
    HumanInteractionModel,
)

logger = logging.getLogger(__name__)

class HumanInteractionService:
    """
    Service for handling human interactions with agents.
    
    This service manages approval requests, feedback collection, and notifications
    between humans and agents.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the human interaction service.
        
        Args:
            db: Database session
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
        """
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
    
    async def request_approval(
        self,
        agent_id: UUID,
        approval_request: HumanApprovalRequest,
    ) -> HumanApprovalResponse:
        """
        Request approval from a human.
        
        Args:
            agent_id: Agent ID
            approval_request: Approval request
            
        Returns:
            HumanApprovalResponse: Response with interaction ID
            
        Raises:
            AgentNotFoundError: If agent not found
            ExecutionNotFoundError: If execution not found
            HumanInteractionError: If request fails
        """
        try:
            # Check if agent exists
            agent = await self._get_agent(agent_id)
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Check execution if provided
            if approval_request.execution_id:
                execution = await self._get_execution(approval_request.execution_id)
                if not execution:
                    raise ExecutionNotFoundError(approval_request.execution_id)
            
            # Create interaction model
            interaction = HumanInteractionModel(
                agent_id=agent_id,
                execution_id=approval_request.execution_id,
                type="approval_request",
                status="pending",
                content={
                    "title": approval_request.title,
                    "description": approval_request.description,
                    "options": approval_request.options,
                    "context": approval_request.context,
                    "deadline": approval_request.deadline.isoformat() if approval_request.deadline else None,
                    "priority": approval_request.priority,
                },
                interaction_metadata=approval_request.metadata or {},
            )
            
            # Save to database
            self.db.add(interaction)
            await self.db.commit()
            await self.db.refresh(interaction)
            
            # Emit approval request event
            await self._emit_approval_request_event(interaction)
            
            # Create response
            response = HumanApprovalResponse(
                interaction_id=interaction.id,
                agent_id=agent_id,
                status="pending",
                timestamp=datetime.utcnow(),
            )
            
            return response
        
        except (AgentNotFoundError, ExecutionNotFoundError):
            # Re-raise these specific exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error requesting approval for agent {agent_id}: {str(e)}")
            raise HumanInteractionError(agent_id, f"Failed to request approval: {str(e)}")
    
    async def provide_approval(
        self,
        interaction_id: UUID,
        response: str,
        feedback: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> HumanInteractionModel:
        """
        Provide approval for an interaction.
        
        Args:
            interaction_id: Interaction ID
            response: Response (e.g., "approve", "reject", or option text)
            feedback: Optional feedback text
            user_id: Optional user ID who provided the response
            
        Returns:
            HumanInteractionModel: Updated interaction
            
        Raises:
            HumanInteractionError: If interaction not found or not an approval request
        """
        try:
            # Get interaction
            interaction = await self.get_interaction(interaction_id)
            
            if not interaction:
                raise HumanInteractionError(
                    UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder UUID
                    f"Interaction with ID {interaction_id} not found"
                )
            
            if interaction.type != "approval_request":
                raise HumanInteractionError(
                    interaction.agent_id,
                    f"Interaction with ID {interaction_id} is not an approval request"
                )
            
            # Update interaction
            interaction.status = "completed"
            interaction.completed_at = datetime.utcnow()
            
            # Add response data
            interaction.response = {
                "decision": response,
                "feedback": feedback,
                "user_id": str(user_id) if user_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Save changes
            await self.db.commit()
            await self.db.refresh(interaction)
            
            # Emit approval response event
            await self._emit_approval_response_event(interaction)
            
            return interaction
        
        except Exception as e:
            if isinstance(e, HumanInteractionError):
                raise
            
            logger.error(f"Error providing approval for interaction {interaction_id}: {str(e)}")
            raise HumanInteractionError(
                UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder UUID
                f"Failed to provide approval: {str(e)}"
            )
    
    async def submit_feedback(
        self,
        agent_id: UUID,
        feedback_request: HumanFeedbackRequest,
    ) -> HumanFeedbackResponse:
        """
        Submit feedback for an agent.
        
        Args:
            agent_id: Agent ID
            feedback_request: Feedback request
            
        Returns:
            HumanFeedbackResponse: Response with interaction ID
            
        Raises:
            AgentNotFoundError: If agent not found
            ExecutionNotFoundError: If execution not found
            HumanInteractionError: If request fails
        """
        try:
            # Check if agent exists
            agent = await self._get_agent(agent_id)
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Check execution if provided
            if feedback_request.execution_id:
                execution = await self._get_execution(feedback_request.execution_id)
                if not execution:
                    raise ExecutionNotFoundError(feedback_request.execution_id)
            
            # Create interaction model
            interaction = HumanInteractionModel(
                agent_id=agent_id,
                execution_id=feedback_request.execution_id,
                type="feedback",
                status="completed",  # Feedback is completed immediately
                content={
                    "feedback_type": feedback_request.feedback_type,
                    "content": feedback_request.content,
                    "rating": feedback_request.rating,
                    "context": feedback_request.context,
                },
                interaction_metadata=feedback_request.metadata or {},
                completed_at=datetime.utcnow(),
            )
            
            # Save to database
            self.db.add(interaction)
            await self.db.commit()
            await self.db.refresh(interaction)
            
            # Emit feedback event
            await self._emit_feedback_event(interaction)
            
            # Create response
            response = HumanFeedbackResponse(
                interaction_id=interaction.id,
                agent_id=agent_id,
                status="completed",
                timestamp=datetime.utcnow(),
            )
            
            return response
        
        except (AgentNotFoundError, ExecutionNotFoundError):
            # Re-raise these specific exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error submitting feedback for agent {agent_id}: {str(e)}")
            raise HumanInteractionError(agent_id, f"Failed to submit feedback: {str(e)}")
    
    async def send_notification(
        self,
        agent_id: UUID,
        notification: Dict[str, Any],
        execution_id: Optional[UUID] = None,
        priority: str = "normal",
    ) -> HumanInteractionModel:
        """
        Send a notification to humans.
        
        Args:
            agent_id: Agent ID
            notification: Notification content
            execution_id: Optional related execution ID
            priority: Priority level
            
        Returns:
            HumanInteractionModel: Created interaction
            
        Raises:
            AgentNotFoundError: If agent not found
            ExecutionNotFoundError: If execution not found
            HumanInteractionError: If notification fails
        """
        try:
            # Check if agent exists
            agent = await self._get_agent(agent_id)
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Check execution if provided
            if execution_id:
                execution = await self._get_execution(execution_id)
                if not execution:
                    raise ExecutionNotFoundError(execution_id)
            
            # Create interaction model
            interaction = HumanInteractionModel(
                agent_id=agent_id,
                execution_id=execution_id,
                type="notification",
                status="delivered",  # Notifications are delivered immediately
                content=notification,
                interaction_metadata={"priority": priority},
            )
            
            # Save to database
            self.db.add(interaction)
            await self.db.commit()
            await self.db.refresh(interaction)
            
            # Emit notification event
            await self._emit_notification_event(interaction)
            
            return interaction
        
        except (AgentNotFoundError, ExecutionNotFoundError):
            # Re-raise these specific exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error sending notification for agent {agent_id}: {str(e)}")
            raise HumanInteractionError(agent_id, f"Failed to send notification: {str(e)}")
    
    async def get_interaction(self, interaction_id: UUID) -> Optional[HumanInteractionModel]:
        """
        Get an interaction by ID.
        
        Args:
            interaction_id: Interaction ID
            
        Returns:
            Optional[HumanInteractionModel]: Interaction if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(HumanInteractionModel).where(HumanInteractionModel.id == interaction_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting interaction {interaction_id}: {str(e)}")
            raise DatabaseError(f"Failed to get interaction: {str(e)}")
    
    async def get_interactions_for_agent(
        self,
        agent_id: UUID,
        interaction_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HumanInteractionModel], int]:
        """
        Get interactions for an agent.
        
        Args:
            agent_id: Agent ID
            interaction_type: Filter by interaction type
            status: Filter by status
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[HumanInteractionModel], int]: List of interactions and total count
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            agent = await self._get_agent(agent_id)
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Build query
            query = select(HumanInteractionModel).where(HumanInteractionModel.agent_id == agent_id)
            
            if interaction_type:
                query = query.where(HumanInteractionModel.type == interaction_type)
            
            if status:
                query = query.where(HumanInteractionModel.status == status)
            
            # Add ordering
            query = query.order_by(desc(HumanInteractionModel.created_at))
            
            # Get total count
            count_query = select(HumanInteractionModel).where(query.whereclause)
            count_result = await self.db.execute(count_query)
            total = len(count_result.scalars().all())
            
            # Add pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            interactions = result.scalars().all()
            
            return interactions, total
        
        except AgentNotFoundError:
            # Re-raise this specific exception
            raise
        
        except Exception as e:
            logger.error(f"Error getting interactions for agent {agent_id}: {str(e)}")
            raise DatabaseError(f"Failed to get interactions: {str(e)}")
    
    async def get_pending_approvals(
        self,
        project_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HumanInteractionModel], int]:
        """
        Get pending approval requests.
        
        Args:
            project_id: Optional filter by project ID
            page: Page number
            page_size: Page size
            
        Returns:
            Tuple[List[HumanInteractionModel], int]: List of pending approvals and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query for pending approval requests
            query = select(HumanInteractionModel).where(
                and_(
                    HumanInteractionModel.type == "approval_request",
                    HumanInteractionModel.status == "pending"
                )
            )
            
            if project_id:
                # Join with agent model to filter by project ID
                query = select(HumanInteractionModel).join(
                    AgentModel,
                    HumanInteractionModel.agent_id == AgentModel.id
                ).where(
                    and_(
                        HumanInteractionModel.type == "approval_request",
                        HumanInteractionModel.status == "pending",
                        AgentModel.project_id == project_id
                    )
                )
            
            # Add ordering by priority and creation time
            query = query.order_by(
                # First by priority (assuming it's stored in metadata)
                # Then by creation time (oldest first for fairness)
                HumanInteractionModel.created_at
            )
            
            # Get total count
            count_query = select(HumanInteractionModel).where(query.whereclause)
            count_result = await self.db.execute(count_query)
            total = len(count_result.scalars().all())
            
            # Add pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            approvals = result.scalars().all()
            
            return approvals, total
        
        except Exception as e:
            logger.error(f"Error getting pending approvals: {str(e)}")
            raise DatabaseError(f"Failed to get pending approvals: {str(e)}")
    
    async def _get_agent(self, agent_id: UUID) -> Optional[AgentModel]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[AgentModel]: Agent if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise DatabaseError(f"Failed to get agent: {str(e)}")
    
    async def _get_execution(self, execution_id: UUID) -> Optional[AgentExecutionModel]:
        """
        Get execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Optional[AgentExecutionModel]: Execution if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            query = select(AgentExecutionModel).where(AgentExecutionModel.id == execution_id)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting execution {execution_id}: {str(e)}")
            raise DatabaseError(f"Failed to get execution: {str(e)}")
    
    async def _emit_approval_request_event(self, interaction: HumanInteractionModel) -> None:
        """
        Emit approval request event.
        
        Args:
            interaction: Interaction model
        """
        event_data = {
            "interaction_id": str(interaction.id),
            "agent_id": str(interaction.agent_id),
            "execution_id": str(interaction.execution_id) if interaction.execution_id else None,
            "type": interaction.type,
            "content": interaction.content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await self.event_bus.publish(
            event_name="human_interaction.approval_requested",
            data=event_data
        )
    
    async def _emit_approval_response_event(self, interaction: HumanInteractionModel) -> None:
        """
        Emit approval response event.
        
        Args:
            interaction: Interaction model
        """
        event_data = {
            "interaction_id": str(interaction.id),
            "agent_id": str(interaction.agent_id),
            "execution_id": str(interaction.execution_id) if interaction.execution_id else None,
            "type": interaction.type,
            "status": interaction.status,
            "response": interaction.response,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await self.event_bus.publish(
            event_name="human_interaction.approval_received",
            data=event_data
        )
    
    async def _emit_feedback_event(self, interaction: HumanInteractionModel) -> None:
        """
        Emit feedback event.
        
        Args:
            interaction: Interaction model
        """
        event_data = {
            "interaction_id": str(interaction.id),
            "agent_id": str(interaction.agent_id),
            "execution_id": str(interaction.execution_id) if interaction.execution_id else None,
            "type": interaction.type,
            "content": interaction.content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await self.event_bus.publish(
            event_name="human_interaction.feedback_submitted",
            data=event_data
        )
    
    async def _emit_notification_event(self, interaction: HumanInteractionModel) -> None:
        """
        Emit notification event.
        
        Args:
            interaction: Interaction model
        """
        event_data = {
            "interaction_id": str(interaction.id),
            "agent_id": str(interaction.agent_id),
            "execution_id": str(interaction.execution_id) if interaction.execution_id else None,
            "type": interaction.type,
            "content": interaction.content,
            "metadata": interaction.interaction_metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        await self.event_bus.publish(
            event_name="human_interaction.notification_sent",
            data=event_data
        )
