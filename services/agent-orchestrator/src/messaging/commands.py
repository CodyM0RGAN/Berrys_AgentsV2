import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from uuid import UUID

from shared.utils.src.messaging import CommandBus
from ..config import Settings
from ..exceptions import (
    AgentNotFoundError,
    InvalidAgentStateError,
    AgentConfigurationError,
    TemplateNotFoundError,
    AgentStateError,
)
from ..models.api import (
    AgentCreate,
    AgentUpdate,
    AgentState,
    AgentStatusChangeRequest,
    AgentExecutionRequest,
)
from ..services.agent_service import AgentService
from ..services.lifecycle_manager import LifecycleManager
from ..services.state_manager import StateManager
from ..services.template_service import TemplateService
from ..services.communication_service import CommunicationService

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Command handler for the agent orchestrator service.
    """
    
    def __init__(
        self,
        command_bus: CommandBus,
        agent_service: AgentService,
        lifecycle_manager: LifecycleManager,
        state_manager: StateManager,
        template_service: TemplateService,
        communication_service: CommunicationService,
    ):
        """
        Initialize the command handler.
        
        Args:
            command_bus: Command bus
            agent_service: Agent service
            lifecycle_manager: Lifecycle manager
            state_manager: State manager
            template_service: Template service
            communication_service: Communication service
        """
        self.command_bus = command_bus
        self.agent_service = agent_service
        self.lifecycle_manager = lifecycle_manager
        self.state_manager = state_manager
        self.template_service = template_service
        self.communication_service = communication_service
    
    async def register_handlers(self) -> None:
        """
        Register command handlers.
        """
        # Register handlers for agent commands
        await self.command_bus.register_command_handler("agent.create", self.handle_create_agent)
        await self.command_bus.register_command_handler("agent.update", self.handle_update_agent)
        await self.command_bus.register_command_handler("agent.delete", self.handle_delete_agent)
        await self.command_bus.register_command_handler("agent.execute", self.handle_execute_agent)
        
        # Register handlers for lifecycle commands
        await self.command_bus.register_command_handler("agent.change_status", self.handle_change_agent_status)
        await self.command_bus.register_command_handler("agent.initialize", self.handle_initialize_agent)
        await self.command_bus.register_command_handler("agent.activate", self.handle_activate_agent)
        await self.command_bus.register_command_handler("agent.pause", self.handle_pause_agent)
        await self.command_bus.register_command_handler("agent.terminate", self.handle_terminate_agent)
        
        # Register handlers for state commands
        await self.command_bus.register_command_handler("agent.update_state", self.handle_update_agent_state)
        await self.command_bus.register_command_handler("agent.create_checkpoint", self.handle_create_checkpoint)
        await self.command_bus.register_command_handler("agent.delete_checkpoint", self.handle_delete_checkpoint)
        
        # Register handlers for template commands
        await self.command_bus.register_command_handler("agent.template.create", self.handle_create_template)
        await self.command_bus.register_command_handler("agent.template.update", self.handle_update_template)
        await self.command_bus.register_command_handler("agent.template.delete", self.handle_delete_template)
        
        # Register handlers for communication commands
        await self.command_bus.register_command_handler("agent.send_communication", self.handle_send_communication)
        await self.command_bus.register_command_handler("agent.mark_delivered", self.handle_mark_delivered)
        
        logger.info("Command handlers registered")
    
    async def handle_create_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentConfigurationError: If agent configuration is invalid
            TemplateNotFoundError: If template not found
        """
        try:
            # Create agent data
            from ..models.api import AgentCreate
            agent_data = AgentCreate(**command_data)
            
            # Create agent
            agent = await self.agent_service.create_agent(agent_data)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "created",
            }
        except Exception as e:
            logger.error(f"Error handling create agent command: {str(e)}")
            raise
    
    async def handle_update_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentConfigurationError: If agent configuration is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.pop("agent_id", None)
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            # Create update data
            from ..models.api import AgentUpdate
            agent_update = AgentUpdate(**command_data)
            
            # Update agent
            agent = await self.agent_service.update_agent(UUID(agent_id), agent_update)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "updated",
                "updated_fields": list(command_data.keys()),
            }
        except Exception as e:
            logger.error(f"Error handling update agent command: {str(e)}")
            raise
    
    async def handle_delete_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            # Delete agent
            await self.agent_service.delete_agent(UUID(agent_id))
            
            # Return result
            return {
                "agent_id": agent_id,
                "status": "deleted",
            }
        except Exception as e:
            logger.error(f"Error handling delete agent command: {str(e)}")
            raise
    
    async def handle_execute_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle execute agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentConfigurationError: If agent configuration is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.pop("agent_id", None)
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            # Create execution request
            from ..models.api import AgentExecutionRequest
            execution_request = AgentExecutionRequest(**command_data)
            
            # Execute agent
            execution_response = await self.agent_service.execute_agent(UUID(agent_id), execution_request)
            
            # Return result
            return {
                "execution_id": str(execution_response.execution_id),
                "agent_id": str(execution_response.agent_id),
                "task_id": str(execution_response.task_id),
                "status": execution_response.status,
                "message": execution_response.message,
            }
        except Exception as e:
            logger.error(f"Error handling execute agent command: {str(e)}")
            raise
    
    async def handle_change_agent_status(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle change agent status command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.pop("agent_id", None)
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            # Create status change request
            from ..models.api import AgentStatusChangeRequest
            status_change = AgentStatusChangeRequest(**command_data)
            
            # Change agent status
            agent = await self.lifecycle_manager.change_agent_state(UUID(agent_id), status_change)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "updated",
                "new_state": agent.state.value,
            }
        except Exception as e:
            logger.error(f"Error handling change agent status command: {str(e)}")
            raise
    
    async def handle_initialize_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initialize agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            reason = command_data.get("reason")
            
            # Initialize agent
            agent = await self.lifecycle_manager.initialize_agent(UUID(agent_id), reason)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "initializing",
            }
        except Exception as e:
            logger.error(f"Error handling initialize agent command: {str(e)}")
            raise
    
    async def handle_activate_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle activate agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            reason = command_data.get("reason")
            
            # Activate agent
            agent = await self.lifecycle_manager.activate_agent(UUID(agent_id), reason)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "active",
            }
        except Exception as e:
            logger.error(f"Error handling activate agent command: {str(e)}")
            raise
    
    async def handle_pause_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle pause agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            reason = command_data.get("reason")
            
            # Pause agent
            agent = await self.lifecycle_manager.pause_agent(UUID(agent_id), reason)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "paused",
            }
        except Exception as e:
            logger.error(f"Error handling pause agent command: {str(e)}")
            raise
    
    async def handle_terminate_agent(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle terminate agent command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            InvalidAgentStateError: If state transition is invalid
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            reason = command_data.get("reason")
            
            # Terminate agent
            agent = await self.lifecycle_manager.terminate_agent(UUID(agent_id), reason)
            
            # Return result
            return {
                "agent_id": str(agent.id),
                "status": "terminated",
            }
        except Exception as e:
            logger.error(f"Error handling terminate agent command: {str(e)}")
            raise
    
    async def handle_update_agent_state(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update agent state command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentStateError: If state update fails
        """
        try:
            # Validate command data
            agent_id = command_data.pop("agent_id", None)
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            create_checkpoint = command_data.pop("create_checkpoint", False)
            
            # Update agent state
            updated_state = await self.state_manager.update_agent_state(
                UUID(agent_id),
                command_data,
                create_checkpoint,
            )
            
            # Return result
            return {
                "agent_id": agent_id,
                "status": "updated",
                "state": updated_state,
            }
        except Exception as e:
            logger.error(f"Error handling update agent state command: {str(e)}")
            raise
    
    async def handle_create_checkpoint(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create checkpoint command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentStateError: If checkpoint creation fails
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            state_data = command_data.get("state_data")
            is_recoverable = command_data.get("is_recoverable", True)
            
            # Create checkpoint
            checkpoint = await self.state_manager.create_checkpoint(
                UUID(agent_id),
                state_data,
                is_recoverable,
            )
            
            # Return result
            return {
                "checkpoint_id": str(checkpoint.id),
                "agent_id": str(checkpoint.agent_id),
                "sequence_number": checkpoint.sequence_number,
                "is_recoverable": checkpoint.is_recoverable,
                "created_at": checkpoint.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error handling create checkpoint command: {str(e)}")
            raise
    
    async def handle_delete_checkpoint(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete checkpoint command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
        """
        try:
            # Validate command data
            agent_id = command_data.get("agent_id")
            if not agent_id:
                raise AgentConfigurationError("Agent ID is required")
            
            # Delete checkpoint
            await self.state_manager.delete_checkpoint(UUID(agent_id))
            
            # Return result
            return {
                "agent_id": agent_id,
                "status": "deleted",
            }
        except Exception as e:
            logger.error(f"Error handling delete checkpoint command: {str(e)}")
            raise
    
    async def handle_create_template(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create template command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            TemplateValidationError: If template data is invalid
        """
        try:
            # Create template data
            from ..models.api import AgentTemplateCreate
            template_data = AgentTemplateCreate(**command_data)
            
            # Create template
            template = await self.template_service.create_template(template_data)
            
            # Return result
            return {
                "template_id": template.id,
                "status": "created",
            }
        except Exception as e:
            logger.error(f"Error handling create template command: {str(e)}")
            raise
    
    async def handle_update_template(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update template command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateValidationError: If template data is invalid
        """
        try:
            # Validate command data
            template_id = command_data.pop("template_id", None)
            if not template_id:
                raise TemplateNotFoundError("unknown", "Template ID is required")
            
            # Create update data
            from ..models.api import AgentTemplateUpdate
            template_update = AgentTemplateUpdate(**command_data)
            
            # Update template
            template = await self.template_service.update_template(template_id, template_update)
            
            # Return result
            return {
                "template_id": template.id,
                "status": "updated",
                "updated_fields": list(command_data.keys()),
            }
        except Exception as e:
            logger.error(f"Error handling update template command: {str(e)}")
            raise
    
    async def handle_delete_template(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle delete template command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        try:
            # Validate command data
            template_id = command_data.get("template_id")
            if not template_id:
                raise TemplateNotFoundError("unknown", "Template ID is required")
            
            # Delete template
            await self.template_service.delete_template(template_id)
            
            # Return result
            return {
                "template_id": template_id,
                "status": "deleted",
            }
        except Exception as e:
            logger.error(f"Error handling delete template command: {str(e)}")
            raise
    
    async def handle_send_communication(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle send communication command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentNotFoundError: If agent not found
            AgentCommunicationError: If communication fails
        """
        try:
            # Validate command data
            from_agent_id = command_data.pop("from_agent_id", None)
            if not from_agent_id:
                raise AgentConfigurationError("From agent ID is required")
            
            # Create communication request
            from ..models.api import AgentCommunicationRequest
            communication_request = AgentCommunicationRequest(**command_data)
            
            # Send communication
            response = await self.communication_service.send_communication(
                UUID(from_agent_id),
                communication_request,
            )
            
            # Return result
            return {
                "communication_id": str(response.communication_id),
                "from_agent_id": str(response.from_agent_id),
                "to_agent_id": str(response.to_agent_id),
                "status": response.status,
                "timestamp": response.timestamp.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error handling send communication command: {str(e)}")
            raise
    
    async def handle_mark_delivered(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle mark delivered command.
        
        Args:
            command_data: Command data
            
        Returns:
            Dict[str, Any]: Result data
            
        Raises:
            AgentCommunicationError: If communication not found
        """
        try:
            # Validate command data
            communication_id = command_data.get("communication_id")
            if not communication_id:
                raise AgentConfigurationError("Communication ID is required")
            
            # Mark as delivered
            communication = await self.communication_service.mark_as_delivered(UUID(communication_id))
            
            # Return result
            return {
                "communication_id": str(communication.id),
                "status": "delivered",
                "delivered_at": communication.delivered_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error handling mark delivered command: {str(e)}")
            raise


# Command sending helper functions

async def send_create_agent_command(
    command_bus: CommandBus,
    name: str,
    agent_type: str,
    project_id: UUID,
    description: Optional[str] = None,
    template_id: Optional[str] = None,
    configuration: Optional[Dict[str, Any]] = None,
    prompt_template: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send create agent command.
    
    Args:
        command_bus: Command bus
        name: Agent name
        agent_type: Agent type
        project_id: Project ID
        description: Agent description
        template_id: Template ID
        configuration: Agent configuration
        prompt_template: Prompt template
        
    Returns:
        Dict[str, Any]: Command result
    """
    # Prepare command data
    command_data = {
        "name": name,
        "type": agent_type,
        "project_id": str(project_id),
    }
    
    if description:
        command_data["description"] = description
    
    if template_id:
        command_data["template_id"] = template_id
    
    if configuration:
        command_data["configuration"] = configuration
    
    if prompt_template:
        command_data["prompt_template"] = prompt_template
    
    # Send command
    result = await command_bus.send_command(
        "agent-orchestrator",
        "agent.create",
        command_data,
        wait_for_response=True,
    )
    
    return result
