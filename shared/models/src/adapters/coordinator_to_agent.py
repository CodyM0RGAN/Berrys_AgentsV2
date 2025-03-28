"""
Adapter for converting between Project Coordinator and Agent Orchestrator models.

This module provides adapters for converting entities between the Project Coordinator
and Agent Orchestrator service representations.
"""

import logging
from typing import Any, Dict, Optional, Union, cast
from uuid import UUID
from enum import Enum

from pydantic import BaseModel

from shared.models.src.adapters.base import ServiceBoundaryAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import ProjectStatus, AgentStatus, TaskStatus, TaskPriority, AgentType

logger = logging.getLogger(__name__)

def normalize_enum_value(value: Any, uppercase: bool = True) -> str:
    """
    Normalize an enum value to a string.
    
    This function handles various input types:
    - If the input is an Enum, returns its value
    - If the input is a string that looks like an enum (e.g., "AgentType.DEVELOPER"),
      extracts and returns just the value part
    - Otherwise, returns the string representation
    
    Args:
        value: The value to normalize
        uppercase: Whether to convert the result to uppercase
        
    Returns:
        The normalized string value
    """
    if value is None:
        raise AdapterValidationError("Cannot normalize None value")
    
    if isinstance(value, Enum):
        result = value.value
    else:
        value_str = str(value)
        
        # Check if the string looks like an enum (e.g., "AgentType.DEVELOPER")
        if "." in value_str and not value_str.startswith("."):
            # Extract the part after the dot
            result = value_str.split(".", 1)[1]
        else:
            result = value_str
    
    return result.upper() if uppercase else result


class CoordinatorToAgentAdapter:
    """
    Adapter for converting between Project Coordinator and Agent Orchestrator models.
    
    This adapter handles the conversion of entities between the Project Coordinator
    and Agent Orchestrator service representations. The main differences are in
    field names (e.g., id → project_id, owner_id → created_by), type conversions
    (Enum → String for status fields), and metadata field names.
    """
    
    @classmethod
    def project_to_agent(
        cls, 
        coordinator_project: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator project to an Agent Orchestrator project.
        
        Args:
            coordinator_project: The Project Coordinator project to convert
            
        Returns:
            The converted Agent Orchestrator project
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if coordinator_project is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(coordinator_project, BaseModel):
                data = coordinator_project.dict()
            elif isinstance(coordinator_project, dict):
                data = coordinator_project
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_project
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Handle field name changes
            if "id" in data:
                result["project_id"] = data["id"]
            
            if "owner_id" in data:
                result["created_by"] = data["owner_id"]
            
            # Copy common fields
            for field in ["name", "description"]:
                if field in data:
                    result[field] = data[field]
            
            # Handle status conversion (Enum to String)
            if "status" in data:
                result["status"] = normalize_enum_value(data["status"], uppercase=True)
            
            # Handle metadata field (project_metadata → metadata)
            if "project_metadata" in data:
                result["metadata"] = data["project_metadata"]
            elif "metadata" in data:
                result["metadata"] = data["metadata"]
            else:
                result["metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator project to Agent Orchestrator: "
                f"ID: {data.get('id')} → project_id: {result.get('project_id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator project to Agent Orchestrator: {str(e)}",
                source_entity=coordinator_project,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def project_from_agent(
        cls, 
        agent_project: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert an Agent Orchestrator project to a Project Coordinator project.
        
        Args:
            agent_project: The Agent Orchestrator project to convert
            
        Returns:
            The converted Project Coordinator project
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if agent_project is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(agent_project, BaseModel):
                data = agent_project.dict()
            elif isinstance(agent_project, dict):
                data = agent_project
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=agent_project
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Handle field name changes
            if "project_id" in data:
                result["id"] = data["project_id"]
            
            if "created_by" in data:
                result["owner_id"] = data["created_by"]
            elif "owner_id" in data:
                # Preserve owner_id if it exists
                result["owner_id"] = data["owner_id"]
            
            # Copy common fields
            for field in ["name", "description"]:
                if field in data:
                    result[field] = data[field]
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    status_value = normalize_enum_value(data["status"], uppercase=True)
                    result["status"] = ProjectStatus(status_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid project status: {data.get('status')} - {str(e)}")
                    # Default to DRAFT if invalid
                    result["status"] = ProjectStatus.DRAFT
            
            # Handle metadata field (metadata → project_metadata)
            if "metadata" in data:
                result["project_metadata"] = data["metadata"]
            elif "project_metadata" in data:
                result["project_metadata"] = data["project_metadata"]
            else:
                result["project_metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Agent Orchestrator project to Project Coordinator: "
                f"project_id: {data.get('project_id')} → ID: {result.get('id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Agent Orchestrator project to Project Coordinator: {str(e)}",
                source_entity=agent_project,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def agent_to_agent_orchestrator(
        cls, 
        coordinator_agent: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator agent to an Agent Orchestrator agent.
        
        Args:
            coordinator_agent: The Project Coordinator agent to convert
            
        Returns:
            The converted Agent Orchestrator agent
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if coordinator_agent is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(coordinator_agent, BaseModel):
                data = coordinator_agent.dict()
            elif isinstance(coordinator_agent, dict):
                data = coordinator_agent
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_agent
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Copy ID and project_id fields
            for field in ["id", "project_id"]:
                if field in data:
                    result[field] = data[field]
            
            # Copy name field
            if "name" in data:
                result["name"] = data["name"]
            
            # Handle type field (type → agent_type)
            if "type" in data:
                try:
                    type_value = normalize_enum_value(data["type"], uppercase=True)
                    # Check if the type is "DEVELOPER" specifically
                    if type_value == "DEVELOPER":
                        result["agent_type"] = AgentType.DEVELOPER
                    else:
                        # Try to convert to enum
                        result["agent_type"] = AgentType(type_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid agent type: {data.get('type')} - {str(e)}")
                    # Default to CUSTOM if invalid
                    result["agent_type"] = AgentType.CUSTOM
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    status_value = normalize_enum_value(data["status"], uppercase=True)
                    result["status"] = AgentStatus(status_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid agent status: {data.get('status')} - {str(e)}")
                    # Default to ACTIVE if invalid
                    result["status"] = AgentStatus.ACTIVE
            
            # Handle metadata field (agent_metadata → config)
            if "agent_metadata" in data:
                result["config"] = data["agent_metadata"]
            elif "config" in data:
                result["config"] = data["config"]
            elif "configuration" in data:
                result["config"] = data["configuration"]
            else:
                result["config"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator agent to Agent Orchestrator: "
                f"ID: {data.get('id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator agent to Agent Orchestrator: {str(e)}",
                source_entity=coordinator_agent,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def agent_from_agent_orchestrator(
        cls, 
        agent_orchestrator_agent: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert an Agent Orchestrator agent to a Project Coordinator agent.
        
        Args:
            agent_orchestrator_agent: The Agent Orchestrator agent to convert
            
        Returns:
            The converted Project Coordinator agent
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if agent_orchestrator_agent is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(agent_orchestrator_agent, BaseModel):
                data = agent_orchestrator_agent.dict()
            elif isinstance(agent_orchestrator_agent, dict):
                data = agent_orchestrator_agent
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=agent_orchestrator_agent
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Copy ID and project_id fields
            for field in ["id", "project_id"]:
                if field in data:
                    result[field] = data[field]
            
            # Copy name field
            if "name" in data:
                result["name"] = data["name"]
            
            # Handle type field (agent_type → type)
            if "agent_type" in data:
                result["type"] = normalize_enum_value(data["agent_type"], uppercase=True)
            elif "type" in data and "agent_type" not in data:
                result["type"] = normalize_enum_value(data["type"], uppercase=True)
            
            # Handle status conversion (Enum to String)
            if "status" in data:
                result["status"] = normalize_enum_value(data["status"], uppercase=True)
            
            # Handle metadata field (config → agent_metadata)
            if "config" in data:
                result["agent_metadata"] = data["config"]
            elif "agent_metadata" in data:
                result["agent_metadata"] = data["agent_metadata"]
            else:
                result["agent_metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Agent Orchestrator agent to Project Coordinator: "
                f"ID: {data.get('id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Agent Orchestrator agent to Project Coordinator: {str(e)}",
                source_entity=agent_orchestrator_agent,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def task_to_agent(
        cls, 
        coordinator_task: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator task to an Agent Orchestrator task.
        
        Args:
            coordinator_task: The Project Coordinator task to convert
            
        Returns:
            The converted Agent Orchestrator task
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if coordinator_task is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(coordinator_task, BaseModel):
                data = coordinator_task.dict()
            elif isinstance(coordinator_task, dict):
                data = coordinator_task
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_task
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Handle field name changes
            if "id" in data:
                result["task_id"] = data["id"]
            
            if "agent_id" in data:
                result["assigned_agent_id"] = data["agent_id"]
            
            # Copy common fields
            for field in ["name", "description", "project_id"]:
                if field in data:
                    result[field] = data[field]
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    status_value = normalize_enum_value(data["status"], uppercase=True)
                    result["status"] = TaskStatus(status_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task status: {data.get('status')} - {str(e)}")
                    # Default to PENDING if invalid
                    result["status"] = TaskStatus.PENDING
            
            # Handle priority conversion (Integer to Enum)
            if "priority" in data:
                try:
                    # Convert integer to string first if needed
                    if isinstance(data["priority"], int):
                        priority_str = str(data["priority"])
                    else:
                        priority_str = normalize_enum_value(data["priority"], uppercase=True)
                    
                    # Try to convert to enum
                    result["priority"] = TaskPriority(int(priority_str))
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task priority: {data.get('priority')} - {str(e)}")
                    # Default to MEDIUM if invalid
                    result["priority"] = TaskPriority.MEDIUM
            
            # Handle metadata field (task_metadata → metadata)
            if "task_metadata" in data:
                result["metadata"] = data["task_metadata"]
            elif "metadata" in data:
                result["metadata"] = data["metadata"]
            else:
                result["metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator task to Agent Orchestrator: "
                f"ID: {data.get('id')} → task_id: {result.get('task_id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator task to Agent Orchestrator: {str(e)}",
                source_entity=coordinator_task,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def task_from_agent(
        cls, 
        agent_task: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert an Agent Orchestrator task to a Project Coordinator task.
        
        Args:
            agent_task: The Agent Orchestrator task to convert
            
        Returns:
            The converted Project Coordinator task
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if agent_task is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(agent_task, BaseModel):
                data = agent_task.dict()
            elif isinstance(agent_task, dict):
                data = agent_task
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=agent_task
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Handle field name changes
            if "task_id" in data:
                result["id"] = data["task_id"]
            
            if "assigned_agent_id" in data:
                result["agent_id"] = data["assigned_agent_id"]
            
            # Copy common fields
            for field in ["name", "description", "project_id"]:
                if field in data:
                    result[field] = data[field]
            
            # Handle status conversion (Enum to String)
            if "status" in data:
                result["status"] = normalize_enum_value(data["status"], uppercase=True)
            
            # Handle priority conversion (Enum to Integer)
            if "priority" in data:
                try:
                    # Map TaskPriority enum values to integers
                    priority_map = {
                        TaskPriority.LOW: 1,
                        TaskPriority.MEDIUM: 3,
                        TaskPriority.HIGH: 5,
                        TaskPriority.CRITICAL: 7
                    }
                    
                    if isinstance(data["priority"], TaskPriority):
                        result["priority"] = priority_map.get(data["priority"], 3)
                    elif isinstance(data["priority"], int):
                        # Keep as is, it's already an integer
                        result["priority"] = data["priority"]
                    else:
                        # Try to normalize and convert to TaskPriority enum
                        priority_str = normalize_enum_value(data["priority"], uppercase=True)
                        try:
                            priority_enum = TaskPriority(priority_str.lower())
                            result["priority"] = priority_map.get(priority_enum, 3)
                        except ValueError:
                            # If conversion fails, default to MEDIUM
                            result["priority"] = 3
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task priority: {data.get('priority')} - {str(e)}")
                    # Default to MEDIUM if invalid
                    result["priority"] = 3
            
            # Handle metadata field (metadata → task_metadata)
            if "metadata" in data:
                result["task_metadata"] = data["metadata"]
            elif "task_metadata" in data:
                result["task_metadata"] = data["task_metadata"]
            else:
                result["task_metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Agent Orchestrator task to Project Coordinator: "
                f"task_id: {data.get('task_id')} → ID: {result.get('id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Agent Orchestrator task to Project Coordinator: {str(e)}",
                source_entity=agent_task,
                error_details={"error": str(e)}
            )
