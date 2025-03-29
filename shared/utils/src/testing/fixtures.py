"""
Test fixtures for Berrys_AgentsV2.

This module provides reusable pytest fixtures for testing, including:
- Database fixtures
- Mock service clients
- Configuration fixtures
- Test data generators
"""

import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional, List, Callable, Union, Type

import pytest
from unittest.mock import MagicMock, patch

# Import database utilities
from .database import (
    get_in_memory_db_engine, 
    create_test_database, 
    drop_test_database,
    TestBase,
    TestUser,
    TestProject
)

# Try to import service-specific types
try:
    from shared.models.src.base import StandardModel
    from shared.models.src.enums import ProjectStatus, AgentStatus, TaskStatus
    HAS_SHARED_MODELS = True
except ImportError:
    HAS_SHARED_MODELS = False
    ProjectStatus = AgentStatus = TaskStatus = None


#
# Database Fixtures
#

@pytest.fixture
def test_db_engine():
    """
    Create a SQLite in-memory database engine for testing.
    
    Returns:
        SQLAlchemy engine instance.
    """
    return get_in_memory_db_engine()


@pytest.fixture
def test_db(test_db_engine):
    """
    Create a test database and session.
    
    This fixture creates the tables defined by TestBase,
    provides a session, and cleans up after the test.
    
    Args:
        test_db_engine: SQLAlchemy engine instance.
        
    Returns:
        SQLAlchemy session.
    """
    from sqlalchemy.orm import sessionmaker
    
    # Create tables
    create_test_database(test_db_engine)
    
    # Create session
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    
    yield session
    
    # Clean up
    session.close()
    drop_test_database(test_db_engine)


#
# Mock Service Client Fixtures
#

@pytest.fixture
def mock_service_client():
    """
    Create a mock service client.
    
    This fixture provides a mock service client that can be configured
    to return specific responses for specific API calls.
    
    Returns:
        Mock service client.
    """
    class MockServiceClient:
        def __init__(self):
            self.responses = {}
            self.calls = []
        
        def add_response(self, endpoint, method, response):
            """Add a response for a specific endpoint and method."""
            self.responses[(endpoint, method)] = response
        
        async def request(self, method, endpoint, **kwargs):
            """Mock the request method."""
            self.calls.append((method, endpoint, kwargs))
            return self.responses.get((endpoint, method), {})
        
        def get(self, endpoint, **kwargs):
            """Mock the get method."""
            return self.request("GET", endpoint, **kwargs)
        
        def post(self, endpoint, **kwargs):
            """Mock the post method."""
            return self.request("POST", endpoint, **kwargs)
        
        def put(self, endpoint, **kwargs):
            """Mock the put method."""
            return self.request("PUT", endpoint, **kwargs)
        
        def delete(self, endpoint, **kwargs):
            """Mock the delete method."""
            return self.request("DELETE", endpoint, **kwargs)
        
        def patch(self, endpoint, **kwargs):
            """Mock the patch method."""
            return self.request("PATCH", endpoint, **kwargs)
    
    return MockServiceClient()


@pytest.fixture
def patch_service_client(mock_service_client):
    """
    Patch the ServiceClient class with a mock.
    
    This fixture patches the shared.utils.src.clients.ServiceClient class
    with a mock that returns the mock_service_client.
    
    Args:
        mock_service_client: Mock service client.
        
    Returns:
        Function to patch a specific service client.
    """
    def _patch_client(module_path):
        patcher = patch(module_path, return_value=mock_service_client)
        mock_client = patcher.start()
        yield mock_client
        patcher.stop()
        
    return _patch_client


#
# Configuration Fixtures
#

@pytest.fixture
def test_config():
    """
    Create a test configuration.
    
    This fixture provides a configuration for testing with sensible defaults.
    
    Returns:
        Configuration dictionary.
    """
    return {
        "database_url": "sqlite:///:memory:",
        "log_level": "DEBUG",
        "testing": True,
        "api_keys": {
            "test": "test_key"
        },
        "jwt_secret": "test_secret",
        "cors_origins": ["http://localhost:3000"],
        "service_urls": {
            "project_coordinator": "http://localhost:8001",
            "agent_orchestrator": "http://localhost:8002",
            "model_orchestration": "http://localhost:8003",
            "planning_system": "http://localhost:8004",
            "tool_integration": "http://localhost:8005"
        }
    }


#
# Test Data Generators
#

@pytest.fixture
def generate_uuid():
    """
    Generate a deterministic UUID for testing.
    
    This fixture provides a function that generates UUIDs in a deterministic
    sequence for testing, making tests more repeatable.
    
    Returns:
        Function that generates UUIDs.
    """
    def _generate_uuid(index=0):
        """Generate a UUID based on an index."""
        # Create a deterministic UUID based on the index
        # This ensures that UUIDs are repeatable in tests
        return uuid.UUID(f"00000000-0000-0000-0000-{index:012d}")
    
    return _generate_uuid


@pytest.fixture
def generate_test_user():
    """
    Generate test user data.
    
    This fixture provides a function that generates test user data
    for testing.
    
    Returns:
        Function that generates user data.
    """
    def _generate_user(index=0, **kwargs):
        """Generate user data based on an index."""
        user_data = {
            "username": f"test_user_{index}",
            "email": f"test_user_{index}@example.com",
            "created_at": datetime.datetime.utcnow()
        }
        user_data.update(kwargs)
        return user_data
    
    return _generate_user


@pytest.fixture
def generate_test_project():
    """
    Generate test project data.
    
    This fixture provides a function that generates test project data
    for testing.
    
    Returns:
        Function that generates project data.
    """
    def _generate_project(index=0, **kwargs):
        """Generate project data based on an index."""
        project_data = {
            "name": f"Test Project {index}",
            "description": f"Description for test project {index}",
            "created_at": datetime.datetime.utcnow()
        }
        
        # Add status if shared models are available
        if HAS_SHARED_MODELS and ProjectStatus is not None:
            project_data["status"] = ProjectStatus.DRAFT
            
        project_data.update(kwargs)
        return project_data
    
    return _generate_project


# Project-specific test data generators

if HAS_SHARED_MODELS:
    @pytest.fixture
    def generate_agent_data():
        """
        Generate test agent data.
        
        This fixture provides a function that generates test agent data
        for testing.
        
        Returns:
            Function that generates agent data.
        """
        def _generate_agent(project_id=None, index=0, **kwargs):
            """Generate agent data based on an index."""
            agent_data = {
                "name": f"Test Agent {index}",
                "agent_type": "ASSISTANT",
                "status": AgentStatus.INACTIVE if AgentStatus else "INACTIVE",
                "config": {
                    "capabilities": ["chat", "planning"],
                    "parameters": {
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                },
                "created_at": datetime.datetime.utcnow()
            }
            
            if project_id is not None:
                agent_data["project_id"] = project_id
                
            agent_data.update(kwargs)
            return agent_data
        
        return _generate_agent
    
    @pytest.fixture
    def generate_task_data():
        """
        Generate test task data.
        
        This fixture provides a function that generates test task data
        for testing.
        
        Returns:
            Function that generates task data.
        """
        def _generate_task(project_id=None, agent_id=None, index=0, **kwargs):
            """Generate task data based on an index."""
            task_data = {
                "name": f"Test Task {index}",
                "description": f"Description for test task {index}",
                "status": TaskStatus.PENDING if TaskStatus else "PENDING",
                "priority": 1,
                "created_at": datetime.datetime.utcnow()
            }
            
            if project_id is not None:
                task_data["project_id"] = project_id
                
            if agent_id is not None:
                task_data["assigned_agent_id"] = agent_id
                
            task_data.update(kwargs)
            return task_data
        
        return _generate_task
