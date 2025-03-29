"""
Pydantic API Model Enum Standardization Template

This template demonstrates how to update Pydantic API models to use standardized enum handling.
It shows the before and after versions of model classes to illustrate the changes needed.

Key changes:
1. Replace local enum definitions with imports from shared/models/src/enums.py
2. Ensure enum values are UPPERCASE
3. Use enum classes directly as field types
4. Update validation logic to handle enum instances and string values

Usage:
1. Use this as a reference when updating your service's API models
2. Adapt the patterns to your specific model structure
3. Ensure all enum fields are properly validated
"""

# ----------------------------------------------------------------------------------
# BEFORE: Original API models with local enum definitions
# ----------------------------------------------------------------------------------

# Original imports
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator

# Local enum definitions (problematic)
class AgentState(str, Enum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"

class AgentType(str, Enum):
    COORDINATOR = "COORDINATOR"
    ASSISTANT = "ASSISTANT"
    RESEARCHER = "RESEARCHER"
    DEVELOPER = "DEVELOPER"
    DESIGNER = "DESIGNER"
    SPECIALIST = "SPECIALIST"
    AUDITOR = "AUDITOR"
    CUSTOM = "CUSTOM"

# Original API models
class AgentBase(BaseModel):
    """
    Base model for Agent with common attributes.
    """
    name: str
    type: AgentType
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None

class AgentCreate(AgentBase):
    """
    Model for creating a new Agent.
    """
    project_id: UUID

class AgentUpdate(BaseModel):
    """
    Model for updating an existing Agent.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None

class AgentResponse(AgentBase):
    """
    Model for Agent response.
    """
    id: UUID
    project_id: UUID
    state: AgentState
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None


# ----------------------------------------------------------------------------------
# AFTER: Updated API models with standardized enum handling
# ----------------------------------------------------------------------------------

# Updated imports
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator

# Import shared enums instead of local definitions
from shared.models.src.enums import AgentType, AgentStatus

# Updated API models
class AgentBase(BaseModel):
    """
    Base model for Agent with common attributes.
    """
    name: str
    type: AgentType  # Using shared enum directly
    description: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_template: Optional[str] = None
    
    # Optional: Add validator for backward compatibility with string values
    @validator('type', pre=True)
    def validate_type(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in AgentType:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v

class AgentCreate(AgentBase):
    """
    Model for creating a new Agent.
    """
    project_id: UUID

class AgentUpdate(BaseModel):
    """
    Model for updating an existing Agent.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None

class AgentResponse(AgentBase):
    """
    Model for Agent response.
    """
    id: UUID
    project_id: UUID
    status: AgentStatus  # Using shared enum directly, renamed from 'state' to match shared model
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime] = None
    
    # Optional: Add validator for backward compatibility with string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in AgentStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
    
    class Config:
        # Allow conversion from ORM models
        from_attributes = True


# ----------------------------------------------------------------------------------
# Example Usage
# ----------------------------------------------------------------------------------

def example_usage():
    """Example of how to use the updated API models."""
    
    # Create a new agent with enum instances
    agent_create = AgentCreate(
        name="Research Assistant",
        type=AgentType.RESEARCHER,
        project_id=UUID("123e4567-e89b-12d3-a456-426614174000")
    )
    
    # Create a new agent with string values (will be validated and converted)
    agent_create2 = AgentCreate(
        name="Code Generator",
        type="DEVELOPER",  # Will be converted to enum instance
        project_id=UUID("123e4567-e89b-12d3-a456-426614174000")
    )
    
    # This would raise a validation error because "invalid" is not a valid type
    try:
        agent_create3 = AgentCreate(
            name="Invalid Agent",
            type="invalid",
            project_id=UUID("123e4567-e89b-12d3-a456-426614174000")
        )
    except ValueError as e:
        print(f"Validation error: {e}")
    
    # Create a response model
    agent_response = AgentResponse(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        name="Research Assistant",
        type=AgentType.RESEARCHER,
        project_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        status=AgentStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Convert to dictionary (for API response)
    response_dict = agent_response.model_dump()
    print(f"Response dict: {response_dict}")
    # Note: Enum values will be serialized as strings in the response
