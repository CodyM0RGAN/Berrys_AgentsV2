"""
Adapter for converting between Planning System and Agent Orchestrator models.

This module provides adapters for converting entities between the Planning System
and Agent Orchestrator service representations.
"""

import logging
from typing import Any, Dict, Optional, Union, cast
from uuid import UUID
from enum import Enum

from pydantic import BaseModel

from shared.models.src.adapters.base import ServiceBoundaryAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import TaskStatus, TaskPriority

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


class PlanningToAgentAdapter:
    """
    Adapter for converting between Planning System and Agent Orchestrator models.
    
    This adapter handles the conversion of entities between the Planning System
    and Agent Orchestrator service representations.
    """
    
    @classmethod
    def task_to_agent(
        cls, 
        planning_task: Union[Dict[str, Any], BaseModel, None]
    ) -> Dict[str, Any]:
        """
        Convert a Planning System task to an Agent Orchestrator task.
        
        Args:
            planning_task: The Planning System task to convert
            
        Returns:
            The converted Agent Orchestrator task
            
        Raises:
            AdapterValidationError: If validation fails
            EntityConversionError: If conversion fails
        """
        try:
            # Handle None input
            if planning_task is None:
                raise AdapterValidationError(
                    "Source data cannot be None",
                    source_data=None
                )
            
            # Convert to dictionary if it's a model
            if isinstance(planning_task, BaseModel):
                data = planning_task.dict()
            elif isinstance(planning_task, dict):
                data = planning_task
            else:
                raise AdapterValidationError(
                    "Source data must be a dictionary or Pydantic model",
                    source_data=planning_task
                )
            
            # Create a new dictionary for the result
            result = {}
            
            # Handle field name changes
            if "id" in data:
                result["task_id"] = data["id"]
            if "plan_id" in data:
                result["project_id"] = data["plan_id"] # Assuming plan_id in PlanningSystem corresponds to project_id in AgentOrchestrator
            if "assigned_to" in data:
                result["assigned_agent_id"] = data["assigned_to"]
            
            # Copy common fields
            for field in ["name", "description"]:
                if field in data:
                    result[field] = data[field]
            
            # Handle status conversion (String to Enum)
            if "status" in data:
                result["status"] = normalize_enum_value(data["status"], uppercase=True)
            
            # Handle priority conversion (Enum to Integer)
            if "priority" in data:
                if isinstance(data["priority"], int):
                    result["priority"] = data["priority"]
                else:
                    result["priority"] = normalize_enum_value(data["priority"], uppercase=True)
            
            # Handle metadata field (task_metadata → metadata)
            if "task_metadata" in data:
                result["metadata"] = data["task_metadata"]
            elif "metadata" in data:
                result["metadata"] = data["metadata"]
            else:
                result["metadata"] = {}
            
            # Log the transformation
            logger.debug(
                f"Transformed Planning System task to Agent Orchestrator: "
                f"ID: {data.get('id')} → task_id: {result.get('task_id')}"
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, (AdapterValidationError, EntityConversionError)):
                raise
            
            raise EntityConversionError(
                f"Failed to convert Planning System task to Agent Orchestrator: {str(e)}",
                source_entity=planning_task,
                error_details={"error": str(e)}
            )
