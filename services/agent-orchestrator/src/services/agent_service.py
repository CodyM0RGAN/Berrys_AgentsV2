import logging
import json
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import AgentOrchestratorConfig
from ..exceptions import (
    AgentNotFoundError,
    AgentConfigurationError,
    DatabaseError,
    TemplateNotFoundError,
)
from ..models.api import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentExecutionRequest,
    AgentExecutionResponse,
)
from shared.models.src.enums import AgentStatus
from ..models.enums import AgentStateDetail
from ..models.internal import (
    AgentModel,
    AgentTemplateModel,
    AgentStateModel,
    AgentExecutionModel,
)

logger = logging.getLogger(__name__)


class AgentService:
    """
    Service for agent operations.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: AgentOrchestratorConfig,
    ):
        """
        Initialize the agent service.
        
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
    
    async def create_agent(self, agent_data: AgentCreate) -> AgentResponse:
        """
        Create a new agent.
        
        Args:
            agent_data: Agent data
            
        Returns:
            AgentResponse: Created agent
            
        Raises:
            AgentConfigurationError: If agent configuration is invalid
            TemplateNotFoundError: If template not found
            DatabaseError: If database operation fails
        """
        try:
            # If template_id is provided, get template
            if agent_data.template_id:
                template = await self._get_template(agent_data.template_id)
                if not template:
                    raise TemplateNotFoundError(agent_data.template_id)
                
                # Apply template defaults if not overridden
                configuration = template.default_configuration.copy()
                configuration.update(agent_data.configuration)
                
                # Use template prompt if not provided
                prompt_template = agent_data.prompt_template or template.prompt_template
            else:
                configuration = agent_data.configuration
                prompt_template = agent_data.prompt_template
            
            # Create agent model
            agent_model = AgentModel(
                name=agent_data.name,
                description=agent_data.description,
                type=agent_data.type,
                status=AgentStatus.INACTIVE,
                state_detail=AgentStateDetail.CREATED,
                project_id=agent_data.project_id,
                template_id=agent_data.template_id,
                configuration=configuration,
                prompt_template=prompt_template,
            )
            
            # Add to database
            self.db.add(agent_model)
            await self.db.commit()
            await self.db.refresh(agent_model)
            
            # Create initial state history entry
            state_history = AgentStateModel(
                agent_id=agent_model.id,
                previous_status=None,
                new_status=AgentStatus.INACTIVE,
                previous_state_detail=None,
                new_state_detail=AgentStateDetail.CREATED,
                reason="Agent created",
            )
            
            self.db.add(state_history)
            await self.db.commit()
            
            # Convert to API model
            agent = AgentResponse.from_orm(agent_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.created",
                {
                    "agent_id": str(agent.id),
                    "project_id": str(agent.project_id),
                    "name": agent.name,
                    "type": agent.type.value,
                    "status": agent.status.value,
                    "state_detail": agent.state_detail.value if agent.state_detail else None,
                }
            )
            
            return agent
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            
            if isinstance(e, (AgentConfigurationError, TemplateNotFoundError)):
                raise
            
            raise DatabaseError(f"Failed to create agent: {str(e)}")
    
    async def get_agent(self, agent_id: UUID) -> Optional[AgentResponse]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[AgentResponse]: Agent if found, None otherwise
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Query agent
            query = select(AgentModel).where(AgentModel.id == agent_id)
            result = await self.db.execute(query)
            agent_model = result.scalars().first()
            
            # Return None if not found
            if not agent_model:
                return None
            
            # Convert to API model
            return AgentResponse.from_orm(agent_model)
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {str(e)}")
            raise DatabaseError(f"Failed to get agent: {str(e)}")
    
    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[UUID] = None,
        state: Optional[str] = None,
        type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[AgentResponse], int]:
        """
        List agents with pagination and filtering.
        
        Args:
            page: Page number
            page_size: Page size
            project_id: Filter by project ID
            state: Filter by state
            type: Filter by type
            search: Search term
            
        Returns:
            Tuple[List[AgentResponse], int]: List of agents and total count
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Build query
            query = select(AgentModel)
            count_query = select(func.count()).select_from(AgentModel)
            
            # Apply filters
            filters = []
            
            if project_id:
                filters.append(AgentModel.project_id == project_id)
            
            if state:
                try:
                    # Try to parse as status first
                    status_enum = AgentStatus(state)
                    filters.append(AgentModel.status == status_enum)
                except ValueError:
                    try:
                        # Try to parse as state_detail
                        state_detail_enum = AgentStateDetail(state)
                        filters.append(AgentModel.state_detail == state_detail_enum)
                    except ValueError:
                        # Invalid state, ignore filter
                        pass
            
            if type:
                filters.append(AgentModel.type == type)
            
            if search:
                search_filter = or_(
                    AgentModel.name.ilike(f"%{search}%"),
                    AgentModel.description.ilike(f"%{search}%"),
                )
                filters.append(search_filter)
            
            # Apply filters to queries
            if filters:
                filter_clause = and_(*filters)
                query = query.where(filter_clause)
                count_query = count_query.where(filter_clause)
            
            # Get total count
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()
            
            # Apply pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # Execute query
            result = await self.db.execute(query)
            agent_models = result.scalars().all()
            
            # Convert to API models
            agents = [AgentResponse.from_orm(model) for model in agent_models]
            
            return agents, total
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise DatabaseError(f"Failed to list agents: {str(e)}")
    
    async def update_agent(
        self,
        agent_id: UUID,
        agent_update: AgentUpdate,
    ) -> AgentResponse:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            agent_update: Agent update data
            
        Returns:
            AgentResponse: Updated agent
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentConfigurationError: If agent configuration is invalid
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
            
            # Update fields
            update_data = agent_update.dict(exclude_unset=True)
            updated_fields = list(update_data.keys())
            
            for key, value in update_data.items():
                if key == "configuration" and value is not None:
                    # Merge configuration
                    current_config = agent_model.configuration or {}
                    current_config.update(value)
                    setattr(agent_model, key, current_config)
                else:
                    setattr(agent_model, key, value)
            
            # Update timestamp
            agent_model.updated_at = datetime.utcnow()
            
            # Commit changes
            await self.db.commit()
            await self.db.refresh(agent_model)
            
            # Convert to API model
            agent = AgentResponse.from_orm(agent_model)
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.updated",
                {
                    "agent_id": str(agent.id),
                    "project_id": str(agent.project_id),
                    "updated_fields": updated_fields,
                    "status": agent.status.value,
                    "state_detail": agent.state_detail.value if agent.state_detail else None,
                }
            )
            
            return agent
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating agent {agent_id}: {str(e)}")
            
            if isinstance(e, (AgentNotFoundError, AgentConfigurationError)):
                raise
            
            raise DatabaseError(f"Failed to update agent: {str(e)}")
    
    async def delete_agent(self, agent_id: UUID) -> None:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Raises:
            AgentNotFoundError: If agent not found
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
            
            # Store agent data for event
            agent_data = {
                "agent_id": str(agent_model.id),
                "project_id": str(agent_model.project_id),
                "name": agent_model.name,
                "type": agent_model.type.value,
                "status": agent_model.status.value,
                "state_detail": agent_model.state_detail.value if agent_model.state_detail else None,
            }
            
            # Delete agent
            await self.db.delete(agent_model)
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.deleted",
                agent_data
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting agent {agent_id}: {str(e)}")
            
            if isinstance(e, AgentNotFoundError):
                raise
            
            raise DatabaseError(f"Failed to delete agent: {str(e)}")
    
    async def execute_agent(
        self,
        agent_id: UUID,
        execution_request: AgentExecutionRequest,
    ) -> AgentExecutionResponse:
        """
        Execute an agent on a task.
        
        Args:
            agent_id: Agent ID
            execution_request: Execution request
            
        Returns:
            AgentExecutionResponse: Execution response
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentConfigurationError: If agent configuration is invalid
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
            
            # Create execution record
            execution_model = AgentExecutionModel(
                agent_id=agent_id,
                task_id=execution_request.task_id,
                status="pending",
                parameters=execution_request.parameters,
            )
            
            self.db.add(execution_model)
            await self.db.commit()
            await self.db.refresh(execution_model)
            
            # Create execution response
            execution_response = AgentExecutionResponse(
                execution_id=execution_model.id,
                agent_id=agent_id,
                task_id=execution_request.task_id,
                status="started",
                message="Agent execution started successfully",
            )
            
            # Publish event
            await self.event_bus.publish_event(
                "agent.execution.started",
                {
                    "execution_id": str(execution_model.id),
                    "agent_id": str(agent_id),
                    "task_id": str(execution_request.task_id),
                    "project_id": str(agent_model.project_id),
                }
            )
            
            return execution_response
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error executing agent {agent_id}: {str(e)}")
            
            if isinstance(e, (AgentNotFoundError, AgentConfigurationError)):
                raise
            
            raise DatabaseError(f"Failed to execute agent: {str(e)}")
    
    async def _get_template(self, template_id: str) -> Optional[AgentTemplateModel]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Optional[AgentTemplateModel]: Template if found, None otherwise
        """
        query = select(AgentTemplateModel).where(AgentTemplateModel.id == template_id)
        result = await self.db.execute(query)
        return result.scalars().first()
