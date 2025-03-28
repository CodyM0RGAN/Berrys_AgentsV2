import logging
from typing import Dict, Any, Callable, Awaitable
from uuid import UUID

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)


class EventHandler:
    """
    Event handler for the agent orchestrator service.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize the event handler.
        
        Args:
            event_bus: Event bus
        """
        self.event_bus = event_bus
    
    async def register_handlers(self) -> None:
        """
        Register event handlers.
        """
        # Register handlers for agent events
        await self.event_bus.subscribe_to_event("agent.created", self.handle_agent_created)
        await self.event_bus.subscribe_to_event("agent.updated", self.handle_agent_updated)
        await self.event_bus.subscribe_to_event("agent.deleted", self.handle_agent_deleted)
        await self.event_bus.subscribe_to_event("agent.status_changed", self.handle_agent_status_changed)
        await self.event_bus.subscribe_to_event("agent.execution.started", self.handle_agent_execution_started)
        await self.event_bus.subscribe_to_event("agent.execution.completed", self.handle_agent_execution_completed)
        
        # Register handlers for template events
        await self.event_bus.subscribe_to_event("agent.template.created", self.handle_template_created)
        await self.event_bus.subscribe_to_event("agent.template.updated", self.handle_template_updated)
        await self.event_bus.subscribe_to_event("agent.template.deleted", self.handle_template_deleted)
        
        # Register handlers for communication events
        await self.event_bus.subscribe_to_event("agent.communication.sent", self.handle_communication_sent)
        await self.event_bus.subscribe_to_event("agent.communication.delivered", self.handle_communication_delivered)
        
        # Register handlers for checkpoint events
        await self.event_bus.subscribe_to_event("agent.checkpoint.created", self.handle_checkpoint_created)
        await self.event_bus.subscribe_to_event("agent.checkpoint.deleted", self.handle_checkpoint_deleted)
        
        # Register handlers for external events
        await self.event_bus.subscribe_to_event("project.created", self.handle_project_created)
        await self.event_bus.subscribe_to_event("project.deleted", self.handle_project_deleted)
        await self.event_bus.subscribe_to_event("task.created", self.handle_task_created)
        await self.event_bus.subscribe_to_event("task.updated", self.handle_task_updated)
        await self.event_bus.subscribe_to_event("task.completed", self.handle_task_completed)
        
        logger.info("Event handlers registered")
    
    async def handle_agent_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent created event.
        
        Args:
            event_data: Event data
        """
        agent_id = event_data.get("agent_id")
        logger.info(f"Agent created: {agent_id}")
        
        # Process event
        # ...
    
    async def handle_agent_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent updated event.
        
        Args:
            event_data: Event data
        """
        agent_id = event_data.get("agent_id")
        updated_fields = event_data.get("updated_fields", [])
        logger.info(f"Agent updated: {agent_id}, fields: {updated_fields}")
        
        # Process event
        # ...
    
    async def handle_agent_deleted(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent deleted event.
        
        Args:
            event_data: Event data
        """
        agent_id = event_data.get("agent_id")
        logger.info(f"Agent deleted: {agent_id}")
        
        # Process event
        # ...
    
    async def handle_agent_status_changed(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent status changed event.
        
        Args:
            event_data: Event data
        """
        agent_id = event_data.get("agent_id")
        previous_status = event_data.get("previous_status")
        new_status = event_data.get("new_status")
        reason = event_data.get("reason")
        logger.info(f"Agent status changed: {agent_id}, {previous_status} -> {new_status}, reason: {reason}")
        
        # Process event
        # ...
    
    async def handle_agent_execution_started(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent execution started event.
        
        Args:
            event_data: Event data
        """
        execution_id = event_data.get("execution_id")
        agent_id = event_data.get("agent_id")
        task_id = event_data.get("task_id")
        logger.info(f"Agent execution started: {execution_id}, agent: {agent_id}, task: {task_id}")
        
        # Process event
        # ...
    
    async def handle_agent_execution_completed(self, event_data: Dict[str, Any]) -> None:
        """
        Handle agent execution completed event.
        
        Args:
            event_data: Event data
        """
        execution_id = event_data.get("execution_id")
        agent_id = event_data.get("agent_id")
        task_id = event_data.get("task_id")
        status = event_data.get("status")
        logger.info(f"Agent execution completed: {execution_id}, agent: {agent_id}, task: {task_id}, status: {status}")
        
        # Process event
        # ...
    
    async def handle_template_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle template created event.
        
        Args:
            event_data: Event data
        """
        template_id = event_data.get("template_id")
        logger.info(f"Template created: {template_id}")
        
        # Process event
        # ...
    
    async def handle_template_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle template updated event.
        
        Args:
            event_data: Event data
        """
        template_id = event_data.get("template_id")
        updated_fields = event_data.get("updated_fields", [])
        logger.info(f"Template updated: {template_id}, fields: {updated_fields}")
        
        # Process event
        # ...
    
    async def handle_template_deleted(self, event_data: Dict[str, Any]) -> None:
        """
        Handle template deleted event.
        
        Args:
            event_data: Event data
        """
        template_id = event_data.get("template_id")
        logger.info(f"Template deleted: {template_id}")
        
        # Process event
        # ...
    
    async def handle_communication_sent(self, event_data: Dict[str, Any]) -> None:
        """
        Handle communication sent event.
        
        Args:
            event_data: Event data
        """
        communication_id = event_data.get("communication_id")
        from_agent_id = event_data.get("from_agent_id")
        to_agent_id = event_data.get("to_agent_id")
        logger.info(f"Communication sent: {communication_id}, from: {from_agent_id}, to: {to_agent_id}")
        
        # Process event
        # ...
    
    async def handle_communication_delivered(self, event_data: Dict[str, Any]) -> None:
        """
        Handle communication delivered event.
        
        Args:
            event_data: Event data
        """
        communication_id = event_data.get("communication_id")
        from_agent_id = event_data.get("from_agent_id")
        to_agent_id = event_data.get("to_agent_id")
        logger.info(f"Communication delivered: {communication_id}, from: {from_agent_id}, to: {to_agent_id}")
        
        # Process event
        # ...
    
    async def handle_checkpoint_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle checkpoint created event.
        
        Args:
            event_data: Event data
        """
        checkpoint_id = event_data.get("checkpoint_id")
        agent_id = event_data.get("agent_id")
        sequence_number = event_data.get("sequence_number")
        logger.info(f"Checkpoint created: {checkpoint_id}, agent: {agent_id}, sequence: {sequence_number}")
        
        # Process event
        # ...
    
    async def handle_checkpoint_deleted(self, event_data: Dict[str, Any]) -> None:
        """
        Handle checkpoint deleted event.
        
        Args:
            event_data: Event data
        """
        agent_id = event_data.get("agent_id")
        logger.info(f"Checkpoint deleted: agent: {agent_id}")
        
        # Process event
        # ...
    
    async def handle_project_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle project created event.
        
        Args:
            event_data: Event data
        """
        project_id = event_data.get("project_id")
        logger.info(f"Project created: {project_id}")
        
        # Process event
        # ...
    
    async def handle_project_deleted(self, event_data: Dict[str, Any]) -> None:
        """
        Handle project deleted event.
        
        Args:
            event_data: Event data
        """
        project_id = event_data.get("project_id")
        logger.info(f"Project deleted: {project_id}")
        
        # Process event
        # ...
    
    async def handle_task_created(self, event_data: Dict[str, Any]) -> None:
        """
        Handle task created event.
        
        Args:
            event_data: Event data
        """
        task_id = event_data.get("task_id")
        project_id = event_data.get("project_id")
        from shared.models.src.adapters.planning_to_agent import PlanningToAgentAdapter

        logger.info(f"Task created: {task_id}, project: {project_id}")
        
        # Convert task data to Agent Orchestrator format
        agent_task_data = PlanningToAgentAdapter.task_to_agent(event_data)

        from ..models.internal import AgentExecutionModel
        from shared.models.src.enums import ExecutionState

        # Process the converted task data
        logger.info(f"Transformed task data: {agent_task_data}")

        # Create AgentExecutionModel instance
        agent_id = agent_task_data.get("assigned_agent_id")
        execution_model = AgentExecutionModel(
            agent_id=agent_id,  # The agent will be assigned later
            task_id=agent_task_data.get("task_id"),
            state=ExecutionState.QUEUED,
            parameters=agent_task_data.get("metadata"),
            context={},  # Add any relevant context information here
        )

        # Add to database
        self.db.add(execution_model)
        await self.db.commit()
        await self.db.refresh(execution_model)

        logger.info(f"Created AgentExecutionModel: {execution_model.id}")
        # ...
    
    async def handle_task_updated(self, event_data: Dict[str, Any]) -> None:
        """
        Handle task updated event.
        
        Args:
            event_data: Event data
        """
        task_id = event_data.get("task_id")
        updated_fields = event_data.get("updated_fields", [])
        logger.info(f"Task updated: {task_id}, fields: {updated_fields}")
        
        # Process event
        # ...
    
    async def handle_task_completed(self, event_data: Dict[str, Any]) -> None:
        """
        Handle task completed event.
        
        Args:
            event_data: Event data
        """
        task_id = event_data.get("task_id")
        status = event_data.get("status")
        logger.info(f"Task completed: {task_id}, status: {status}")
        
        # Process event
        # ...


# Event publishing helper functions

async def publish_agent_event(
    event_bus: EventBus,
    event_type: str,
    agent_id: UUID,
    project_id: UUID,
    additional_data: Dict[str, Any] = None,
) -> None:
    """
    Publish an agent event.
    
    Args:
        event_bus: Event bus
        event_type: Event type
        agent_id: Agent ID
        project_id: Project ID
        additional_data: Additional event data
    """
    # Prepare event data
    event_data = {
        "agent_id": str(agent_id),
        "project_id": str(project_id),
    }
    
    # Add additional data
    if additional_data:
        event_data.update(additional_data)
    
    # Publish event
    await event_bus.publish_event(event_type, event_data)
    logger.debug(f"Published event: {event_type}, agent_id: {agent_id}")
