"""
SQLAlchemy Model Enum Standardization Template

This template demonstrates how to update SQLAlchemy models to use standardized enum handling.
It shows the before and after versions of a model class to illustrate the changes needed.

Key changes:
1. Replace direct Enum() usage with String columns
2. Import shared enums from shared/models/src/enums.py
3. Add validation using EnumColumnMixin or enum_column()
4. Use UPPERCASE enum values consistently

Usage:
1. Use this as a reference when updating your service's models
2. Adapt the patterns to your specific model structure
3. Ensure all enum columns are properly validated
"""

# ----------------------------------------------------------------------------------
# BEFORE: Original model with direct Enum() usage
# ----------------------------------------------------------------------------------

# Original imports
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

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

# Original model class
class AgentModel:
    """
    SQLAlchemy model for agents.
    """
    __tablename__ = "agents"  # Plural table name (problematic)
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    
    # Direct Enum usage (problematic)
    type = Column(SQLAlchemyEnum(AgentType), nullable=False)
    state = Column(SQLAlchemyEnum(AgentState), nullable=False, default=AgentState.CREATED)
    
    # Other columns...
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type}', state='{self.state}')>"


# ----------------------------------------------------------------------------------
# AFTER: Updated model with standardized enum handling
# ----------------------------------------------------------------------------------

# Updated imports
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

# Import shared enums instead of local definitions
from shared.models.src.enums import AgentType, AgentStatus
from shared.utils.src.enum_validation import EnumColumnMixin, enum_column

# Updated model class
class AgentModel(EnumColumnMixin):
    """
    SQLAlchemy model for agents.
    """
    __tablename__ = "agent"  # Singular table name (standardized)
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    
    # String columns with enum validation (standardized)
    # Option 1: Using EnumColumnMixin
    type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=AgentStatus.CREATED.value)
    
    # Option 2: Using enum_column function (alternative approach)
    # type = enum_column(AgentType, nullable=False)
    # status = enum_column(AgentStatus, nullable=False, default=AgentStatus.CREATED.value)
    
    # Other columns...
    
    # Define enum columns for validation
    __enum_columns__ = {
        'type': AgentType,
        'status': AgentStatus
    }
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"


# ----------------------------------------------------------------------------------
# Example Usage
# ----------------------------------------------------------------------------------

def example_usage():
    """Example of how to use the updated model."""
    
    # Create a new agent with enum instances
    agent1 = AgentModel(
        name="Research Assistant",
        type=AgentType.RESEARCHER,
        status=AgentStatus.CREATED
    )
    
    # Create a new agent with string values (will be validated)
    agent2 = AgentModel(
        name="Code Generator",
        type="DEVELOPER",
        status="READY"
    )
    
    # This would raise a validation error because "invalid" is not a valid status
    try:
        agent3 = AgentModel(
            name="Invalid Agent",
            type=AgentType.CUSTOM,
            status="invalid"
        )
    except ValueError as e:
        print(f"Validation error: {e}")
    
    # During the transition period, lowercase values will be converted to uppercase
    # but will generate a deprecation warning
    import warnings
    with warnings.catch_warnings(record=True) as w:
        agent4 = AgentModel(
            name="Legacy Agent",
            type="developer",  # Will be converted to "DEVELOPER" with warning
            status=AgentStatus.ACTIVE
        )
        if w:
            print(f"Got deprecation warning: {w[0].message}")
