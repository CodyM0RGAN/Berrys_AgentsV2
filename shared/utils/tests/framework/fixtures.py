"""
Test fixtures for use across all services.

This module provides test fixtures that can be used across all services,
including database fixtures, API fixtures, and mock fixtures.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator, Generator, Type

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from .database import DatabaseTestHelper, DatabaseTestConfig
from .api import APITestHelper, APITestConfig
from .config import BaseTestConfig, ConfigLoader


# Database fixtures

@pytest_asyncio.fixture
async def db_engine(test_config: BaseTestConfig) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a database engine for testing.
    
    Args:
        test_config: Test configuration
        
    Yields:
        AsyncEngine: Database engine
    """
    # Create engine
    engine = create_async_engine(
        test_config.database_url or "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test",
        echo=test_config.database_echo,
    )
    
    yield engine
    
    # Close engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session_factory(db_engine: AsyncEngine) -> sessionmaker:
    """
    Create a database session factory for testing.
    
    Args:
        db_engine: Database engine
        
    Returns:
        sessionmaker: Session factory
    """
    return sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def db_session(db_session_factory: sessionmaker) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.
    
    Args:
        db_session_factory: Session factory
        
    Yields:
        AsyncSession: Database session
    """
    async with db_session_factory() as session:
        # Start transaction
        async with session.begin():
            # Return session
            yield session
            
            # Rollback transaction
            await session.rollback()


@pytest_asyncio.fixture
async def db_helper(test_config: BaseTestConfig) -> AsyncGenerator[DatabaseTestHelper, None]:
    """
    Create a database helper for testing.
    
    Args:
        test_config: Test configuration
        
    Yields:
        DatabaseTestHelper: Database helper
    """
    # Create database config
    db_config = DatabaseTestConfig(
        database_url=test_config.database_url,
        echo=test_config.database_echo,
    )
    
    # Create helper
    helper = DatabaseTestHelper(db_config)
    
    yield helper
    
    # Clean up
    await helper.teardown_database()


# API fixtures

@pytest.fixture
def test_app() -> FastAPI:
    """
    Create a FastAPI application for testing.
    
    Returns:
        FastAPI: FastAPI application
    """
    app = FastAPI(title="Test API")
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """
    Create a test client for testing.
    
    Args:
        test_app: FastAPI application
        
    Returns:
        TestClient: Test client
    """
    return TestClient(test_app)


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI, test_config: BaseTestConfig) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async client for testing.
    
    Args:
        test_app: FastAPI application
        test_config: Test configuration
        
    Yields:
        AsyncClient: Async client
    """
    async with AsyncClient(app=test_app, base_url=test_config.api_base_url) as client:
        yield client


@pytest.fixture
def api_helper(test_app: FastAPI, test_config: BaseTestConfig) -> APITestHelper:
    """
    Create an API helper for testing.
    
    Args:
        test_app: FastAPI application
        test_config: Test configuration
        
    Returns:
        APITestHelper: API helper
    """
    # Create API config
    api_config = APITestConfig(
        base_url=test_config.api_base_url,
        timeout=test_config.api_timeout,
    )
    
    # Create helper
    return APITestHelper(test_app, api_config)


# Configuration fixtures

@pytest.fixture
def test_config() -> BaseTestConfig:
    """
    Create a test configuration.
    
    Returns:
        BaseTestConfig: Test configuration
    """
    # Load configuration from environment variables
    return ConfigLoader.from_env(BaseTestConfig)


@pytest.fixture
def test_config_from_file(request) -> BaseTestConfig:
    """
    Create a test configuration from a file.
    
    Args:
        request: Pytest request
        
    Returns:
        BaseTestConfig: Test configuration
    """
    # Get config file path from marker
    marker = request.node.get_closest_marker("config_file")
    if marker is None:
        pytest.skip("No config_file marker found")
    
    file_path = marker.args[0]
    
    # Load configuration from file
    if file_path.endswith(".json"):
        return ConfigLoader.from_json(BaseTestConfig, file_path)
    elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
        return ConfigLoader.from_yaml(BaseTestConfig, file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


# Logging fixtures

@pytest.fixture
def test_logger(test_config: BaseTestConfig) -> logging.Logger:
    """
    Create a logger for testing.
    
    Args:
        test_config: Test configuration
        
    Returns:
        logging.Logger: Logger
    """
    # Create logger
    logger = logging.getLogger("test")
    
    # Set level
    logger.setLevel(getattr(logging, test_config.log_level))
    
    # Add handler
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(test_config.log_format))
    logger.addHandler(handler)
    
    return logger


# Temporary directory fixtures

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for testing.
    
    Yields:
        str: Temporary directory path
    """
    import tempfile
    import shutil
    
    # Create directory
    temp_dir = tempfile.mkdtemp()
    
    yield temp_dir
    
    # Clean up
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_file(temp_dir: str) -> Generator[str, None, None]:
    """
    Create a temporary file for testing.
    
    Args:
        temp_dir: Temporary directory
        
    Yields:
        str: Temporary file path
    """
    import tempfile
    
    # Create file
    fd, path = tempfile.mkstemp(dir=temp_dir)
    os.close(fd)
    
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.remove(path)


# Mock fixtures

@pytest.fixture
def mock_response() -> Dict[str, Any]:
    """
    Create a mock response for testing.
    
    Returns:
        Dict[str, Any]: Mock response
    """
    return {
        "status": "success",
        "message": "Operation completed successfully",
        "data": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test",
            "created_at": "2025-01-01T00:00:00Z",
        },
    }


@pytest.fixture
def mock_error_response() -> Dict[str, Any]:
    """
    Create a mock error response for testing.
    
    Returns:
        Dict[str, Any]: Mock error response
    """
    return {
        "status": "error",
        "message": "Operation failed",
        "error": {
            "code": "INVALID_REQUEST",
            "message": "Invalid request parameters",
            "details": [
                {
                    "field": "name",
                    "message": "Name is required",
                },
            ],
        },
    }


@pytest.fixture
def mock_db_session() -> AsyncSession:
    """
    Create a mock database session for testing.
    
    Returns:
        AsyncSession: Mock database session
    """
    from unittest.mock import AsyncMock
    
    # Create mock
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock methods
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    return mock_session


# Event loop fixtures

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for testing.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Service-specific fixtures

@pytest_asyncio.fixture
async def agent_orchestrator_db(db_helper: DatabaseTestHelper) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for the agent-orchestrator service.
    
    Args:
        db_helper: Database helper
        
    Yields:
        AsyncSession: Database session
    """
    # Import Base from agent-orchestrator
    from services.agent_orchestrator.src.models.base import Base
    
    # Setup database
    await db_helper.setup_database(Base)
    
    # Create session
    async with db_helper.db_session() as session:
        yield session


@pytest_asyncio.fixture
async def model_orchestration_db(db_helper: DatabaseTestHelper) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for the model-orchestration service.
    
    Args:
        db_helper: Database helper
        
    Yields:
        AsyncSession: Database session
    """
    # Import Base from model-orchestration
    from services.model_orchestration.src.models.base import Base
    
    # Setup database
    await db_helper.setup_database(Base)
    
    # Create session
    async with db_helper.db_session() as session:
        yield session


@pytest_asyncio.fixture
async def project_coordinator_db(db_helper: DatabaseTestHelper) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for the project-coordinator service.
    
    Args:
        db_helper: Database helper
        
    Yields:
        AsyncSession: Database session
    """
    # Import Base from project-coordinator
    from services.project_coordinator.src.models.base import Base
    
    # Setup database
    await db_helper.setup_database(Base)
    
    # Create session
    async with db_helper.db_session() as session:
        yield session


@pytest_asyncio.fixture
async def service_integration_db(db_helper: DatabaseTestHelper) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for the service-integration service.
    
    Args:
        db_helper: Database helper
        
    Yields:
        AsyncSession: Database session
    """
    # Import Base from service-integration
    from services.service_integration.src.models.base import Base
    
    # Setup database
    await db_helper.setup_database(Base)
    
    # Create session
    async with db_helper.db_session() as session:
        yield session


@pytest_asyncio.fixture
async def tool_integration_db(db_helper: DatabaseTestHelper) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for the tool-integration service.
    
    Args:
        db_helper: Database helper
        
    Yields:
        AsyncSession: Database session
    """
    # Import Base from tool-integration
    from services.tool_integration.src.models.base import Base
    
    # Setup database
    await db_helper.setup_database(Base)
    
    # Create session
    async with db_helper.db_session() as session:
        yield session


# Example usage:
# 
# ```python
# import pytest
# from shared.utils.tests.framework.fixtures import db_session, test_app, test_client
# 
# @pytest.mark.asyncio
# async def test_something(db_session, test_app, test_client):
#     # Test code here
#     pass
