"""
Tests for the AgentToModelAdapter.

This module contains tests for the AgentToModelAdapter, which converts
entities between the Agent Orchestrator and Model Orchestration service representations.
"""

import unittest
import uuid
from datetime import datetime
from typing import Dict, Any

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from shared.models.src.adapters import AgentToModelAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import ProjectStatus, AgentStatus, TaskStatus, TaskPriority, AgentType, ModelCapability
from shared.models.src.base import BaseEntityModel


class TestAgentToModelAdapter(unittest.TestCase):
    """Tests for the AgentToModelAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_id = uuid.uuid4()
        self.agent_id = uuid.uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Sample project data
        self.agent_project = {
            "project_id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": "DRAFT",
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample agent data
        self.agent_orchestrator_agent = {
            "id": self.agent_id,
            "name": "Test Agent",
            "agent_type": AgentType.DEVELOPER,
            "status": AgentStatus.ACTIVE,
            "project_id": self.project_id,
            "config": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def test_project_to_model(self):
        """Test converting an Agent Orchestrator project to a Model Orchestration project."""
        # Convert the project
        model_project = AgentToModelAdapter.project_to_model(self.agent_project)
        
        # Verify the conversion
        self.assertEqual(model_project["project_id"], self.project_id)
        self.assertEqual(model_project["name"], "Test Project")
        self.assertEqual(model_project["status"], "DRAFT")
        self.assertEqual(model_project["config"], {"key": "value"})
        
        # Description field is not present in Model Orchestration
        self.assertNotIn("description", model_project)
    
    def test_project_from_model(self):
        """Test converting a Model Orchestration project to an Agent Orchestrator project."""
        # Create a Model Orchestration project
        model_project = {
            "project_id": self.project_id,
            "name": "Test Project",
            "status": "DRAFT",
            "config": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the project
        agent_project = AgentToModelAdapter.project_from_model(model_project)
        
        # Verify the conversion
        self.assertEqual(agent_project["project_id"], self.project_id)
        self.assertEqual(agent_project["name"], "Test Project")
        self.assertEqual(agent_project["status"], "DRAFT")
        self.assertEqual(agent_project["metadata"], {"key": "value"})
        
        # Description field is added with empty string
        self.assertEqual(agent_project["description"], "")
    
    def test_agent_to_model(self):
        """Test converting an Agent Orchestrator agent to a Model Orchestration agent."""
        # Convert the agent
        model_agent = AgentToModelAdapter.agent_to_model(self.agent_orchestrator_agent)
        
        # Verify the conversion
        self.assertEqual(model_agent["agent_id"], self.agent_id)
        self.assertEqual(model_agent["name"], "Test Agent")
        self.assertEqual(model_agent["type"], "DEVELOPER")
        self.assertEqual(model_agent["status"], "ACTIVE")
        self.assertEqual(model_agent["project_id"], self.project_id)
        
        # Verify capabilities
        self.assertEqual(model_agent["capabilities"], [ModelCapability.CHAT.value, ModelCapability.COMPLETION.value])
        
        # Verify settings with capability configuration
        self.assertIn("capability_config", model_agent["settings"])
        capability_config = model_agent["settings"]["capability_config"]
        
        # Verify chat capability configuration
        self.assertIn("chat", capability_config)
        self.assertEqual(capability_config["chat"]["max_tokens"], 4000)
        self.assertEqual(capability_config["chat"]["temperature"], 0.7)
        self.assertEqual(capability_config["chat"]["top_p"], 0.95)
        
        # Verify completion capability configuration
        self.assertIn("completion", capability_config)
        self.assertEqual(capability_config["completion"]["max_tokens"], 2000)
        self.assertEqual(capability_config["completion"]["temperature"], 0.5)
        self.assertEqual(capability_config["completion"]["top_p"], 0.9)
        
        # Verify original settings are preserved
        self.assertEqual(model_agent["settings"]["key"], "value")
    
    def test_agent_from_model(self):
        """Test converting a Model Orchestration agent to an Agent Orchestrator agent."""
        # Create a Model Orchestration agent
        model_agent = {
            "agent_id": self.agent_id,
            "name": "Test Agent",
            "type": "DEVELOPER",
            "status": "active",
            "project_id": self.project_id,
            "settings": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the agent
        agent_orchestrator_agent = AgentToModelAdapter.agent_from_model(model_agent)
        
        # Verify the conversion
        self.assertEqual(agent_orchestrator_agent["id"], self.agent_id)
        self.assertEqual(agent_orchestrator_agent["name"], "Test Agent")
        self.assertEqual(agent_orchestrator_agent["agent_type"], "DEVELOPER")
        self.assertEqual(agent_orchestrator_agent["status"], "ACTIVE")
        self.assertEqual(agent_orchestrator_agent["project_id"], self.project_id)
        self.assertEqual(agent_orchestrator_agent["config"], {"key": "value"})
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        # Test with None
        with self.assertRaises(AdapterValidationError):
            AgentToModelAdapter.project_to_model(None)
        
        # Test with non-dict, non-BaseModel
        with self.assertRaises(AdapterValidationError):
            AgentToModelAdapter.project_to_model("not a dict or model")
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        # Create a project with missing fields
        project_with_missing_fields = {
            "project_id": self.project_id,
            "name": "Test Project"
        }
        
        # Convert the project
        model_project = AgentToModelAdapter.project_to_model(project_with_missing_fields)
        
        # Verify the conversion (should have default values)
        self.assertEqual(model_project["project_id"], self.project_id)
        self.assertEqual(model_project["name"], "Test Project")
        self.assertEqual(model_project["config"], {})
        
        # Status field is not present
        self.assertNotIn("status", model_project)
    
    def test_agent_with_string_type(self):
        """Test converting an agent with string type."""
        # Create an agent with string type
        agent_with_string_type = self.agent_orchestrator_agent.copy()
        agent_with_string_type["agent_type"] = "DEVELOPER"
        
        # Convert the agent
        model_agent = AgentToModelAdapter.agent_to_model(agent_with_string_type)
        
        # Verify the conversion
        self.assertEqual(model_agent["type"], "DEVELOPER")
        
        # Verify capabilities
        self.assertEqual(model_agent["capabilities"], [ModelCapability.CHAT.value, ModelCapability.COMPLETION.value])
        
        # Verify capability configuration
        self.assertIn("capability_config", model_agent["settings"])


    def test_designer_agent_capabilities(self):
        """Test converting a designer agent with image generation capability."""
        # Create a designer agent
        designer_agent = self.agent_orchestrator_agent.copy()
        designer_agent["agent_type"] = AgentType.DESIGNER
        
        # Convert the agent
        model_agent = AgentToModelAdapter.agent_to_model(designer_agent)
        
        # Verify the conversion
        self.assertEqual(model_agent["type"], "DESIGNER")
        
        # Verify capabilities
        self.assertEqual(model_agent["capabilities"], [ModelCapability.IMAGE_GENERATION.value])
        
        # Verify capability configuration
        self.assertIn("capability_config", model_agent["settings"])
        capability_config = model_agent["settings"]["capability_config"]
        
        # Verify image generation capability configuration
        self.assertIn("image_generation", capability_config)
        self.assertEqual(capability_config["image_generation"]["size"], "1024x1024")
        self.assertEqual(capability_config["image_generation"]["quality"], "standard")
        self.assertEqual(capability_config["image_generation"]["style"], "natural")

    def test_agent_from_agent_orchestrator_with_both_type_and_agent_type(self):
        """Test converting an Agent Orchestrator agent with both type and agent_type."""
        # Create an agent with both type and agent_type
        agent_data = {
            "id": self.agent_id,
            "name": "Test Agent",
            "agent_type": AgentType.DEVELOPER,
            "type": "RESEARCHER",  # This should be ignored
            "status": AgentStatus.ACTIVE,
            "project_id": self.project_id,
            "config": {"key": "value"}
        }

        # Convert the agent
        coordinator_agent = AgentToModelAdapter.agent_from_model(agent_data)

        # Verify the conversion
        self.assertEqual(coordinator_agent["id"], self.agent_id)
        self.assertEqual(coordinator_agent["type"], "DEVELOPER")


if __name__ == "__main__":
    unittest.main()
