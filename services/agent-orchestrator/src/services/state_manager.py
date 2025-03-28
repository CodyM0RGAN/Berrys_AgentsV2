import logging
import json
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    AgentStateError,
    ConcurrentModificationError,
    DatabaseError,
)
from ..models.internal import (
    AgentModel,
    AgentCheckpointModel,
)

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manager for agent state persistence and checkpointing.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the state manager.
        
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
    
    async def create_checkpoint(
        self,
        agent_id: UUID,
        state_data: Dict[str, Any],
        is_recoverable: bool = True,
    ) -> AgentCheckpointModel:
        """
        Create a checkpoint for an agent's state.
        
        Args:
            agent_id: Agent ID
            state_data: State data to checkpoint
            is_recoverable: Whether the checkpoint is recoverable
            
        Returns:
            AgentCheckpointModel: Created checkpoint
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentStateError: If checkpoint creation fails
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent_model = result.scalars().first()
            
            if not agent_model:
                raise AgentNotFoundError(agent_id)
            
            # Check if checkpoint already exists
            query = select(AgentCheckpointModel).where(AgentCheckpointModel.agent_id == agent_id)
            result = await self.db.execute(query)
            existing_checkpoint = result.scalars().first()
            
            if existing_checkpoint:
                # Update existing checkpoint
                existing_checkpoint.state_data = state_data
                existing_checkpoint.sequence_number += 1
                existing_checkpoint.is_recoverable = is_recoverable
                existing_checkpoint.created_at = datetime.utcnow()
                
                await self.db.commit()
                await self.db.refresh(existing_checkpoint)
                
                checkpoint = existing_checkpoint
            else:
                # Create new checkpoint
                checkpoint = AgentCheckpointModel(
                    agent_id=agent_id,
                    state_data=state_data,
                    sequence_number=1,
                    is_recoverable=is_recoverable,
                )
                
                self.db.add(checkpoint)
                await self.db.commit()
                await self.db.refresh(checkpoint)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.checkpoint.created",
                {
                    "agent_id": str(agent_id),
                    "checkpoint_id": str(checkpoint.id),
                    "sequence_number": checkpoint.sequence_number,
                    "is_recoverable": checkpoint.is_recoverable,
                }
            )
            
            return checkpoint
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating checkpoint for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise AgentStateError(agent_id, f"Failed to create checkpoint: {str(e)}")
    
    async def get_latest_checkpoint(
        self,
        agent_id: UUID,
    ) -> Optional[AgentCheckpointModel]:
        """
        Get the latest checkpoint for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[AgentCheckpointModel]: Latest checkpoint if found, None otherwise
            
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
            
            # Get latest checkpoint
            query = select(AgentCheckpointModel).where(AgentCheckpointModel.agent_id == agent_id)
            result = await self.db.execute(query)
            checkpoint = result.scalars().first()
            
            return checkpoint
        except Exception as e:
            logger.error(f"Error getting checkpoint for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to get checkpoint: {str(e)}")
    
    async def delete_checkpoint(
        self,
        agent_id: UUID,
    ) -> None:
        """
        Delete the checkpoint for an agent.
        
        Args:
            agent_id: Agent ID
            
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
            
            # Delete checkpoint
            delete_stmt = delete(AgentCheckpointModel).where(AgentCheckpointModel.agent_id == agent_id)
            await self.db.execute(delete_stmt)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.checkpoint.deleted",
                {
                    "agent_id": str(agent_id),
                }
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting checkpoint for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to delete checkpoint: {str(e)}")
    
    async def update_agent_state(
        self,
        agent_id: UUID,
        state_update: Dict[str, Any],
        create_checkpoint: bool = False,
    ) -> Dict[str, Any]:
        """
        Update an agent's runtime state.
        
        Args:
            agent_id: Agent ID
            state_update: State update
            create_checkpoint: Whether to create a checkpoint
            
        Returns:
            Dict[str, Any]: Updated state
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentStateError: If state update fails
            DatabaseError: If database operation fails
        """
        try:
            # Check if agent exists
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent_model = result.scalars().first()
            
            if not agent_model:
                raise AgentNotFoundError(agent_id)
            
            # Get latest checkpoint
            checkpoint = await self.get_latest_checkpoint(agent_id)
            
            if checkpoint:
                # Update existing state
                current_state = checkpoint.state_data
                
                # Apply update
                for key, value in state_update.items():
                    if isinstance(value, dict) and key in current_state and isinstance(current_state[key], dict):
                        # Merge nested dictionaries
                        current_state[key].update(value)
                    else:
                        # Replace value
                        current_state[key] = value
                
                updated_state = current_state
            else:
                # No existing state, use update as initial state
                updated_state = state_update
            
            # Create checkpoint if requested
            if create_checkpoint:
                await self.create_checkpoint(agent_id, updated_state)
            
            return updated_state
        except Exception as e:
            logger.error(f"Error updating state for agent {agent_id}: {str(e)}")
            
            if isinstance(e, (AgentNotFoundError, AgentStateError)):
                raise
            
            raise AgentStateError(agent_id, f"Failed to update state: {str(e)}")
    
    async def get_agent_state(
        self,
        agent_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get an agent's runtime state.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[Dict[str, Any]]: Agent state if found, None otherwise
            
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
            
            # Get latest checkpoint
            checkpoint = await self.get_latest_checkpoint(agent_id)
            
            if checkpoint:
                return checkpoint.state_data
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting state for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to get state: {str(e)}")
    
    async def schedule_checkpoint(
        self,
        agent_id: UUID,
    ) -> None:
        """
        Schedule a checkpoint for an agent.
        This is a placeholder for a more sophisticated checkpointing system.
        
        Args:
            agent_id: Agent ID
            
        Raises:
            AgentNotFoundError: If agent not found
            DatabaseError: If database operation fails
        """
        try:
            # Get current state
            state = await self.get_agent_state(agent_id)
            
            if state:
                # Create checkpoint
                await self.create_checkpoint(agent_id, state)
        except Exception as e:
            logger.error(f"Error scheduling checkpoint for agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to schedule checkpoint: {str(e)}")
