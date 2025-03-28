import logging
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    AgentCommunicationError,
    DatabaseError,
)
from ..models.api import (
    AgentCommunicationRequest,
    AgentCommunicationResponse,
)
from ..models.internal import (
    AgentModel,
    AgentCommunicationModel,
)

logger = logging.getLogger(__name__)


class CommunicationService:
    """
    Service for agent communication operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the communication service.
        
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
    
    async def send_communication(
        self,
        from_agent_id: UUID,
        communication_request: AgentCommunicationRequest,
    ) -> AgentCommunicationResponse:
        """
        Send a communication from one agent to another.
        
        Args:
            from_agent_id: Sender agent ID
            communication_request: Communication request
            
        Returns:
            AgentCommunicationResponse: Communication response
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentCommunicationError: If communication fails
            DatabaseError: If database operation fails
        """
        try:
            # Check if sender agent exists
            query = select(AgentModel).where(AgentModel.id == from_agent_id)
            result = await self.db.execute(query)
            from_agent = result.scalars().first()
            
            if not from_agent:
                raise AgentNotFoundError(from_agent_id)
            
            # Check if recipient agent exists
            to_agent_id = communication_request.to_agent_id
            query = select(AgentModel).where(AgentModel.id == to_agent_id)
            result = await self.db.execute(query)
            to_agent = result.scalars().first()
            
            if not to_agent:
                raise AgentNotFoundError(to_agent_id)
            
            # Create communication record
            communication = AgentCommunicationModel(
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                type=communication_request.type,
                content=communication_request.content,
                status="sent",
            )
            
            self.db.add(communication)
            await self.db.commit()
            await self.db.refresh(communication)
            
            # Create response
            response = AgentCommunicationResponse(
                communication_id=communication.id,
                from_agent_id=from_agent_id,
                to_agent_id=to_agent_id,
                status="sent",
                timestamp=communication.created_at,
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.communication.sent",
                {
                    "communication_id": str(communication.id),
                    "from_agent_id": str(from_agent_id),
                    "to_agent_id": str(to_agent_id),
                    "type": communication.type,
                    "project_id": str(from_agent.project_id),
                }
            )
            
            return response
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error sending communication from {from_agent_id} to {communication_request.to_agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise AgentCommunicationError(
                from_agent_id=from_agent_id,
                to_agent_id=communication_request.to_agent_id,
                message=f"Failed to send communication: {str(e)}",
            )
    
    async def mark_as_delivered(
        self,
        communication_id: UUID,
    ) -> AgentCommunicationModel:
        """
        Mark a communication as delivered.
        
        Args:
            communication_id: Communication ID
            
        Returns:
            AgentCommunicationModel: Updated communication
            
        Raises:
            AgentCommunicationError: If communication not found
            DatabaseError: If database operation fails
        """
        try:
            # Query communication
            query = select(AgentCommunicationModel).where(AgentCommunicationModel.id == communication_id)
            result = await self.db.execute(query)
            communication = result.scalars().first()
            
            if not communication:
                raise AgentCommunicationError(
                    from_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                    to_agent_id=UUID('00000000-0000-0000-0000-000000000000'),
                    message=f"Communication {communication_id} not found",
                )
            
            # Update status and delivered timestamp
            communication.status = "delivered"
            communication.delivered_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(communication)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.communication.delivered",
                {
                    "communication_id": str(communication.id),
                    "from_agent_id": str(communication.from_agent_id),
                    "to_agent_id": str(communication.to_agent_id),
                }
            )
            
            return communication
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking communication {communication_id} as delivered: {str(e)}")
            
            if isinstance(e, AgentCommunicationError):
                raise
            
            raise DatabaseError(f"Failed to mark communication as delivered: {str(e)}")
    
    async def get_communications_for_agent(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        direction: str = "both",
        status: Optional[str] = None,
    ) -> Tuple[List[AgentCommunicationModel], int]:
        """
        Get communications for an agent.
        
        Args:
            agent_id: Agent ID
            page: Page number
            page_size: Page size
            direction: Direction of communications ("sent", "received", or "both")
            status: Filter by status
            
        Returns:
            Tuple[List[AgentCommunicationModel], int]: List of communications and total count
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent = result.scalars().first()
            
            if not agent:
                raise AgentNotFoundError(agent_id)
            
            # Build query
            if direction == "sent":
                query = select(AgentCommunicationModel).where(AgentCommunicationModel.from_agent_id == agent_id)
                count_query = select(func.count()).where(AgentCommunicationModel.from_agent_id == agent_id)
            elif direction == "received":
                query = select(AgentCommunicationModel).where(AgentCommunicationModel.to_agent_id == agent_id)
                count_query = select(func.count()).where(AgentCommunicationModel.to_agent_id == agent_id)
            else:  # "both"
                query = select(AgentCommunicationModel).where(
                    or_(
                        AgentCommunicationModel.from_agent_id == agent_id,
                        AgentCommunicationModel.to_agent_id == agent_id,
                    )
                )
                count_query = select(func.count()).where(
                    or_(
                        AgentCommunicationModel.from_agent_id == agent_id,
                        AgentCommunicationModel.to_agent_id == agent_id,
                    )
                )
            
            # Apply status filter
            if status:
                query = query.where(AgentCommunicationModel.status == status)
                count_query = count_query.where(AgentCommunicationModel.status == status)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination and ordering
            query = (
                query
                .order_by(AgentCommunicationModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            
            # Execute query
            result = await self.db.execute(query)
            communications = result.scalars().all()
            
            return list(communications), total
        except Exception as e:
            logger.error(f"Error getting communications for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to get communications: {str(e)}")
    
    async def get_communication(
        self,
        communication_id: UUID,
    ) -> Optional[AgentCommunicationModel]:
        """
        Get a communication by ID.
        
        Args:
            communication_id: Communication ID
            
        Returns:
            Optional[AgentCommunicationModel]: Communication if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query communication
            query = select(AgentCommunicationModel).where(AgentCommunicationModel.id == communication_id)
            result = await self.db.execute(query)
            communication = result.scalars().first()
            
            return communication
        except Exception as e:
            logger.error(f"Error getting communication {communication_id}: {str(e)}")
            raise DatabaseError(f"Failed to get communication: {str(e)}")
