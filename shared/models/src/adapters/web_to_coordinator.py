"""
Adapter for converting between Web Dashboard and Project Coordinator models.

This module provides adapters for converting entities between the Web Dashboard
and Project Coordinator service representations.
"""

import logging
from typing import Any, Dict, Optional, Union, cast
from uuid import UUID
from enum import Enum

from pydantic import BaseModel

from shared.models.src.adapters.base import ServiceBoundaryAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import AgentStatus, TaskStatus, TaskPriority
from shared.models.src.project import Project as ProjectPydantic, ProjectStatus
from shared.models.src.agent import Agent as AgentPydantic
from shared.models.src.task import Task as TaskPydantic

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


class WebToCoordinatorAdapter:
    """
    Adapter for converting between Web Dashboard and Project Coordinator models.
    
    This adapter handles the conversion of entities between the Web Dashboard
    and Project Coordinator service representations. The main differences are
    in the handling of status fields (String vs Enum) and metadata fields.
    """
    
    @classmethod
    def project_to_coordinator(
        cls, 
        web_project: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert a Web Dashboard project to a Project Coordinator project.
        
        Args:
            web_project: The Web Dashboard project to convert
            
        Returns:
            The converted Project Coordinator project
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if web_project is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(web_project, BaseModel):
                data = web_project.dict()
            elif isinstance(web_project, dict):
                data = web_project
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_project
                )
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_project
                )
            
            # Handle metadata field (project_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "project_metadata" not in data:
                data["project_metadata"] = data.pop("metadata")
            elif "project_metadata" not in data:
                data["project_metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Web Dashboard project to Project Coordinator: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Web Dashboard project to Project Coordinator: {str(e)}",
                source_entity=web_project,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def project_from_coordinator(
        cls, 
        coordinator_project: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator project to a Web Dashboard project.
        
        Args:
            coordinator_project: The Project Coordinator project to convert
            
        Returns:
            The converted Web Dashboard project
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(coordinator_project, BaseModel):
                data = coordinator_project.dict()
            else:
                data = dict(coordinator_project)
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_project
                )
            
            # Handle status conversion (Enum to String)
            if "status" in data:
                try:
                    data["status"] = normalize_enum_value(data["status"], uppercase=True)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid project status: {data.get('status')} - {str(e)}")
                    # Default to DRAFT if invalid
                    data["status"] = ProjectStatus.DRAFT.value
            
            # Handle metadata field (project_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "project_metadata" not in data:
                data["project_metadata"] = data.pop("metadata")
            elif "project_metadata" in data and "metadata" not in data:
                data["metadata"] = data["project_metadata"]
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator project to Web Dashboard: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator project to Web Dashboard: {str(e)}",
                source_entity=coordinator_project,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def project_create_request_to_coordinator(
        cls,
        web_request: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Web Dashboard project create request to a Project Coordinator request.
        
        Args:
            web_request: The Web Dashboard project create request to convert
            
        Returns:
            The converted Project Coordinator request
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(web_request, BaseModel):
                data = web_request.dict()
            elif isinstance(web_request, dict):
                data = web_request
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_request
                )
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_request
                )
            
            # Remove status field if present
            if "status" in data:
                data.pop("status")
            
            # Log the transformation
            logger.debug(
                f"Transformed Web Dashboard project create request to Project Coordinator"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Web Dashboard project create request to Project Coordinator: {str(e)}",
                source_entity=web_request,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def agent_to_coordinator(
        cls, 
        web_agent: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Web Dashboard agent to a Project Coordinator agent.
        
        Args:
            web_agent: The Web Dashboard agent to convert
            
        Returns:
            The converted Project Coordinator agent
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(web_agent, BaseModel):
                data = web_agent.dict()
            else:
                data = dict(web_agent)
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_agent
                )
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    status_value = normalize_enum_value(data["status"], uppercase=True)
                    data["status"] = AgentStatus(status_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid agent status: {data.get('status')} - {str(e)}")
                    # Default to ACTIVE if invalid
                    data["status"] = AgentStatus.ACTIVE
            
            # Handle type field normalization
            if "type" in data:
                data["type"] = normalize_enum_value(data["type"], uppercase=True)
            
            # Handle metadata field (agent_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "agent_metadata" not in data:
                data["agent_metadata"] = data.pop("metadata")
            elif "agent_metadata" not in data:
                data["agent_metadata"] = {}
            
            # Handle configuration field if present
            if "configuration" in data and "agent_metadata" not in data:
                data["agent_metadata"] = data.pop("configuration")
            
            # Log the transformation
            logger.debug(
                f"Transformed Web Dashboard agent to Project Coordinator: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Web Dashboard agent to Project Coordinator: {str(e)}",
                source_entity=web_agent,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def agent_from_coordinator(
        cls, 
        coordinator_agent: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator agent to a Web Dashboard agent.
        
        Args:
            coordinator_agent: The Project Coordinator agent to convert
            
        Returns:
            The converted Web Dashboard agent
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(coordinator_agent, BaseModel):
                data = coordinator_agent.dict()
            else:
                data = dict(coordinator_agent)
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_agent
                )
            
            # Handle status conversion (Enum to String)
            if "status" in data:
                try:
                    data["status"] = normalize_enum_value(data["status"], uppercase=True)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid agent status: {data.get('status')} - {str(e)}")
                    # Default to ACTIVE if invalid
                    data["status"] = AgentStatus.ACTIVE.value
            
            # Handle metadata field (agent_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "agent_metadata" not in data:
                data["agent_metadata"] = data.pop("metadata")
            elif "agent_metadata" in data and "metadata" not in data:
                data["metadata"] = data["agent_metadata"]
            
            # Handle configuration field if needed
            if "agent_metadata" in data and "configuration" not in data:
                data["configuration"] = data["agent_metadata"]
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator agent to Web Dashboard: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator agent to Web Dashboard: {str(e)}",
                source_entity=coordinator_agent,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def task_to_coordinator(
        cls, 
        web_task: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Web Dashboard task to a Project Coordinator task.
        
        Args:
            web_task: The Web Dashboard task to convert
            
        Returns:
            The converted Project Coordinator task
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(web_task, BaseModel):
                data = web_task.dict()
            else:
                data = dict(web_task)
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=web_task
                )
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    status_value = normalize_enum_value(data["status"], uppercase=True)
                    data["status"] = TaskStatus(status_value)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task status: {data.get('status')} - {str(e)}")
                    # Default to PENDING if invalid
                    data["status"] = TaskStatus.PENDING
            
            # Handle priority conversion (Integer to Enum)
            if "priority" in data:
                try:
                    if isinstance(data["priority"], int):
                        # Convert integer directly to enum
                        data["priority"] = TaskPriority(data["priority"])
                    else:
                        # Try to normalize and convert to enum
                        priority_str = normalize_enum_value(data["priority"], uppercase=True)
                        data["priority"] = TaskPriority(int(priority_str))
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task priority: {data.get('priority')} - {str(e)}")
                    # Default to MEDIUM if invalid
                    data["priority"] = TaskPriority.MEDIUM
            
            # Handle field name differences
            if "assigned_to" in data and "agent_id" not in data:
                data["agent_id"] = data.pop("assigned_to")
            
            # Handle metadata field (task_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "task_metadata" not in data:
                data["task_metadata"] = data.pop("metadata")
            elif "task_metadata" not in data:
                data["task_metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Web Dashboard task to Project Coordinator: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Web Dashboard task to Project Coordinator: {str(e)}",
                source_entity=web_task,
                error_details={"error": str(e)}
            )
    
    @classmethod
    def task_from_coordinator(
        cls, 
        coordinator_task: Union[Dict[str, Any], BaseModel]
    ) -> Dict[str, Any]:
        """
        Convert a Project Coordinator task to a Web Dashboard task.
        
        Args:
            coordinator_task: The Project Coordinator task to convert
            
        Returns:
            The converted Web Dashboard task
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Convert to dictionary if it's a model
            if isinstance(coordinator_task, BaseModel):
                data = coordinator_task.dict()
            else:
                data = dict(coordinator_task)
            
            # Validate the source data
            if not isinstance(data, dict):
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=coordinator_task
                )
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                try:
                    data["status"] = normalize_enum_value(data["status"], uppercase=True)
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task status: {data.get('status')} - {str(e)}")
                    # Default to PENDING if invalid
                    data["status"] = TaskStatus.PENDING.value
            
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
                        data["priority"] = priority_map.get(data["priority"], 3)
                    elif isinstance(data["priority"], int):
                        # Keep as is, it's already an integer
                        pass
                    else:
                        # Try to normalize and convert to TaskPriority enum
                        priority_str = normalize_enum_value(data["priority"], uppercase=True)
                        try:
                            priority_enum = TaskPriority(priority_str.lower())
                            data["priority"] = priority_map.get(priority_enum, 3)
                        except ValueError:
                            # If conversion fails, default to MEDIUM
                            data["priority"] = 3
                except (ValueError, AdapterValidationError) as e:
                    logger.warning(f"Invalid task priority: {data.get('priority')} - {str(e)}")
                    # Default to MEDIUM if invalid
                    data["priority"] = 3
            
            # Handle field name differences
            if "agent_id" in data and "assigned_to" not in data:
                data["assigned_to"] = data.pop("agent_id")
            
            # Handle metadata field (task_metadata in both services)
            # No conversion needed, but ensure it exists
            if "metadata" in data and "task_metadata" not in data:
                data["task_metadata"] = data.pop("metadata")
            elif "task_metadata" in data and "metadata" not in data:
                data["metadata"] = data["task_metadata"]
            
            # Log the transformation
            logger.debug(
                f"Transformed Project Coordinator task to Web Dashboard: "
                f"ID: {data.get('id')}"
            )
            
            return data
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Project Coordinator task to Web Dashboard: {str(e)}",
                source_entity=coordinator_task,
                error_details={"error": str(e)}
            )
