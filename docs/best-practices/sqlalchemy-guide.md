# SQLAlchemy Best Practices Guide

This guide provides best practices for working with SQLAlchemy in the Berrys_AgentsV2 project, focusing on common pitfalls, optimization techniques, and specific considerations for our microservices architecture.

## Quick Reference

- **Avoid reserved column names**: Don't use `metadata` as a column name in SQLAlchemy models
- **Handle circular dependencies**: Use string references and late binding for circular relationships
- **Use appropriate relationship types**: Choose the right relationship type for your data model
- **Optimize queries**: Use eager loading, query optimization, and indexing
- **Follow migration best practices**: Use Alembic for schema migrations
- **Database CLI access**: Use `psql -h localhost -p 5432 -U sa -d mas_framework` to connect to containerized PostgreSQL

## Model Definition

### Base Model

Use a common base model for all SQLAlchemy models:

```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Model Structure

Follow a consistent structure for model definitions:

```python
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import BaseModel

class ProjectModel(BaseModel):
    __tablename__ = "projects"
    
    name = Column(String, nullable=False)
    description = Column(JSONB, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    
    # Relationships
    agents = relationship("AgentModel", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="project", cascade="all, delete-orphan")
```

## Avoiding Reserved Column Names

### Problem: `metadata` Column Name

SQLAlchemy uses `metadata` internally, so using it as a column name causes conflicts:

```python
# DON'T DO THIS
class BadModel(BaseModel):
    __tablename__ = "bad_models"
    
    metadata = Column(JSONB, nullable=True)  # This will cause errors!
```

### Solution: Use Alternative Names

Use alternative column names like `meta_data`, `metadata_json`, or domain-specific names:

```python
# DO THIS INSTEAD
class GoodModel(BaseModel):
    __tablename__ = "good_models"
    
    meta_data = Column(JSONB, nullable=True)  # This works fine
```

### Real-world Examples

In our project, we follow a consistent pattern of prefixing "metadata" with the entity name:

```python
# PROBLEMATIC
class CommunicationModel(BaseModel):
    metadata = Column(JSON, nullable=True)  # Conflicts with SQLAlchemy's metadata

# FIXED
class CommunicationModel(BaseModel):
    communication_metadata = Column(JSON, nullable=True)  # Domain-specific name
```

Here are more examples from our codebase:

```python
# Project model
class Project(BaseModel):
    project_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'

# Tool model
class Tool(BaseModel):
    tool_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'

# AI Model model
class ModelModel(Base):
    model_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'

# Chat models
class ChatSession(Base):
    session_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'

class ChatMessage(Base):
    message_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata'
```

This consistent naming pattern makes it clear what the metadata relates to and avoids conflicts with SQLAlchemy's reserved names.

## SQLAlchemy Reserved Names

SQLAlchemy has several reserved names that should not be used as column names:

- `metadata` - Used for table metadata
- `query` - Used for query objects
- `session` - Used for session management
- `_sa_instance_state` - Used internally by SQLAlchemy
- `__table__` - References the table object
- `__mapper__` - References the mapper object

When you encounter errors like:

```
AttributeError: 'MetaData' object has no attribute 'x'
```

It's often because you're using a reserved name as a column name.

## Table Naming Conventions and Foreign Keys

### Lessons Learned from api-gateway Troubleshooting

When troubleshooting the api-gateway service, we discovered several issues related to table naming:

1. **Table name mismatch**: Our BaseModel uses a custom `__tablename__` method that converts CamelCase to snake_case and removes the "model" suffix. This means `UserModel` becomes `user` table (singular), not `users` (plural).

2. **Foreign key reference errors**: We had errors like:
   ```
   Foreign key associated with column 'agent_tools.agent_id' could not find table 'agents' with which to generate a foreign key to target column 'id'
   ```
   
   This happened because we were using plural names in foreign key references when the actual table name was singular:
   
   ```python
   # INCORRECT - Assumes table name is "agents"
   agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
   
   # CORRECT - References the actual table name "agent"
   agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=False)
   ```

3. **Solution**: When in doubt, explicitly declare the table name:
   ```python
   class AIModelModel(BaseModel):
       __tablename__ = 'ai_model'  # Explicitly set table name
       
       id = Column(String(100), primary_key=True)
       # ...
   ```

## Inheritance Patterns in SQLAlchemy

### Single-Table Inheritance

When working with the HumanInteractionModel in api-gateway, we implemented single-table inheritance:

```python
class HumanInteractionModel(BaseModel):
    """Base class for all human interactions."""
    
    __tablename__ = 'human_interaction'
    
    # Discriminator column
    type = Column(String(50), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'HUMAN_INTERACTION'
    }
    
    # Include all possible columns for all subclasses
    approved = Column(Boolean, nullable=True)  # Used by ApprovalRequestModel
    feedback = Column(JSON, nullable=True)     # Used by FeedbackRequestModel
```

Key lessons:
- Single-table inheritance stores all subclasses in one table
- Use a discriminator column to identify the type
- Include all subclass-specific columns in the base class
- Set `polymorphic_identity` for each subclass

This pattern works well when subclasses share most columns and have few unique columns.

## Handling Circular Dependencies

### Problem: Circular Import Dependencies

When models reference each other, circular imports can occur:

```python
# agent.py
from .tool import ToolModel  # Imports tool.py

# tool.py
from .agent import AgentModel  # Imports agent.py - circular import!
```

### Solution 1: String References

Use string references in relationship definitions:

```python
# agent.py
class AgentModel(BaseModel):
    __tablename__ = "agents"
    
    # Use string reference instead of importing ToolModel
    tools = relationship("ToolModel", secondary="agent_tools", back_populates="agents")
```

### Solution 2: Late Binding for Association Tables

Define association tables after model classes:

```python
# Define models first
class AgentModel(BaseModel):
    __tablename__ = "agents"
    # ...

class ToolModel(BaseModel):
    __tablename__ = "tools"
    # ...

# Then define association table
agent_tool_association = Table(
    'agent_tools',
    BaseModel.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id'), primary_key=True),
    Column('tool_id', UUID(as_uuid=True), ForeignKey('tools.id'), primary_key=True),
    Column('configuration', JSONB, nullable=True),
)

# Now set up relationships
AgentModel.tools = relationship("ToolModel", secondary=agent_tool_association, back_populates="agents")
ToolModel.agents = relationship("AgentModel", secondary=agent_tool_association, back_populates="tools")
```

### Solution 3: Explicit Join Conditions

For complex relationships, use explicit join conditions:

```python
class CommunicationModel(BaseModel):
    __tablename__ = "communications"
    
    from_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    to_agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    # Use explicit primaryjoin/secondaryjoin
    from_agent = relationship(
        "AgentModel", 
        foreign_keys=[from_agent_id],
        primaryjoin="CommunicationModel.from_agent_id == AgentModel.id",
        back_populates="sent_communications"
    )
    to_agent = relationship(
        "AgentModel", 
        foreign_keys=[to_agent_id],
        primaryjoin="CommunicationModel.to_agent_id == AgentModel.id",
        back_populates="received_communications"
    )
```

## Relationship Types

Choose the appropriate relationship type based on your data model:

### One-to-Many Relationship

```python
# Parent side (One)
class ProjectModel(BaseModel):
    __tablename__ = "projects"
    
    # One project has many agents
    agents = relationship("AgentModel", back_populates="project", cascade="all, delete-orphan")

# Child side (Many)
class AgentModel(BaseModel):
    __tablename__ = "agents"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Many agents belong to one project
    project = relationship("ProjectModel", back_populates="agents")
```

### Many-to-Many Relationship

```python
# Association table
agent_tool_association = Table(
    'agent_tools',
    BaseModel.metadata,
    Column('agent_id', UUID(as_uuid=True), ForeignKey('agents.id'), primary_key=True),
    Column('tool_id', UUID(as_uuid=True), ForeignKey('tools.id'), primary_key=True),
    Column('configuration', JSONB, nullable=True),
)

# First side
class AgentModel(BaseModel):
    __tablename__ = "agents"
    
    # Many agents use many tools
    tools = relationship("ToolModel", secondary=agent_tool_association, back_populates="agents")

# Second side
class ToolModel(BaseModel):
    __tablename__ = "tools"
    
    # Many tools are used by many agents
    agents = relationship("AgentModel", secondary=agent_tool_association, back_populates="tools")
```

### Self-Referential Relationship

```python
# Self-referential many-to-many (e.g., task dependencies)
task_dependency = Table(
    'task_dependencies',
    BaseModel.metadata,
    Column('dependent_task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
    Column('dependency_task_id', UUID(as_uuid=True), ForeignKey('tasks.id'), primary_key=True),
)

class TaskModel(BaseModel):
    __tablename__ = "tasks"
    
    # Self-referential relationship for task dependencies
    dependencies = relationship(
        "TaskModel",
        secondary=task_dependency,
        primaryjoin="TaskModel.id == task_dependencies.c.dependent_task_id",
        secondaryjoin="TaskModel.id == task_dependencies.c.dependency_task_id",
        backref="dependents"
    )
```

## Query Optimization

### Eager Loading

Use eager loading to avoid the N+1 query problem:

```python
# Without eager loading (N+1 problem)
projects = session.query(ProjectModel).all()
for project in projects:
    # This causes a separate query for each project
    for agent in project.agents:
        print(agent.name)

# With eager loading (efficient)
projects = session.query(ProjectModel).options(
    joinedload(ProjectModel.agents)
).all()
for project in projects:
    # No additional queries needed
    for agent in project.agents:
        print(agent.name)
```

### Selective Loading

Load only the columns you need:

```python
# Load only specific columns
project_names = session.query(ProjectModel.id, ProjectModel.name).all()
```

### Pagination

Use pagination for large result sets:

```python
# Paginate results
page = 1
page_size = 20
offset = (page - 1) * page_size

projects = session.query(ProjectModel).order_by(ProjectModel.created_at.desc()).offset(offset).limit(page_size).all()
```

### Indexing

Add indexes to frequently queried columns:

```python
class AgentModel(BaseModel):
    __tablename__ = "agents"
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
```

## Transaction Management

### Session Management

Use context managers for session management:

```python
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage
with get_session() as session:
    project = session.query(ProjectModel).get(project_id)
    # Do something with project
```

### Explicit Transactions

Use explicit transactions for complex operations:

```python
with get_session() as session:
    # Start a transaction
    project = ProjectModel(name="New Project", description={"key": "value"})
    session.add(project)
    
    # Create related entities
    agent = AgentModel(name="Agent 1", project=project)
    session.add(agent)
    
    # Transaction is committed at the end of the context manager
```

## Migration Best Practices

### Using Alembic

Use Alembic for database migrations:

```python
# Generate a migration
alembic revision --autogenerate -m "Add new column to projects"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1
```

### Migration Safety

Follow these practices for safe migrations:

1. **Backup**: Always back up the database before applying migrations
2. **Transaction Management**: Run migrations in transactions where possible
3. **Downgrade Path**: Ensure every migration has a working downgrade path
4. **Testing**: Test migrations on a copy of production data before deploying

### Complex Migrations

For complex migrations that cannot be auto-generated:

```python
def upgrade():
    # Add new table
    op.create_table(
        'new_table',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Data migration
    connection = op.get_bind()
    
    # Query existing data
    results = connection.execute("SELECT id, data FROM old_table")
    for row in results:
        # Transform data
        new_name = row.data.get('name', 'Default')
        
        # Insert into new table
        connection.execute(
            f"INSERT INTO new_table (id, name) VALUES ('{row.id}', '{new_name}')"
        )
```

## SQLAlchemy with FastAPI

### Dependency Injection

Use dependency injection for database sessions:

```python
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/projects/{project_id}")
def read_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = db.query(ProjectModel).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### Pydantic Integration

Use Pydantic models for API requests and responses:

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

class ProjectCreate(BaseModel):
    name: str
    description: Optional[Dict[str, Any]] = None
    status: str = "DRAFT"

class Project(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }

@app.post("/projects/", response_model=Project)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = ProjectModel(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
```

## Testing with SQLAlchemy

### Test Database Setup

Use an in-memory SQLite database for testing:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture
def tables(engine):
    BaseModel.metadata.create_all(engine)
    yield
    BaseModel.metadata.drop_all(engine)

@pytest.fixture
def session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

### Model Testing

Test model relationships and constraints:

```python
def test_project_agent_relationship(session):
    # Create a project
    project = ProjectModel(name="Test Project")
    session.add(project)
    session.commit()
    
    # Create an agent for the project
    agent = AgentModel(name="Test Agent", project=project)
    session.add(agent)
    session.commit()
    
    # Test relationship
    assert agent in project.agents
    assert agent.project == project
```

## Common Pitfalls and Solutions

### 1. Detached Instance Error

```python
# Problem: Using a detached instance
project = session1.query(ProjectModel).get(project_id)
session1.close()
session2.add(project)  # Error: Instance is not bound to a Session

# Solution: Merge the instance
project = session1.query(ProjectModel).get(project_id)
session1.close()
project = session2.merge(project)  # Merge the instance into the new session
```

### 2. Lazy Loading with Expired Session

```python
# Problem: Accessing lazy-loaded attributes after session close
project = session.query(ProjectModel).get(project_id)
session.close()
agents = project.agents  # Error: Session is closed

# Solution: Eager load the relationship
project = session.query(ProjectModel).options(
    joinedload(ProjectModel.agents)
).get(project_id)
session.close()
agents = project.agents  # Works fine
```

### 3. Bulk Operations Performance

```python
# Problem: Adding items one by one
for item in items:
    session.add(item)
    session.commit()  # Slow, commits after each item

# Solution: Bulk insert
session.bulk_save_objects(items)
session.commit()  # Fast, commits once
```

## Database CLI Access

### Connecting to Containerized PostgreSQL

For direct database access and SQL execution, use the PostgreSQL CLI (`psql`):

```bash
# Prerequisites:
# 1. Docker Desktop must be running
# 2. PostgreSQL container must be started
docker-compose up -d postgres

# Connect to database (using credentials from .env)
psql -h localhost -p 5432 -U sa -d mas_framework
```

### Essential psql Commands

```sql
-- List all tables
\dt

-- Describe table structure
\d project

-- Execute SQL query
SELECT * FROM project LIMIT 5;

-- Execute SQL file
\i path/to/script.sql

-- Exit psql
\q
```

### Alternative: Docker Exec Method

If you don't have PostgreSQL client tools installed locally:

```bash
# Connect directly through Docker container
docker exec -it berrys_agentsv2-postgres-1 psql -U sa -d mas_framework
```

### Troubleshooting

- **"psql not found"**: Add PostgreSQL bin directory to PATH or use full path
- **"Connection refused"**: Ensure Docker is running and container is started
- **Authentication errors**: Verify credentials match those in .env file

## Conclusion

Following these SQLAlchemy best practices will help ensure that your database operations are efficient, maintainable, and free from common pitfalls. Remember to avoid reserved column names, handle circular dependencies properly, use appropriate relationship types, optimize queries, and follow migration best practices.
