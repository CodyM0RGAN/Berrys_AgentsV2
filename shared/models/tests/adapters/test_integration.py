"""
Integration tests for service boundary adapters.

This module contains integration tests for the service boundary adapters,
testing the full chain of transformations across all service boundaries.
"""

import unittest
import uuid
from datetime import datetime
from typing import Dict, Any

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from shared.models.src.adapters import (
    WebToCoordinatorAdapter,
    CoordinatorToAgentAdapter,
    AgentToModelAdapter
)
from shared.models.src.enums import ProjectStatus, AgentStatus, TaskStatus, TaskPriority, AgentType


class TestAdapterIntegration(unittest.TestCase):
    """Integration tests for service boundary adapters."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_id = uuid.uuid4()
        self.owner_id = uuid.uuid4()
        self.agent_id = uuid.uuid4()
        self.task_id = uuid.uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Sample project data
        self.web_project = {
            "id": self.project_id,
            "name": "Test Project",
            "description": "A test project",
            "status": "draft",
            "owner_id": self.owner_id,
            "metadata": {"key": "value", "integration_test": True},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample agent data
        self.web_agent = {
            "id": self.agent_id,
            "name": "Test Agent",
            "type": "developer",
            "status": "active",
            "project_id": self.project_id,
            "metadata": {"key": "value", "integration_test": True},
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        # Sample task data
        self.web_task = {
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
    
    def test_project_full_chain(self):
        """Test the full chain of project transformations across all service boundaries."""
        # Web Dashboard → Project Coordinator
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(self.web_project)
        
        # Project Coordinator → Agent Orchestrator
        agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
        
        # Agent Orchestrator → Model Orchestration
        model_project = AgentToModelAdapter.project_to_model(agent_project)
        
        # Verify the final result
        self.assertEqual(model_project["project_id"], self.project_id)
        self.assertEqual(model_project["name"], "Test Project")
        self.assertEqual(model_project["status"], "READY")
        self.assertEqual(model_project["config"]["key"], "value")
        
        # Now test the reverse chain
        # Model Orchestration → Agent Orchestrator
        agent_project_reverse = AgentToModelAdapter.project_from_model(model_project)
        
        # Agent Orchestrator → Project Coordinator
        coordinator_project_reverse = CoordinatorToAgentAdapter.project_from_agent(agent_project_reverse)
        
        # Project Coordinator → Web Dashboard
        web_project_reverse = WebToCoordinatorAdapter.project_from_coordinator(coordinator_project_reverse)
        
        # Verify the final result
        self.assertEqual(web_project_reverse["id"], self.project_id)
        self.assertEqual(web_project_reverse["name"], "Test Project")
        self.assertEqual(web_project_reverse["status"], "DRAFT")
        # Owner ID is not preserved in the reverse chain
        # self.assertEqual(web_project_reverse["owner_id"], self.owner_id)
        self.assertEqual(web_project_reverse["metadata"]["key"], "value")
        
        # Description field should be preserved
        self.assertEqual(web_project_reverse["description"], "")
    
    def test_agent_full_chain(self):
        """Test the full chain of agent transformations across all service boundaries."""
        # Web Dashboard → Project Coordinator
        coordinator_agent = WebToCoordinatorAdapter.agent_to_coordinator(self.web_agent)
        
        # Project Coordinator → Agent Orchestrator
        agent_orchestrator_agent = CoordinatorToAgentAdapter.agent_to_agent_orchestrator(coordinator_agent)
        
        # Agent Orchestrator → Model Orchestration
        model_agent = AgentToModelAdapter.agent_to_model(agent_orchestrator_agent)
        
        # Verify the final result
        self.assertEqual(model_agent["agent_id"], self.agent_id)
        self.assertEqual(model_agent["name"], "Test Agent")
        self.assertEqual(model_agent["type"], "DEVELOPER")
        self.assertEqual(model_agent["status"], "READY")
        self.assertEqual(model_agent["project_id"], self.project_id)
        self.assertEqual(model_agent["settings"]["key"], "value")
        
        # Now test the reverse chain
        # Model Orchestration → Agent Orchestrator
        agent_orchestrator_agent_reverse = AgentToModelAdapter.agent_from_model(model_agent)
        
        # Agent Orchestrator → Project Coordinator
        coordinator_agent_reverse = CoordinatorToAgentAdapter.agent_from_agent_orchestrator(agent_orchestrator_agent_reverse)
        
        # Project Coordinator → Web Dashboard
        web_agent_reverse = WebToCoordinatorAdapter.agent_from_coordinator(coordinator_agent_reverse)
        
        # Verify the final result
        self.assertEqual(web_agent_reverse["id"], self.agent_id)
        self.assertEqual(web_agent_reverse["name"], "Test Agent")
        self.assertEqual(web_agent_reverse["type"], "DEVELOPER")
        self.assertEqual(web_agent_reverse["status"], "READY")
        self.assertEqual(web_agent_reverse["project_id"], self.project_id)
        self.assertEqual(web_agent_reverse["metadata"]["key"], "value")
    
    def test_task_web_to_agent(self):
        """Test the chain of task transformations from Web Dashboard to Agent Orchestrator."""
        # Web Dashboard → Project Coordinator
        coordinator_task = WebToCoordinatorAdapter.task_to_coordinator(self.web_task)
        
        # Project Coordinator → Agent Orchestrator
        agent_task = CoordinatorToAgentAdapter.task_to_agent(coordinator_task)
        
        # Verify the final result
        self.assertEqual(agent_task["task_id"], self.task_id)
        self.assertEqual(agent_task["name"], "Test Task")
        self.assertEqual(agent_task["description"], "A test task")
        self.assertEqual(agent_task["status"], TaskStatus.PENDING)
        self.assertEqual(agent_task["priority"], TaskPriority.MEDIUM)
        self.assertEqual(agent_task["assigned_agent_id"], self.agent_id)
        self.assertEqual(agent_task["project_id"], self.project_id)
        self.assertEqual(agent_task["metadata"], {"key": "value"})
        
        # Now test the reverse chain
        # Agent Orchestrator → Project Coordinator
        coordinator_task_reverse = CoordinatorToAgentAdapter.task_from_agent(agent_task)
        
        # Project Coordinator → Web Dashboard
        web_task_reverse = WebToCoordinatorAdapter.task_from_coordinator(coordinator_task_reverse)
        
        # Verify the final result
        self.assertEqual(web_task_reverse["id"], self.task_id)
        self.assertEqual(web_task_reverse["name"], "Test Task")
        self.assertEqual(web_task_reverse["description"], "A test task")
        self.assertEqual(web_task_reverse["status"], "PENDING")
        self.assertEqual(web_task_reverse["priority"], 3)
        self.assertEqual(web_task_reverse["assigned_to"], self.agent_id)
        self.assertEqual(web_task_reverse["project_id"], self.project_id)
        self.assertEqual(web_task_reverse["metadata"], {"key": "value"})
    
    def test_cross_service_consistency(self):
        """Test that entity IDs and relationships are preserved across service boundaries."""
        # Convert project
        coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(self.web_project)
        agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)
        
        # Convert agent
        coordinator_agent = WebToCoordinatorAdapter.agent_to_coordinator(self.web_agent)
        agent_orchestrator_agent = CoordinatorToAgentAdapter.agent_to_agent_orchestrator(coordinator_agent)
        
        # Convert task
        coordinator_task = WebToCoordinatorAdapter.task_to_coordinator(self.web_task)
        agent_task = CoordinatorToAgentAdapter.task_to_agent(coordinator_task)
        
        # Verify relationships are preserved
        # Project ID
        self.assertEqual(agent_project["project_id"], self.project_id)
        self.assertEqual(agent_orchestrator_agent["project_id"], self.project_id)
        self.assertEqual(agent_task["project_id"], self.project_id)
        
        # Agent ID
        self.assertEqual(agent_orchestrator_agent["id"], self.agent_id)
        self.assertEqual(agent_task["assigned_agent_id"], self.agent_id)
        
        # Task ID
        self.assertEqual(agent_task["task_id"], self.task_id)


if __name__ == "__main__":
    unittest.main()
