"""
Test constants for use across all services.

This module provides test constants that can be used across all services,
including database constants, API constants, and mock data constants.
"""

import os
from enum import Enum
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid


# Environment constants

class TestEnvironment(str, Enum):
    """Test environment enum."""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# Database constants

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test"
)

DATABASE_SCHEMA = "public"

DATABASE_TABLES = [
    "agents",
    "agent_templates",
    "agent_specializations",
    "agent_configurations",
    "models",
    "model_configurations",
    "model_versions",
    "projects",
    "project_configurations",
    "tasks",
    "task_results",
    "tools",
    "tool_configurations",
    "tool_versions",
    "users",
    "user_preferences",
]


# API constants

API_BASE_URL = "http://test"

API_ENDPOINTS = {
    "health": "/health",
    "agents": "/agents",
    "agent_templates": "/agent-templates",
    "agent_specializations": "/agent-specializations",
    "models": "/models",
    "model_versions": "/model-versions",
    "projects": "/projects",
    "tasks": "/tasks",
    "tools": "/tools",
    "tool_versions": "/tool-versions",
    "users": "/users",
}

API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

API_AUTH_HEADER = {
    "Authorization": "Bearer test_token"
}


# Mock data constants

MOCK_UUID = "123e4567-e89b-12d3-a456-426614174000"

MOCK_DATETIME = datetime(2025, 1, 1, 0, 0, 0)

MOCK_USER = {
    "id": str(uuid.uuid4()),
    "username": "test_user",
    "email": "test@example.com",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_PROJECT = {
    "id": str(uuid.uuid4()),
    "name": "Test Project",
    "description": "A test project",
    "user_id": MOCK_USER["id"],
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_AGENT = {
    "id": str(uuid.uuid4()),
    "name": "Test Agent",
    "description": "A test agent",
    "type": "GENERAL",
    "project_id": MOCK_PROJECT["id"],
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_AGENT_TEMPLATE = {
    "id": str(uuid.uuid4()),
    "name": "Test Agent Template",
    "description": "A test agent template",
    "type": "GENERAL",
    "configuration": {
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        "capabilities": [
            "text_generation",
            "code_generation",
        ],
    },
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_AGENT_SPECIALIZATION = {
    "id": str(uuid.uuid4()),
    "name": "Test Agent Specialization",
    "description": "A test agent specialization",
    "type": "CODING",
    "configuration": {
        "parameters": {
            "temperature": 0.5,
            "max_tokens": 2000,
        },
        "capabilities": [
            "code_generation",
            "code_review",
            "debugging",
        ],
    },
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_MODEL = {
    "id": str(uuid.uuid4()),
    "name": "Test Model",
    "description": "A test model",
    "provider": "TEST",
    "type": "LLM",
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_MODEL_VERSION = {
    "id": str(uuid.uuid4()),
    "model_id": MOCK_MODEL["id"],
    "version": "1.0.0",
    "description": "A test model version",
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_TOOL = {
    "id": str(uuid.uuid4()),
    "name": "Test Tool",
    "description": "A test tool",
    "capability": "test_capability",
    "source": "INTERNAL",
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_TOOL_VERSION = {
    "id": str(uuid.uuid4()),
    "tool_id": MOCK_TOOL["id"],
    "version": "1.0.0",
    "description": "A test tool version",
    "status": "ACTIVE",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_TASK = {
    "id": str(uuid.uuid4()),
    "project_id": MOCK_PROJECT["id"],
    "agent_id": MOCK_AGENT["id"],
    "name": "Test Task",
    "description": "A test task",
    "status": "PENDING",
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}

MOCK_TASK_RESULT = {
    "id": str(uuid.uuid4()),
    "task_id": MOCK_TASK["id"],
    "status": "SUCCESS",
    "result": {
        "output": "Test output",
        "metadata": {
            "execution_time": 1.5,
            "tokens_used": 100,
        },
    },
    "created_at": MOCK_DATETIME.isoformat(),
    "updated_at": MOCK_DATETIME.isoformat(),
}


# Test data constants

TEST_USERS = [
    {
        "id": str(uuid.uuid4()),
        "username": f"user_{i}",
        "email": f"user_{i}@example.com",
        "created_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
        "updated_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
    }
    for i in range(5)
]

TEST_PROJECTS = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Project {i}",
        "description": f"Project {i} description",
        "user_id": TEST_USERS[i % len(TEST_USERS)]["id"],
        "status": "ACTIVE",
        "created_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
        "updated_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
    }
    for i in range(5)
]

TEST_AGENTS = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Agent {i}",
        "description": f"Agent {i} description",
        "type": "GENERAL",
        "project_id": TEST_PROJECTS[i % len(TEST_PROJECTS)]["id"],
        "status": "ACTIVE",
        "created_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
        "updated_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
    }
    for i in range(5)
]

TEST_MODELS = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Model {i}",
        "description": f"Model {i} description",
        "provider": "TEST",
        "type": "LLM",
        "status": "ACTIVE",
        "created_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
        "updated_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
    }
    for i in range(5)
]

TEST_TOOLS = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Tool {i}",
        "description": f"Tool {i} description",
        "capability": f"capability_{i}",
        "source": "INTERNAL",
        "status": "ACTIVE",
        "created_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
        "updated_at": (MOCK_DATETIME + timedelta(days=i)).isoformat(),
    }
    for i in range(5)
]


# Error constants

ERROR_MESSAGES = {
    "not_found": "Resource not found",
    "already_exists": "Resource already exists",
    "invalid_request": "Invalid request",
    "unauthorized": "Unauthorized",
    "forbidden": "Forbidden",
    "internal_error": "Internal server error",
}

ERROR_CODES = {
    "not_found": 404,
    "already_exists": 409,
    "invalid_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "internal_error": 500,
}


# Test configuration constants

TEST_CONFIG = {
    "database": {
        "url": DATABASE_URL,
        "echo": False,
        "create_tables": True,
        "drop_tables": True,
    },
    "api": {
        "base_url": API_BASE_URL,
        "timeout": 10.0,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
    "auth": {
        "enabled": False,
        "token_url": "/token",
    },
}


# Service-specific constants

AGENT_ORCHESTRATOR_CONFIG = {
    "service_name": "agent-orchestrator",
    "service_url": "http://agent-orchestrator:8000",
    "database_url": DATABASE_URL,
}

MODEL_ORCHESTRATION_CONFIG = {
    "service_name": "model-orchestration",
    "service_url": "http://model-orchestration:8000",
    "database_url": DATABASE_URL,
}

PROJECT_COORDINATOR_CONFIG = {
    "service_name": "project-coordinator",
    "service_url": "http://project-coordinator:8000",
    "database_url": DATABASE_URL,
}

SERVICE_INTEGRATION_CONFIG = {
    "service_name": "service-integration",
    "service_url": "http://service-integration:8000",
    "database_url": DATABASE_URL,
}

TOOL_INTEGRATION_CONFIG = {
    "service_name": "tool-integration",
    "service_url": "http://tool-integration:8000",
    "database_url": DATABASE_URL,
}


# Test file paths

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")

TEST_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

TEST_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

TEST_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
