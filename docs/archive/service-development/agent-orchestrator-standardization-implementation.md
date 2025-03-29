# Agent Orchestrator Standardization Implementation

This document outlines the detailed implementation plan and execution for standardizing the Agent Orchestrator service according to our service standardization guidelines.

## Implementation Plan

### Current State Analysis

#### API Models (`api.py`)

The Agent Orchestrator service initially defined the following local enums:

1. **AgentState**:
   ```python
   class AgentState(str, Enum):
       CREATED = "CREATED"
       INITIALIZING = "INITIALIZING"
       READY = "READY"
       ACTIVE = "ACTIVE"
       PAUSED = "PAUSED"
       ERROR = "ERROR"
       TERMINATED = "TERMINATED"
   ```

2. **ExecutionState**:
   ```python
   class ExecutionState(str, Enum):
       QUEUED = "QUEUED"
       PREPARING = "PREPARING"
       RUNNING = "RUNNING"
       PAUSED = "PAUSED"
       COMPLETED = "COMPLETED"
       FAILED = "FAILED"
       CANCELLED = "CANCELLED"
   ```

3. **AgentType**:
   ```python
   class AgentType(str, Enum):
       RESEARCHER = "RESEARCHER"
       PLANNER = "PLANNER"
       DEVELOPER = "DEVELOPER"
       REVIEWER = "REVIEWER"
       MANAGER = "MANAGER"
       SPECIALIST = "SPECIALIST"
       TOOL_CURATOR = "TOOL_CURATOR"
       DEPLOYMENT = "DEPLOYMENT"
       AUDITOR = "AUDITOR"
       CUSTOM = "CUSTOM"
   ```

#### Internal Models (`internal.py`)

The internal models used these enums directly with SQLAlchemy's `Enum()` type:

```python
class AgentModel(Base):
    __tablename__ = "agents"  # Plural table name
    
    # ...
    type = Column(Enum(AgentType), nullable=False)
    state = Column(Enum(AgentState), nullable=False, default=AgentState.CREATED)
    # ...
```

#### Shared Enums (`shared/models/src/enums.py`)

The shared enums module defines standardized enums that should be used across all services:

1. **AgentStatus** (equivalent to AgentState):
   ```python
   class AgentStatus(str, Enum):
       INACTIVE = "INACTIVE"
       ACTIVE = "ACTIVE"
       BUSY = "BUSY"
       ERROR = "ERROR"
       MAINTENANCE = "MAINTENANCE"
   ```

2. **AgentType**:
   ```python
   class AgentType(str, Enum):
       COORDINATOR = "COORDINATOR"
       ASSISTANT = "ASSISTANT"
       RESEARCHER = "RESEARCHER"
       DEVELOPER = "DEVELOPER"
       DESIGNER = "DESIGNER"
       SPECIALIST = "SPECIALIST"
       AUDITOR = "AUDITOR"
       CUSTOM = "CUSTOM"
   ```

### Enum Mapping

We mapped the local enums to the shared enums as follows:

#### AgentState → AgentStatus

| Local (AgentState) | Shared (AgentStatus) | Notes |
|--------------------|----------------------|-------|
| CREATED | INACTIVE | Initial state |
| INITIALIZING | INACTIVE | With additional state tracking |
| READY | INACTIVE | Ready but not active |
| ACTIVE | ACTIVE | Direct mapping |
| PAUSED | INACTIVE | With additional state tracking |
| ERROR | ERROR | Direct mapping |
| TERMINATED | INACTIVE | Terminal state |

Since the shared `AgentStatus` enum doesn't have direct equivalents for all local states, we:
1. Used the closest match from `AgentStatus`
2. Added a new column `state_detail` to track the more detailed state when needed

#### AgentType

| Local (AgentType) | Shared (AgentType) | Notes |
|-------------------|-------------------|-------|
| RESEARCHER | RESEARCHER | Direct mapping |
| PLANNER | COORDINATOR | Best match |
| DEVELOPER | DEVELOPER | Direct mapping |
| REVIEWER | AUDITOR | Best match |
| MANAGER | COORDINATOR | Best match |
| SPECIALIST | SPECIALIST | Direct mapping |
| TOOL_CURATOR | SPECIALIST | Best match |
| DEPLOYMENT | SPECIALIST | Best match |
| AUDITOR | AUDITOR | Direct mapping |
| CUSTOM | CUSTOM | Direct mapping |

#### ExecutionState

There's no direct equivalent in the shared enums, so we kept `ExecutionState` as a local enum but moved it to a new file `services/agent-orchestrator/src/models/enums.py` for service-specific enums.

## Implementation Overview

The Agent Orchestrator service has been standardized to follow the project-wide conventions for model representation, enum usage, and database schema. The following changes have been implemented:

1. Created service-specific enums in a dedicated `enums.py` file
2. Updated API models to use shared enums and add state_detail
3. Updated internal models to use string columns with validation and singular table names
4. Set up Alembic migration infrastructure
5. Created a migration script to create the missing tables and add state_detail column to the agent table
6. Added tests to verify enum validation works correctly

## Enum Standardization

### Service-Specific Enums

Service-specific enums have been defined in `src/models/enums.py`:

```python
from enum import Enum

class AgentStateDetail(str, Enum):
    """Detailed state of an agent."""
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"

class ExecutionState(str, Enum):
    """State of an agent execution."""
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
```

### Shared Enums

Shared enums from `shared.models.src.enums` are used where appropriate:

```python
from shared.models.src.enums import AgentStatus, AgentType
```

## Model Standardization

### API Models

API models have been updated to use shared enums and add state_detail:

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from shared.models.src.enums import AgentStatus, AgentType
from src.models.enums import AgentStateDetail, ExecutionState

class AgentBase(BaseModel):
    """Base model for agent data."""
    name: str
    description: Optional[str] = None
    type: AgentType
    project_id: UUID
    template_id: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None

class AgentCreate(AgentBase):
    """Model for creating a new agent."""
    pass

class AgentUpdate(BaseModel):
    """Model for updating an agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None

class AgentResponse(AgentBase):
    """Model for agent response."""
    id: UUID
    status: AgentStatus
    state_detail: Optional[AgentStateDetail] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

### Internal Models

Internal models have been updated to use string columns with validation and singular table names:

```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean, JSON, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from shared.models.src.enums import AgentStatus, AgentType
from src.models.enums import AgentStateDetail, ExecutionState

Base = declarative_base()

class AgentModel(Base):
    """Agent model."""
    __tablename__ = "agent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default=AgentStatus.INACTIVE.value)
    state_detail = Column(String(20), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    template_id = Column(String(50), nullable=True)
    configuration = Column(JSON, nullable=True)
    prompt_template = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint(
            f"type IN {tuple(item.value for item in AgentType)}",
            name="agent_type_check"
        ),
        CheckConstraint(
            f"status IN {tuple(item.value for item in AgentStatus)}",
            name="agent_status_check"
        ),
        CheckConstraint(
            f"state_detail IS NULL OR state_detail IN {tuple(item.value for item in AgentStateDetail)}",
            name="agent_state_detail_check"
        ),
    )

    def __init__(self, **kwargs):
        # Convert enum instances to their string values
        if "type" in kwargs and hasattr(kwargs["type"], "value"):
            kwargs["type"] = kwargs["type"].value
        elif "type" in kwargs and isinstance(kwargs["type"], str):
            # Validate string value against enum
            if kwargs["type"] not in [item.value for item in AgentType]:
                raise ValueError(f"Invalid value '{kwargs['type']}' for enum AgentType")
        
        if "status" in kwargs and hasattr(kwargs["status"], "value"):
            kwargs["status"] = kwargs["status"].value
        elif "status" in kwargs and isinstance(kwargs["status"], str):
            # Validate string value against enum
            if kwargs["status"] not in [item.value for item in AgentStatus]:
                raise ValueError(f"Invalid value '{kwargs['status']}' for enum AgentStatus")
        
        if "state_detail" in kwargs and hasattr(kwargs["state_detail"], "value"):
            kwargs["state_detail"] = kwargs["state_detail"].value
        elif "state_detail" in kwargs and isinstance(kwargs["state_detail"], str):
            # Validate string value against enum
            if kwargs["state_detail"] not in [item.value for item in AgentStateDetail]:
                raise ValueError(f"Invalid value '{kwargs['state_detail']}' for enum AgentStateDetail")
        
        super().__init__(**kwargs)
```

## Database Migration

A migration script has been created to add the missing tables and the state_detail column to the agent table:

```python
"""Create agent orchestrator tables

Revision ID: 20250326_create_agent_tables
Revises: 
Create Date: 2025-03-26

This migration creates the following tables for the Agent Orchestrator service:
1. agent_template
2. agent_execution
3. agent_checkpoint
4. agent_state_history
5. execution_state_history

Note: The agent table and human_interaction table already exist in the database.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20250326_create_agent_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_template table
    op.create_table(
        'agent_template',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('agent_type', sa.String(20), nullable=False),
        sa.Column('configuration_schema', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('default_configuration', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "agent_type IN ('COORDINATOR', 'ASSISTANT', 'RESEARCHER', 'DEVELOPER', 'DESIGNER', 'SPECIALIST', 'AUDITOR', 'CUSTOM')",
            name='agent_template_agent_type_check'
        )
    )
    
    # Create agent_state_history table
    op.create_table(
        'agent_state_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=False),
        sa.Column('previous_state_detail', sa.String(20), nullable=True),
        sa.Column('new_state_detail', sa.String(20), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.CheckConstraint(
            "previous_status IS NULL OR previous_status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE')",
            name='agent_state_history_previous_status_check'
        ),
        sa.CheckConstraint(
            "new_status IN ('INACTIVE', 'ACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE')",
            name='agent_state_history_new_status_check'
        ),
        sa.CheckConstraint(
            "previous_state_detail IS NULL OR previous_state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')",
            name='agent_state_history_previous_state_detail_check'
        ),
        sa.CheckConstraint(
            "new_state_detail IS NULL OR new_state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')",
            name='agent_state_history_new_state_detail_check'
        )
    )
    
    # Create agent_checkpoint table
    op.create_table(
        'agent_checkpoint',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True, unique=True),
        sa.Column('state_data', sa.JSON(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False, default=0),
        sa.Column('is_recoverable', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    
    # Create agent_execution table
    op.create_table(
        'agent_execution',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('state', sa.String(20), nullable=False, default='QUEUED'),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=False, default=0.0),
        sa.Column('status_message', sa.String(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='agent_execution_state_check'
        )
    )
    
    # Create execution_state_history table
    op.create_table(
        'execution_state_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_execution.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('previous_state', sa.String(20), nullable=True),
        sa.Column('new_state', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.CheckConstraint(
            "previous_state IS NULL OR previous_state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='execution_state_history_previous_state_check'
        ),
        sa.CheckConstraint(
            "new_state IN ('QUEUED', 'PREPARING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='execution_state_history_new_state_check'
        )
    )
    
    # Add state_detail column to agent table if it doesn't exist
    op.add_column('agent', sa.Column('state_detail', sa.String(20), nullable=True))
    op.create_check_constraint(
        'agent_state_detail_check',
        'agent',
        "state_detail IS NULL OR state_detail IN ('CREATED', 'INITIALIZING', 'READY', 'ACTIVE', 'PAUSED', 'ERROR', 'TERMINATED')"
    )
```

## Testing

Tests have been added to verify that enum validation works correctly:

```python
def test_create_with_enum_instance(self, db_session):
    """Test creating an agent with enum instances."""
    # Create an agent with enum instances
    agent = AgentModel(
        name="Test Agent",
        type=AgentType.DEVELOPER,
        status=AgentStatus.ACTIVE,
        state_detail=AgentStateDetail.READY,
        project_id=uuid.uuid4()
    )
    
    # Add to session and commit
    db_session.add(agent)
    db_session.commit()
    
    # Retrieve from database
    db_agent = db_session.query(AgentModel).filter_by(name="Test Agent").first()
    
    # Verify
    assert db_agent is not None
    assert db_agent.type == AgentType.DEVELOPER.value
    assert db_agent.status == AgentStatus.ACTIVE.value
    assert db_agent.state_detail == AgentStateDetail.READY.value
```

## Running the Migrations

To apply the migrations and create the necessary tables in the database, follow these steps:

### Windows

```bash
cd services/agent-orchestrator/scripts
apply_migration.bat
```

### Unix/Linux/macOS

```bash
cd services/agent-orchestrator/scripts
./apply_migration.sh
```

You can also specify a custom database URL if needed:

```bash
./apply_migration.sh --db-url postgresql://username:password@localhost:5432/database_name
```

The migration script will:
1. Run the Alembic migration to create the missing tables and add the state_detail column to the agent table
2. Verify that all tables and columns were created successfully

## Database Migration Status

The database migrations have been successfully applied to the PostgreSQL database. The following changes were made:

1. Added the `state_detail` column to the `agent` table with appropriate constraints
2. Created the following new tables:
   - `agent_template` - For storing agent templates
   - `agent_state_history` - For tracking agent state transitions
   - `agent_checkpoint` - For storing agent state checkpoints
   - `agent_execution` - For tracking agent executions
   - `execution_state_history` - For tracking execution state transitions

3. Added appropriate indexes for performance optimization:
   - `agent_state_history_agent_id_idx` on `agent_state_history(agent_id)`
   - `agent_state_history_timestamp_idx` on `agent_state_history(timestamp)`
   - `agent_checkpoint_agent_id_idx` on `agent_checkpoint(agent_id)`
   - `agent_execution_agent_id_idx` on `agent_execution(agent_id)`
   - `agent_execution_task_id_idx` on `agent_execution(task_id)`
   - `execution_state_history_execution_id_idx` on `execution_state_history(execution_id)`
   - `execution_state_history_timestamp_idx` on `execution_state_history(timestamp)`

4. Added constraints to ensure data integrity:
   - Check constraints for enum values on all enum columns
   - Foreign key constraints for relationships between tables
   - Unique constraint on `agent_checkpoint(agent_id)` to ensure each agent has only one checkpoint

## Implementation Status

The Agent Orchestrator service standardization is now complete. All planned changes have been implemented and verified:

✅ Created service-specific enums in a dedicated `enums.py` file
✅ Updated API models to use shared enums and add state_detail
✅ Updated internal models to use string columns with validation
✅ Set up Alembic migration infrastructure
✅ Created migration scripts for all required tables
✅ Applied database migrations successfully
✅ Added tests to verify enum validation
✅ Updated documentation to reflect the changes

## Next Steps

The next service to be standardized is the Planning System service, as outlined in the [Service Standardization Summary](service-standardization-summary.md).
