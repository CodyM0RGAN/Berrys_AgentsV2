"""
Tests for the agent repository.

This module contains tests for the agent repository, which is responsible
for accessing agent instructions, capabilities, knowledge domains, and
prompt templates from the database.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from ..src.repositories.agent_repository import AgentRepository
from ..src.models.internal import (
    AgentInstructions, AgentCapability, AgentKnowledgeDomain, AgentPromptTemplate
)


@pytest.fixture
def agent_instructions(db: Session):
    """Create test agent instructions."""
    agent_id = uuid.uuid4()
    agent = AgentInstructions(
        id=agent_id,
        agent_name="TestAgent",
        purpose="Test agent for unit tests",
        capabilities={
            "test_capability": {
                "description": "Test capability",
                "parameters": {"param1": "value1"}
            }
        },
        tone_guidelines="Test tone guidelines",
        knowledge_domains={
            "test_domain": {
                "priority": 1,
                "description": "Test domain"
            }
        },
        response_templates={
            "greeting": "Hello, I'm TestAgent!"
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(agent)
    db.flush()
    
    # Add capabilities
    capability = AgentCapability(
        id=uuid.uuid4(),
        agent_instruction_id=agent_id,
        capability_name="test_capability",
        description="Test capability",
        parameters={"param1": "value1"}
    )
    db.add(capability)
    
    # Add knowledge domains
    knowledge_domain = AgentKnowledgeDomain(
        id=uuid.uuid4(),
        agent_instruction_id=agent_id,
        domain_name="test_domain",
        priority_level=1,
        description="Test domain"
    )
    db.add(knowledge_domain)
    
    # Add prompt templates
    prompt_template = AgentPromptTemplate(
        id=uuid.uuid4(),
        agent_instruction_id=agent_id,
        template_name="test_template",
        template_version="1.0",
        template_content="This is a test template",
        context_parameters={"required": ["param1"], "optional": ["param2"]},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(prompt_template)
    
    db.commit()
    return agent


def test_get_agent_instructions(db: Session, agent_instructions):
    """Test getting agent instructions."""
    repository = AgentRepository(db)
    result = repository.get_agent_instructions("TestAgent")
    assert result is not None
    assert result.agent_name == "TestAgent"
    assert result.purpose == "Test agent for unit tests"


def test_get_agent_capabilities(db: Session, agent_instructions):
    """Test getting agent capabilities."""
    repository = AgentRepository(db)
    result = repository.get_agent_capabilities(agent_instructions.id)
    assert len(result) == 1
    assert result[0].capability_name == "test_capability"
    assert result[0].description == "Test capability"


def test_get_agent_knowledge_domains(db: Session, agent_instructions):
    """Test getting agent knowledge domains."""
    repository = AgentRepository(db)
    result = repository.get_agent_knowledge_domains(agent_instructions.id)
    assert len(result) == 1
    assert result[0].domain_name == "test_domain"
    assert result[0].description == "Test domain"


def test_get_agent_prompt_templates(db: Session, agent_instructions):
    """Test getting agent prompt templates."""
    repository = AgentRepository(db)
    result = repository.get_agent_prompt_templates(agent_instructions.id)
    assert len(result) == 1
    assert result[0].template_name == "test_template"
    assert result[0].template_version == "1.0"
    assert result[0].template_content == "This is a test template"


def test_get_agent_prompt_template(db: Session, agent_instructions):
    """Test getting a specific agent prompt template."""
    repository = AgentRepository(db)
    result = repository.get_agent_prompt_template(
        agent_instructions.id, "test_template", "1.0"
    )
    assert result is not None
    assert result.template_name == "test_template"
    assert result.template_version == "1.0"
    
    # Test getting the latest version
    result = repository.get_agent_prompt_template(
        agent_instructions.id, "test_template"
    )
    assert result is not None
    assert result.template_name == "test_template"
    assert result.template_version == "1.0"


def test_get_complete_agent_configuration(db: Session, agent_instructions):
    """Test getting complete agent configuration."""
    repository = AgentRepository(db)
    result = repository.get_complete_agent_configuration("TestAgent")
    assert result is not None
    assert result["agent_name"] == "TestAgent"
    assert result["purpose"] == "Test agent for unit tests"
    assert "test_capability" in result["capabilities"]
    assert "test_domain" in result["knowledge_domains"]
    assert "test_template" in result["prompt_templates"]
    assert result["prompt_templates"]["test_template"]["version"] == "1.0"


def test_get_nonexistent_agent(db: Session):
    """Test getting a nonexistent agent."""
    repository = AgentRepository(db)
    result = repository.get_agent_instructions("NonexistentAgent")
    assert result is None
    
    result = repository.get_complete_agent_configuration("NonexistentAgent")
    assert result == {}
