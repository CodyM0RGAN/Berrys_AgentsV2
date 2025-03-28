"""
Tests for the WebToCoordinatorAdapter.

This module contains tests for the WebToCoordinatorAdapter, which converts
entities between the Web Dashboard and Project Coordinator service representations.
"""

import unittest
import uuid
from datetime import datetime
from typing import Dict, Any

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from shared.models.src.adapters import WebToCoordinatorAdapter
from shared.models.src.adapters.exceptions import AdapterValidationError, EntityConversionError
from shared.models.src.enums import AgentStatus, TaskStatus, TaskPriority, AgentType
from shared.models.src.project import Project as ProjectPydantic, ProjectStatus
from shared.models.src.agent import Agent as AgentPydantic
from shared.models.src.task import Task as TaskPydantic


class TestWebToCoordinatorAdapter(unittest.TestCase):
    """Tests for the WebToCoordinatorAdapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_id = uuid.uuid4()
        self.owner_id = uuid.uuid4()
        self.agent_id = uuid.uuid4()
        self.task_id = uuid.uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Sample project data
        self.web_project_dict = {
            "id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": "DRAFT",
            "owner_id": self.owner_id,
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        self.web_project_pydantic = ProjectPydantic(
            id=self.project_id,
            name="Test Project",
            description="A test project",
            status=ProjectStatus.DRAFT,
            owner_id=self.owner_id,
            metadata={"key": "value"},
            created_at=self.created_at,
            updated_at=self.updated_at
        )
        
        # Sample agent data
        self.web_agent_dict = {
            "id": self.agent_id,
            "name": "Test Agent",
            "type": "developer",
            "status": "active",
            "project_id": self.project_id,
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample task data
        self.web_task_dict = {
            "id": self.task_id,
            "name": "Test Task",
            "description": "A test task",
            "status": "pending",
            "priority": 3,
            "assigned_to": self.agent_id,
            "project_id": self.project_id,
            "metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def test_project_to_coordinator_dict(self):
        """Test converting a Web Dashboard project dictionary to a Project Coordinator project."""
        # Convert the project
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(self.web_project_dict)
        
        # Verify the conversion
        self.assertEqual(coordinator_project["id"], self.project_id)
        self.assertEqual(coordinator_project["name"], "Test Project")
        self.assertEqual(coordinator_project["description"], "A test project")
        self.assertEqual(coordinator_project["status"], ProjectStatus.DRAFT)
        self.assertEqual(coordinator_project["owner_id"], self.owner_id)
        self.assertEqual(coordinator_project["project_metadata"], {"key": "value"})
    
    def test_project_to_coordinator_pydantic(self):
        """Test converting a Web Dashboard project Pydantic model to a Project Coordinator project."""
        # Convert the project
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(self.web_project_pydantic)
        
        # Verify the conversion
        self.assertEqual(coordinator_project["id"], self.project_id)
        self.assertEqual(coordinator_project["name"], "Test Project")
        self.assertEqual(coordinator_project["description"], "A test project")
        self.assertEqual(coordinator_project["status"], ProjectStatus.DRAFT)
        self.assertEqual(coordinator_project["owner_id"], self.owner_id)
        self.assertEqual(coordinator_project["project_metadata"], {"key": "value"})
    
    def test_project_from_coordinator(self):
        """Test converting a Project Coordinator project to a Web Dashboard project."""
        # Create a Project Coordinator project
        coordinator_project = {
            "id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": ProjectStatus.DRAFT,
            "owner_id": self.owner_id,
            "project_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the project
        web_project = WebToCoordinatorAdapter.project_from_coordinator(coordinator_project)
        
        # Verify the conversion
        self.assertEqual(web_project["id"], self.project_id)
        self.assertEqual(web_project["name"], "Test Project")
        self.assertEqual(web_project["description"], "A test project")
        self.assertEqual(web_project["status"], "DRAFT")
        self.assertEqual(web_project["owner_id"], self.owner_id)
        self.assertEqual(web_project["metadata"], {"key": "value"})
    
    def test_agent_to_coordinator(self):
        """Test converting a Web Dashboard agent to a Project Coordinator agent."""
        # Convert the agent
        coordinator_agent = WebToCoordinatorAdapter.agent_to_coordinator(self.web_agent_dict)
        
        # Verify the conversion
        self.assertEqual(coordinator_agent["id"], self.agent_id)
        self.assertEqual(coordinator_agent["name"], "Test Agent")
        self.assertEqual(coordinator_agent["type"], "DEVELOPER")
        self.assertEqual(coordinator_agent["status"], AgentStatus.ACTIVE)
        self.assertEqual(coordinator_agent["project_id"], self.project_id)
        self.assertEqual(coordinator_agent["agent_metadata"], {"key": "value"})
    
    def test_agent_from_coordinator(self):
        """Test converting a Project Coordinator agent to a Web Dashboard agent."""
        # Create a Project Coordinator agent
        coordinator_agent = {
            "id": self.agent_id,
            "name": "Test Agent",
            "type": "DEVELOPER",
            "status": AgentStatus.ACTIVE,
            "project_id": self.project_id,
            "agent_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the agent
        web_agent = WebToCoordinatorAdapter.agent_from_coordinator(coordinator_agent)
        
        # Verify the conversion
        self.assertEqual(web_agent["id"], self.agent_id)
        self.assertEqual(web_agent["name"], "Test Agent")
        self.assertEqual(web_agent["type"], "DEVELOPER")
        self.assertEqual(web_agent["status"], "ACTIVE")
        self.assertEqual(web_agent["project_id"], self.project_id)
        self.assertEqual(web_agent["metadata"], {"key": "value"})
    
    def test_task_to_coordinator(self):
        """Test converting a Web Dashboard task to a Project Coordinator task."""
        # Convert the task
        coordinator_task = WebToCoordinatorAdapter.task_to_coordinator(self.web_task_dict)
        
        # Verify the conversion
        self.assertEqual(coordinator_task["id"], self.task_id)
        self.assertEqual(coordinator_task["name"], "Test Task")
        self.assertEqual(coordinator_task["description"], "A test task")
        self.assertEqual(coordinator_task["status"], TaskStatus.PENDING)
        self.assertEqual(coordinator_task["priority"], TaskPriority.MEDIUM)
        self.assertEqual(coordinator_task["agent_id"], self.agent_id)
        self.assertEqual(coordinator_task["project_id"], self.project_id)
        self.assertEqual(coordinator_task["task_metadata"], {"key": "value"})
    
    def test_task_from_coordinator(self):
        """Test converting a Project Coordinator task to a Web Dashboard task."""
        # Create a Project Coordinator task
        coordinator_task = {
            "id": self.task_id,
            "name": "Test Task",
            "description": "A test task",
            "status": TaskStatus.PENDING,
            "priority": TaskPriority.MEDIUM,
            "agent_id": self.agent_id,
            "project_id": self.project_id,
            "task_metadata": {"key": "value"},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Convert the task
        web_task = WebToCoordinatorAdapter.task_from_coordinator(coordinator_task)
        
        # Verify the conversion
        self.assertEqual(web_task["id"], self.task_id)
        self.assertEqual(web_task["name"], "Test Task")
        self.assertEqual(web_task["description"], "A test task")
        self.assertEqual(web_task["status"], "PENDING")
        self.assertEqual(web_task["priority"], 3)
        self.assertEqual(web_task["assigned_to"], self.agent_id)
        self.assertEqual(web_task["project_id"], self.project_id)
        self.assertEqual(web_task["metadata"], {"key": "value"})
    
    def test_invalid_input(self):
        """Test handling of invalid input."""
        # Test with None
        with self.assertRaises(AdapterValidationError):
            WebToCoordinatorAdapter.project_to_coordinator(None)
        
        # Test with non-dict, non-BaseModel
        with self.assertRaises(AdapterValidationError):
            WebToCoordinatorAdapter.project_to_coordinator("not a dict or model")
    
    def test_invalid_status(self):
        """Test handling of invalid status values."""
        # Create a project with invalid status
        project_with_invalid_status = self.web_project_dict.copy()
        project_with_invalid_status["status"] = "INVALID_STATUS"
        
        # Convert the project
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(project_with_invalid_status)
        
        # Verify the conversion (should default to DRAFT)
        self.assertEqual(coordinator_project["status"], ProjectStatus.DRAFT)


if __name__ == "__main__":
    unittest.main()
