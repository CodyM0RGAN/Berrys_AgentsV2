import logging
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List, Set
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    InvalidAgentStateError,
    AgentExecutionError,
    ConcurrentModificationError,
    DatabaseError,
)
from ..models.api import (
    AgentStatusChangeRequest,
    StateTransitionValidator,
)
from shared.models.src.enums import AgentStatus
from ..models.enums import AgentStateDetail
from ..models.internal import (
    AgentModel,
    AgentStateModel,
)

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manager for agent lifecycle operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the lifecycle manager.
        
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
        self._running_tasks: Dict[UUID, asyncio.Task] = {}
    
    async def change_agent_state(
        self,
        agent_id: UUID,
        status_change: AgentStatusChangeRequest,
    ) -> AgentModel:
        """
        Change an agent's state.
        
        Args:
            agent_id: Agent ID
            status_change: Status change request
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            ConcurrentModificationError: If agent was modified concurrently
            DatabaseError: If database operation fails
        """
        try:
            # Query agent
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent_model = result.scalars().first()
            
            # Check if agent exists
            if not agent_model:
                raise AgentNotFoundError(agent_id)
            
            current_status = agent_model.status
            current_state_detail = agent_model.state_detail
            target_status = status_change.target_status
            target_state_detail = status_change.target_state_detail
            
            # Validate state transition
            if not StateTransitionValidator.is_valid_transition(current_status, target_status, current_state_detail, target_state_detail):
                raise InvalidAgentStateError(
                    current_state=current_status.value,
                    target_state=target_status.value,
                    current_state_detail=current_state_detail.value if current_state_detail else None,
                    target_state_detail=target_state_detail.value if target_state_detail else None,
                )
            
            # Update agent state with optimistic locking
            update_stmt = (
                update(AgentModel)
                .where(AgentModel.id == agent_id, AgentModel.status == current_status)
                .values(
                    status=target_status,
                    state_detail=target_state_detail,
                    updated_at=datetime.utcnow(),
                    last_active_at=datetime.utcnow() if target_status == AgentStatus.ACTIVE else agent_model.last_active_at,
                )
                .returning(AgentModel)
            )
            
            result = await self.db.execute(update_stmt)
            updated_agent = result.scalar_one_or_none()
            
            if not updated_agent:
                raise ConcurrentModificationError(agent_id)
            
            # Create state history entry
            state_history = AgentStateModel(
                agent_id=agent_id,
                previous_status=current_status,
                new_status=target_status,
                previous_state_detail=current_state_detail,
                new_state_detail=target_state_detail,
                reason=status_change.reason,
            )
            
            self.db.add(state_history)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.status_changed",
                {
                    "agent_id": str(agent_id),
                    "project_id": str(updated_agent.project_id),
                    "previous_status": current_status.value,
                    "new_status": target_status.value,
                    "previous_state_detail": current_state_detail.value if current_state_detail else None,
                    "new_state_detail": target_state_detail.value if target_state_detail else None,
                    "reason": status_change.reason,
                }
            )
            
            # Handle state-specific actions
            await self._handle_state_change(updated_agent, current_status, target_status)
            
            return updated_agent
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error changing agent state for {agent_id}: {str(e)}")
            
            if isinstance(e, (AgentNotFoundError, InvalidAgentStateError, ConcurrentModificationError)):
                raise
            
            raise DatabaseError(f"Failed to change agent state: {str(e)}")
    
    async def initialize_agent(self, agent_id: UUID, reason: Optional[str] = None) -> AgentModel:
        """
        Initialize an agent.
        
        Args:
            agent_id: Agent ID
            reason: Reason for initialization
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            AgentExecutionError: If initialization fails
        """
        status_change = AgentStatusChangeRequest(
            target_status=AgentStatus.INITIALIZING,
            target_state_detail=AgentStateDetail.INITIALIZING,
            reason=reason or "Agent initialization started",
        )
        
        return await self.change_agent_state(agent_id, status_change)
    
    async def activate_agent(self, agent_id: UUID, reason: Optional[str] = None) -> AgentModel:
        """
        Activate an agent.
        
        Args:
            agent_id: Agent ID
            reason: Reason for activation
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            AgentExecutionError: If activation fails
        """
        status_change = AgentStatusChangeRequest(
            target_status=AgentStatus.ACTIVE,
            target_state_detail=AgentStateDetail.ACTIVE,
            reason=reason or "Agent activated",
        )
        
        return await self.change_agent_state(agent_id, status_change)
    
    async def pause_agent(self, agent_id: UUID, reason: Optional[str] = None) -> AgentModel:
        """
        Pause an agent.
        
        Args:
            agent_id: Agent ID
            reason: Reason for pausing
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            AgentExecutionError: If pausing fails
        """
        status_change = AgentStatusChangeRequest(
            target_status=AgentStatus.INACTIVE,
            target_state_detail=AgentStateDetail.PAUSED,
            reason=reason or "Agent paused",
        )
        
        return await self.change_agent_state(agent_id, status_change)
    
    async def terminate_agent(self, agent_id: UUID, reason: Optional[str] = None) -> AgentModel:
        """
        Terminate an agent.
        
        Args:
            agent_id: Agent ID
            reason: Reason for termination
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            AgentExecutionError: If termination fails
        """
        status_change = AgentStatusChangeRequest(
            target_status=AgentStatus.TERMINATED,
            target_state_detail=AgentStateDetail.TERMINATED,
            reason=reason or "Agent terminated",
        )
        
        return await self.change_agent_state(agent_id, status_change)
    
    async def handle_agent_error(self, agent_id: UUID, error_message: str) -> AgentModel:
        """
        Handle an agent error.
        
        Args:
            agent_id: Agent ID
            error_message: Error message
            
        Returns:
            AgentModel: Updated agent model
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
            AgentExecutionError: If error handling fails
        """
        status_change = AgentStatusChangeRequest(
            target_status=AgentStatus.ERROR,
            target_state_detail=AgentStateDetail.ERROR,
            reason=f"Agent error: {error_message}",
        )
        
        return await self.change_agent_state(agent_id, status_change)
    
    async def get_agent_state_history(
        self,
        agent_id: UUID,
        limit: int = 10,
    ) -> List[AgentStateModel]:
        """
        Get an agent's state history.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of history entries to return
            
        Returns:
            List[AgentStateModel]: Agent state history
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent_model = result.scalars().first()
            
            if not agent_model:
                raise AgentNotFoundError(agent_id)
            
            # Query state history
            query = (
                select(AgentStateModel)
                .where(AgentStateModel.agent_id == agent_id)
                .order_by(AgentStateModel.timestamp.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            state_history = result.scalars().all()
            
            return list(state_history)
        except Exception as e:
            logger.error(f"Error getting agent state history for {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to get agent state history: {str(e)}")
    
    async def _handle_state_change(
        self,
        agent: AgentModel,
        previous_status: AgentStatus,
        new_status: AgentStatus,
    ) -> None:
        """
        Handle state-specific actions when an agent's status changes.
        
        Args:
            agent: Agent model
            previous_status: Previous status
            new_status: New status
        """
        agent_id = agent.id
        
        # Handle status-specific actions
        if new_status == AgentStatus.INITIALIZING:
            # Start initialization task
            if self.settings.enable_agent_recovery:
                task = asyncio.create_task(self._initialize_agent_task(agent))
                self._running_tasks[agent_id] = task
        
        elif new_status == AgentStatus.ACTIVE:
            # Start agent task if not already running
            if agent_id not in self._running_tasks or self._running_tasks[agent_id].done():
                task = asyncio.create_task(self._run_agent_task(agent))
                self._running_tasks[agent_id] = task
        
        elif new_status == AgentStatus.INACTIVE and agent.state_detail == AgentStateDetail.PAUSED:
            # Pause agent task (handled by the task itself)
            pass
        
        elif new_status == AgentStatus.TERMINATED:
            # Cancel any running tasks
            if agent_id in self._running_tasks and not self._running_tasks[agent_id].done():
                self._running_tasks[agent_id].cancel()
                try:
                    await self._running_tasks[agent_id]
                except asyncio.CancelledError:
                    pass
                del self._running_tasks[agent_id]
    
    async def _initialize_agent_task(self, agent: AgentModel) -> None:
        """
        Task to initialize an agent.
        
        Args:
            agent: Agent model
        """
        agent_id = agent.id
        
        try:
            logger.info(f"Initializing agent {agent_id}")
            
            # Simulate initialization work
            await asyncio.sleep(2)
            
            # Mark agent as ready
            await self.change_agent_state(
                agent_id,
                AgentStatusChangeRequest(
                    target_status=AgentStatus.INACTIVE,
                    target_state_detail=AgentStateDetail.READY,
                    reason="Agent initialization completed",
                ),
            )
        except asyncio.CancelledError:
            logger.info(f"Agent initialization cancelled for {agent_id}")
            raise
        except Exception as e:
            logger.error(f"Error initializing agent {agent_id}: {str(e)}")
            
            try:
                # Mark agent as error
                await self.handle_agent_error(agent_id, str(e))
            except Exception as inner_e:
                logger.error(f"Error handling agent error for {agent_id}: {str(inner_e)}")
    
    async def _run_agent_task(self, agent: AgentModel) -> None:
        """
        Task to run an agent.
        
        Args:
            agent: Agent model
        """
        agent_id = agent.id
        
        try:
            logger.info(f"Running agent {agent_id}")
            
            # Simulate agent work
            while True:
                # Check if agent is still active
                query = select(AgentModel).where(AgentModel.id == agent_id)
                result = await self.db.execute(query)
                current_agent = result.scalars().first()
                
                if not current_agent or current_agent.status != AgentStatus.ACTIVE:
                    logger.info(f"Agent {agent_id} is no longer active, stopping task")
                    break
                
                # Update last active timestamp
                update_stmt = (
                    update(AgentModel)
                    .where(AgentModel.id == agent_id)
                    .values(last_active_at=datetime.utcnow())
                )
                await self.db.execute(update_stmt)
                await self.db.commit()
                
                # Simulate work
                await asyncio.sleep(self.settings.agent_heartbeat_interval)
        except asyncio.CancelledError:
            logger.info(f"Agent task cancelled for {agent_id}")
            raise
        except Exception as e:
            logger.error(f"Error running agent {agent_id}: {str(e)}")
            
            try:
                # Mark agent as error
                await self.handle_agent_error(agent_id, str(e))
            except Exception as inner_e:
                logger.error(f"Error handling agent error for {agent_id}: {str(inner_e)}")
