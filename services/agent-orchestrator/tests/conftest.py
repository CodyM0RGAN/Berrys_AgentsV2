import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Set up SQLAlchemy mocks before any imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from httpx import AsyncClient

# Create a base declarative model
Base = declarative_base()

# Mock all shared modules before any imports
sys.modules['shared'] = MagicMock()
sys.modules['shared.utils'] = MagicMock()
sys.modules['shared.utils.src.database'] = MagicMock()
sys.modules['shared.utils.src.messaging'] = MagicMock()
sys.modules['shared.utils.logging'] = MagicMock()
sys.modules['shared.utils.auth'] = MagicMock()
sys.modules['shared.models'] = MagicMock()

# Set up database mocks
db_mock = AsyncMock()
db_mock.Base = Base
db_mock.get_db = AsyncMock()
db_mock.init_db = AsyncMock()
db_mock.close_db_connection = AsyncMock()
db_mock.check_db_connection = AsyncMock(return_value=True)
sys.modules['shared.utils.src.database'] = db_mock

# Set up messaging mocks
messaging_mock = AsyncMock()
messaging_mock.init_messaging = AsyncMock()
messaging_mock.close_messaging = AsyncMock()
messaging_mock.get_event_bus = AsyncMock()
messaging_mock.get_command_bus = AsyncMock()
sys.modules['shared.utils.src.messaging'] = messaging_mock

# Set up logging mocks
logging_mock = AsyncMock()
logging_mock.setup_logging = MagicMock()
logging_mock.get_logger = MagicMock()
sys.modules['shared.utils.logging'] = logging_mock

# Set up auth mocks
auth_mock = AsyncMock()
auth_mock.create_access_token = AsyncMock()
auth_mock.get_current_user = AsyncMock()
auth_mock.get_password_hash = MagicMock()
auth_mock.verify_password = MagicMock()
auth_mock.require_permission = MagicMock()
sys.modules['shared.utils.auth'] = auth_mock

# Create mock dependencies
async def get_db():
    """Mock database dependency."""
    yield None

async def get_event_bus():
    """Mock event bus dependency."""
    return AsyncMock()

async def get_command_bus():
    """Mock command bus dependency."""
    return AsyncMock()

# Now import from src after all mocks are set up
from src.config import get_settings, Settings
from src.main import app
from src.models.internal import AgentModel, AgentStateModel, AgentTemplateModel, AgentCheckpointModel, AgentCommunicationModel


# Override settings for testing
@pytest.fixture(scope="session")
def settings() -> Settings:
    """
    Get test settings.
    """
    return get_settings()


# Database fixtures
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """
    Create a test database engine.
    """
    # Use test database URL
    test_db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test"
    )
    
    # Create engine
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Return engine
    yield engine
    
    # Close engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    """
    # Create session
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create session
    async with async_session() as session:
        # Start transaction
        async with session.begin():
            # Return session
            yield session
            
            # Rollback transaction
            await session.rollback()


# Override dependencies for testing
@pytest.fixture(scope="function")
def override_get_db(db_session: AsyncSession):
    """
    Override get_db dependency.
    """
    async def _override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = _override_get_db
    
    yield
    
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function")
def override_get_event_bus():
    """
    Override get_event_bus dependency.
    """
    # Create mock event bus
    event_bus = AsyncMock()
    event_bus.publish_event = AsyncMock()
    
    async def _override_get_event_bus():
        return event_bus
    
    app.dependency_overrides[get_event_bus] = _override_get_event_bus
    
    yield event_bus
    
    app.dependency_overrides.pop(get_event_bus, None)


@pytest.fixture(scope="function")
def override_get_command_bus():
    """
    Override get_command_bus dependency.
    """
    # Create mock command bus
    command_bus = AsyncMock()
    command_bus.send_command = AsyncMock()
    command_bus.register_handler = MagicMock()
    
    async def _override_get_command_bus():
        return command_bus
    
    app.dependency_overrides[get_command_bus] = _override_get_command_bus
    
    yield command_bus
    
    app.dependency_overrides.pop(get_command_bus, None)


# Test client
@pytest_asyncio.fixture(scope="function")
async def client(
    override_get_db,
    override_get_event_bus,
    override_get_command_bus,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Test data fixtures
@pytest_asyncio.fixture(scope="function")
async def agent_template(db_session: AsyncSession) -> Dict[str, Any]:
    """
    Create a test agent template.
    """
    # Create template
    template = AgentTemplateModel(
        id="test-template",
        name="Test Template",
        description="Test template description",
        agent_type="RESEARCHER",
        schema={
            "type": "object",
            "properties": {
                "key1": {"type": "string"},
                "key2": {"type": "number"},
            },
            "required": ["key1"],
        },
        default_configuration={
            "key1": "default-value",
            "key2": 42,
        },
        version="1.0.0",
    )
    
    # Add to session
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    
    # Return template data
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "agent_type": template.agent_type,
        "schema": template.schema,
        "default_configuration": template.default_configuration,
        "version": template.version,
    }


@pytest_asyncio.fixture(scope="function")
async def agent(db_session: AsyncSession, agent_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test agent.
    """
    # Create agent
    agent = AgentModel(
        name="Test Agent",
        description="Test agent description",
        type="RESEARCHER",
        project_id="00000000-0000-0000-0000-000000000001",
        template_id=agent_template["id"],
        configuration={
            "key1": "value1",
            "key2": 42,
        },
        prompt_template="You are a {{agent_type}} agent named {{name}}.",
        state="CREATED",
    )
    
    # Add to session
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    # Return agent data
    return {
        "id": str(agent.id),
        "name": agent.name,
        "description": agent.description,
        "type": agent.type,
        "project_id": agent.project_id,
        "template_id": agent.template_id,
        "configuration": agent.configuration,
        "prompt_template": agent.prompt_template,
        "state": agent.state,
    }


@pytest_asyncio.fixture(scope="function")
async def agent_state(db_session: AsyncSession, agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test agent state.
    """
    # Create agent state
    state = AgentStateModel(
        agent_id=agent["id"],
        state="CREATED",
        reason="Initial state",
    )
    
    # Add to session
    db_session.add(state)
    await db_session.commit()
    await db_session.refresh(state)
    
    # Return state data
    return {
        "id": str(state.id),
        "agent_id": str(state.agent_id),
        "state": state.state,
        "reason": state.reason,
        "created_at": state.created_at.isoformat(),
    }


@pytest_asyncio.fixture(scope="function")
async def agent_checkpoint(db_session: AsyncSession, agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test agent checkpoint.
    """
    # Create checkpoint
    checkpoint = AgentCheckpointModel(
        agent_id=agent["id"],
        sequence_number=1,
        state_data={
            "memory": ["Item 1", "Item 2"],
            "context": {"key": "value"},
        },
        is_recoverable=True,
    )
    
    # Add to session
    db_session.add(checkpoint)
    await db_session.commit()
    await db_session.refresh(checkpoint)
    
    # Return checkpoint data
    return {
        "id": str(checkpoint.id),
        "agent_id": str(checkpoint.agent_id),
        "sequence_number": checkpoint.sequence_number,
        "state_data": checkpoint.state_data,
        "is_recoverable": checkpoint.is_recoverable,
        "created_at": checkpoint.created_at.isoformat(),
    }


@pytest_asyncio.fixture(scope="function")
async def agent_communication(db_session: AsyncSession, agent: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a test agent communication.
    """
    # Create communication
    communication = AgentCommunicationModel(
        from_agent_id=agent["id"],
        to_agent_id="00000000-0000-0000-0000-000000000002",
        type="MESSAGE",
        content={
            "text": "Hello, agent!",
            "metadata": {"key": "value"},
        },
        status="SENT",
    )
    
    # Add to session
    db_session.add(communication)
    await db_session.commit()
    await db_session.refresh(communication)
    
    # Return communication data
    return {
        "id": str(communication.id),
        "from_agent_id": str(communication.from_agent_id),
        "to_agent_id": str(communication.to_agent_id),
        "type": communication.type,
        "content": communication.content,
        "status": communication.status,
        "created_at": communication.created_at.isoformat(),
        "delivered_at": communication.delivered_at.isoformat() if communication.delivered_at else None,
    }
