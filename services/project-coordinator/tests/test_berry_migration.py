"""
Tests for the Berry agent configuration migration.

This module contains tests for the migration script that creates the
agent_prompt_template table and inserts Berry's configuration.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from ..src.repositories.agent_repository import AgentRepository


def test_agent_prompt_template_table_exists(db: Session):
    """Test that the agent_prompt_template table exists."""
    inspector = inspect(db.bind)
    assert "agent_prompt_template" in inspector.get_table_names()


def test_agent_prompt_template_columns(db: Session):
    """Test that the agent_prompt_template table has the expected columns."""
    inspector = inspect(db.bind)
    columns = {column["name"] for column in inspector.get_columns("agent_prompt_template")}
    expected_columns = {
        "id", "agent_instruction_id", "template_name", "template_version",
        "template_content", "context_parameters", "created_at", "updated_at"
    }
    assert expected_columns.issubset(columns)


def test_berry_configuration_exists(db: Session):
    """Test that Berry's configuration exists in the database."""
    repository = AgentRepository(db)
    berry_config = repository.get_complete_agent_configuration("Berry")
    assert berry_config is not None
    assert berry_config["agent_name"] == "Berry"
    assert "purpose" in berry_config
    assert "capabilities" in berry_config
    assert "tone_guidelines" in berry_config
    assert "knowledge_domains" in berry_config
    assert "response_templates" in berry_config
    assert "prompt_templates" in berry_config


def test_berry_prompt_templates_exist(db: Session):
    """Test that Berry's prompt templates exist in the database."""
    repository = AgentRepository(db)
    berry_config = repository.get_complete_agent_configuration("Berry")
    assert "prompt_templates" in berry_config
    
    # Check that the expected prompt templates exist
    expected_templates = [
        "conversation_intent_recognition",
        "mental_model_building",
        "response_strategies",
        "project_potential_detection"
    ]
    
    for template_name in expected_templates:
        assert template_name in berry_config["prompt_templates"]
        template = berry_config["prompt_templates"][template_name]
        assert "version" in template
        assert "content" in template
        assert "context_parameters" in template


def test_berry_capabilities_exist(db: Session):
    """Test that Berry's capabilities exist in the database."""
    repository = AgentRepository(db)
    berry_config = repository.get_complete_agent_configuration("Berry")
    assert "capabilities" in berry_config
    
    # Check that the expected capabilities exist
    expected_capabilities = [
        "project_creation",
        "agent_assignment",
        "model_selection",
        "general_conversation",
        "project_opportunity_recognition"
    ]
    
    for capability_name in expected_capabilities:
        assert capability_name in berry_config["capabilities"]
        capability = berry_config["capabilities"][capability_name]
        assert "description" in capability


def test_berry_knowledge_domains_exist(db: Session):
    """Test that Berry's knowledge domains exist in the database."""
    repository = AgentRepository(db)
    berry_config = repository.get_complete_agent_configuration("Berry")
    assert "knowledge_domains" in berry_config
    
    # Check that the expected knowledge domains exist
    expected_domains = [
        "project_management",
        "ai_models",
        "agent_systems",
        "general_topics",
        "conversation_skills",
        "project_indicators"
    ]
    
    for domain_name in expected_domains:
        assert domain_name in berry_config["knowledge_domains"]
        domain = berry_config["knowledge_domains"][domain_name]
        assert "priority_level" in domain
        assert "description" in domain
