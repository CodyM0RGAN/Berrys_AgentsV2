"""
Schema validation tests for the agent-orchestrator service.

This module tests the database schema to ensure it matches the expected structure
and validates any changes to the schema.
"""

import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base

from shared.utils.src.testing.schema import SchemaValidator, format_schema_diff
from shared.utils.src.testing.database import get_in_memory_db_engine
from shared.utils.src.testing.performance import benchmark

from src.models.base import Base
from src.models.agent import Agent
from src.models.template import AgentTemplate
from src.models.lifecycle import AgentLifecycle
from src.models.state import AgentState
from src.models.human_interaction import HumanInteraction


class TestSchemaValidation:
    """Test database schema validation."""
    
    @pytest.fixture
    def db_engine(self):
        """Create an in-memory SQLite database for testing."""
        return get_in_memory_db_engine()
        
    @pytest.fixture
    def test_db(self, db_engine):
        """Set up test database with tables."""
        Base.metadata.create_all(db_engine)
        yield db_engine
        Base.metadata.drop_all(db_engine)
        
    @pytest.fixture
    def schema_validator(self, test_db):
        """Create a schema validator for the test database."""
        return SchemaValidator(test_db)
        
    def test_table_structure(self, schema_validator):
        """Test that all required tables exist in the database."""
        expected_tables = {
            'agent', 
            'agent_template', 
            'agent_lifecycle', 
            'agent_state',
            'human_interaction'
        }
        
        # Get tables from the database
        actual_tables = set(schema_validator.get_table_names())
        
        # Check that all expected tables exist
        assert expected_tables.issubset(actual_tables), \
            f"Missing tables: {expected_tables - actual_tables}"
            
    def test_agent_table_columns(self, schema_validator):
        """Test that the agent table has the required columns."""
        expected_columns = {
            'id', 'name', 'agent_type', 'status', 'config',
            'created_at', 'updated_at', 'project_id'
        }
        
        # Get columns from the agent table
        columns = schema_validator.get_table_columns('agent')
        actual_columns = {col['name'] for col in columns}
        
        # Check that all expected columns exist
        assert expected_columns.issubset(actual_columns), \
            f"Missing columns: {expected_columns - actual_columns}"
            
    def test_agent_template_table_columns(self, schema_validator):
        """Test that the agent_template table has the required columns."""
        expected_columns = {
            'id', 'name', 'description', 'template_type', 
            'config_schema', 'created_at', 'updated_at'
        }
        
        # Get columns from the agent_template table
        columns = schema_validator.get_table_columns('agent_template')
        actual_columns = {col['name'] for col in columns}
        
        # Check that all expected columns exist
        assert expected_columns.issubset(actual_columns), \
            f"Missing columns: {expected_columns - actual_columns}"
            
    def test_schema_completeness(self, schema_validator):
        """Test that the database schema matches the SQLAlchemy models."""
        # Compare schema with models
        differences = schema_validator.compare_schema_with_models(Base)
        
        # There should be no missing tables or columns
        assert not differences['missing_tables'], \
            f"Missing tables: {differences['missing_tables']}"
            
        assert not differences['column_differences'], \
            f"Column differences: {differences['column_differences']}"
            
    @benchmark(iterations=5, warmup=1)
    def test_schema_validation_performance(self, schema_validator):
        """Test performance of schema validation."""
        # This function will be benchmarked
        return schema_validator.get_database_schema()


def test_model_creation_performance():
    """Test performance of model creation."""
    @benchmark(iterations=100, warmup=5)
    def create_agent():
        """Create an agent instance."""
        return Agent(
            name="Test Agent",
            agent_type="ASSISTANT",
            status="ACTIVE",
            config={
                "capabilities": ["chat", "planning"],
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            },
            project_id="project-123"
        )
        
    # Run the benchmark
    create_agent()


def test_model_serialization_performance():
    """Test performance of model serialization to dict."""
    # Create an agent
    agent = Agent(
        name="Test Agent",
        agent_type="ASSISTANT",
        status="ACTIVE",
        config={
            "capabilities": ["chat", "planning"],
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        project_id="project-123"
    )
    
    @benchmark(iterations=100, warmup=5)
    def serialize_agent():
        """Serialize an agent to a dictionary."""
        return {
            "id": agent.id,
            "name": agent.name,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "config": agent.config,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "project_id": agent.project_id
        }
        
    # Run the benchmark
    serialize_agent()
