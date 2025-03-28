"""
Tests for the CoordinatorToAgentAdapter.

This module contains tests for the CoordinatorToAgentAdapter, which converts
entities between the Project Coordinator and Agent Orchestrator service representations.
"""

import unittest
import uuid
from datetime import datetime
from typing import Dict, Any

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from shared.models.src.adapters import CoordinatorToAgentAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import ProjectStatus, AgentStatus, TaskStatus, TaskPriority, AgentType


class TestCoordinatorToAgentAdapter(unittest.TestCase):
    """Tests for the CoordinatorToAgentAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_id = uuid.uuid4()
        self.owner_id = uuid.uuid4()
        self.agent_id = uuid.uuid4()
        self.task_id = uuid.uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Sample project data
        self.coordinator_project = {
            "id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": ProjectStatus.DRAFT,
            "owner_id": self.owner_id,
            "project_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample agent data
        self.coordinator_agent = {
            "id": self.agent_id,
            "name": "Test Agent",
            "type": "developer",
            "status": "active",
            "project_id": self.project_id,
            "agent_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample task data
        self.coordinator_task = {
            "id": self.task_id,
            "name": "Test Task",
            "description": "A test task",
            "status": "pending",
            "priority": 3,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "task_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def test_project_to_agent(self):
        """Test converting a Project Coordinator project to an Agent Orchestrator project."""
        # Convert the project
        agent_project = CoordinatorToAgentAdapter.project_to_agent(self.coordinator_project)
        
        # Verify the conversion
        self.assertEqual(agent_project["project_id"], self.project_id)
        self.assertEqual(agent_project["name"], "Test Project")
        self.assertEqual(agent_project["description"], "A test project")
        self.assertEqual(agent_project["status"], "DRAFT")
        self.assertEqual(agent_project["created_by"], self.owner_id)
        self.assertEqual(agent_project["metadata"], {"key": "value"})
    
    def test_project_from_agent(self):
        """Test converting an Agent Orchestrator project to a Project Coordinator project."""
        # Create an Agent Orchestrator project
        agent_project = {
            "project_id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": "DRAFT",
            "created_by": self.owner_id,
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the project
        coordinator_project = CoordinatorToAgentAdapter.project_from_agent(agent_project)
        
        # Verify the conversion
        self.assertEqual(coordinator_project["id"], self.project_id)
        self.assertEqual(coordinator_project["name"], "Test Project")
        self.assertEqual(coordinator_project["description"], "A test project")
        self.assertEqual(coordinator_project["status"], ProjectStatus.DRAFT)
        self.assertEqual(coordinator_project["owner_id"], self.owner_id)
        self.assertEqual(coordinator_project["project_metadata"], {"key": "value"})
    
    def test_agent_to_agent_orchestrator(self):
        """Test converting a Project Coordinator agent to an Agent Orchestrator agent."""
        # Convert the agent
        agent_orchestrator_agent = CoordinatorToAgentAdapter.agent_to_agent_orchestrator(self.coordinator_agent)
        
        # Verify the conversion
        self.assertEqual(agent_orchestrator_agent["id"], self.agent_id)
        self.assertEqual(agent_orchestrator_agent["name"], "Test Agent")
        self.assertEqual(agent_orchestrator_agent["agent_type"], AgentType.DEVELOPER)
        self.assertEqual(agent_orchestrator_agent["status"], AgentStatus.ACTIVE)
        self.assertEqual(agent_orchestrator_agent["project_id"], self.project_id)
        self.assertEqual(agent_orchestrator_agent["config"], {"key": "value"})
    
    def test_agent_from_agent_orchestrator(self):
        """Test converting an Agent Orchestrator agent to a Project Coordinator agent."""
        # Create an Agent Orchestrator agent
        agent_orchestrator_agent = {
            "id": self.agent_id,
            "name": "Test Agent",
            "agent_type": AgentType.DEVELOPER,
            "status": AgentStatus.ACTIVE,
            "project_id": self.project_id,
            "config": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the agent
        coordinator_agent = CoordinatorToAgentAdapter.agent_from_agent_orchestrator(agent_orchestrator_agent)
        
        # Verify the conversion
        self.assertEqual(coordinator_agent["id"], self.agent_id)
        self.assertEqual(coordinator_agent["name"], "Test Agent")
        self.assertEqual(coordinator_agent["type"], "DEVELOPER")
        self.assertEqual(coordinator_agent["status"], "ACTIVE")
        self.assertEqual(coordinator_agent["project_id"], self.project_id)
        self.assertEqual(coordinator_agent["agent_metadata"], {"key": "value"})
    
    def test_task_to_agent(self):
        """Test converting a Project Coordinator task to an Agent Orchestrator task."""
        # Convert the task
        agent_task = CoordinatorToAgentAdapter.task_to_agent(self.coordinator_task)
        
        # Verify the conversion
        self.assertEqual(agent_task["task_id"], self.task_id)
        self.assertEqual(agent_task["name"], "Test Task")
        self.assertEqual(agent_task["description"], "A test task")
        self.assertEqual(agent_task["status"], TaskStatus.PENDING)
        self.assertEqual(agent_task["priority"], TaskPriority.MEDIUM)
        self.assertEqual(agent_task["assigned_agent_id"], self.agent_id)
        self.assertEqual(agent_task["project_id"], self.project_id)
        self.assertEqual(agent_task["metadata"], {"key": "value"})
    
    def test_task_from_agent(self):
        """Test converting an Agent Orchestrator task to a Project Coordinator task."""
        # Create an Agent Orchestrator task
        agent_task = {
            "task_id": self.task_id,
            "name": "Test Task",
            "description": "A test task",
            "status": TaskStatus.PENDING,
            "priority": TaskPriority.MEDIUM,
            "assigned_agent_id": self.agent_id,
            "project_id": self.project_id,
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the task
        coordinator_task = CoordinatorToAgentAdapter.task_from_agent(agent_task)
        
        # Verify the conversion
        self.assertEqual(coordinator_task["id"], self.task_id)
        self.assertEqual(coordinator_task["name"], "Test Task")
        self.assertEqual(coordinator_task["description"], "A test task")
        self.assertEqual(coordinator_task["status"], "PENDING")
        self.assertEqual(coordinator_task["priority"], 3)
        self.assertEqual(coordinator_task["agent_id"], self.agent_id)
        self.assertEqual(coordinator_task["project_id"], self.project_id)
        self.assertEqual(coordinator_task["task_metadata"], {"key": "value"})
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        # Test with None
        with self.assertRaises(AdapterValidationError):
            CoordinatorToAgentAdapter.project_to_agent(None)
        
        # Test with non-dict, non-BaseModel
        with self.assertRaises(AdapterValidationError):
            CoordinatorToAgentAdapter.project_to_agent("not a dict or model")
    
    def test_invalid_status(self):
        """Test handling of invalid status values."""
        # Create a project with invalid status
        project_with_invalid_status = self.coordinator_project.copy()
        project_with_invalid_status["status"] = "INVALID_STATUS"
        
        # Convert the project
        agent_project = CoordinatorToAgentAdapter.project_to_agent(project_with_invalid_status)
        
        # Verify the conversion (should convert to string)
        self.assertEqual(agent_project["status"], "INVALID_STATUS")
    
    def test_invalid_agent_type(self):
        """Test handling of invalid agent type values."""
        # Create an agent with invalid type
        agent_with_invalid_type = self.coordinator_agent.copy()
        agent_with_invalid_type["type"] = "INVALID_TYPE"
        
        # Convert the agent
        agent_orchestrator_agent = CoordinatorToAgentAdapter.agent_to_agent_orchestrator(agent_with_invalid_type)
        
        # Verify the conversion (should default to CUSTOM)
        self.assertEqual(agent_orchestrator_agent["agent_type"], AgentType.CUSTOM)


if __name__ == "__main__":
    unittest.main()
