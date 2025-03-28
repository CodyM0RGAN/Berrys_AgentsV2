"""
Tests for the ProjectCoordinatorClient class.

This module contains tests for the ProjectCoordinatorClient class in
shared/utils/src/clients/project_coordinator.py.
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.utils.src.clients.project_coordinator import ProjectCoordinatorClient
from shared.utils.src.exceptions import ServiceUnavailableError, MaxRetriesExceededError


class TestProjectCoordinatorClient(unittest.TestCase):
    """Test cases for ProjectCoordinatorClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "http://project-coordinator:8000"
        self.client = ProjectCoordinatorClient(base_url=self.base_url)
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.get")
    def test_get_projects(self, mock_get):
        """Test get_projects method."""
        # Mock response
        mock_get.return_value = {
            "items": [
                {"id": "1", "name": "Project 1"},
                {"id": "2", "name": "Project 2"}
            ],
            "total": 2,
            "page": 1,
            "per_page": 10
        }
        
        # Call get_projects
        result = self.client.get_projects(
            search="test",
            status="PLANNING",
            sort="name",
            page=2,
            per_page=5
        )
        
        # Verify get was called with correct parameters
        mock_get.assert_called_once_with(
            "/projects",
            params={
                "search": "test",
                "status": "PLANNING",
                "sort": "name",
                "page": 2,
                "per_page": 5
            }
        )
        
        # Verify result
        self.assertEqual(result["items"][0]["name"], "Project 1")
        self.assertEqual(result["items"][1]["name"], "Project 2")
        self.assertEqual(result["total"], 2)
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.get")
    def test_get_project(self, mock_get):
        """Test get_project method."""
        # Mock response
        mock_get.return_value = {
            "id": "1",
            "name": "Project 1",
            "description": "Test project",
            "status": "PLANNING"
        }
        
        # Call get_project
        result = self.client.get_project("1")
        
        # Verify get was called with correct parameters
        mock_get.assert_called_once_with("/projects/1")
        
        # Verify result
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["name"], "Project 1")
        self.assertEqual(result["status"], "PLANNING")
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.post")
    async def test_create_project_success(self, mock_post, mock_retry):
        """Test create_project method with successful response."""
        # Mock response
        mock_post.return_value = {
            "id": "1",
            "name": "Test Project",
            "description": "Test description",
            "status": "PLANNING"
        }
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call create_project
        result = await self.client.create_project(
            name="Test Project",
            description="Test description",
            metadata={"key": "value"}
        )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify post was called with correct parameters
        mock_post.assert_called_once_with(
            "/projects",
            data={
                "name": "Test Project",
                "description": "Test description",
                "metadata": {"key": "value"}
            }
        )
        
        # Verify result
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["name"], "Test Project")
        self.assertEqual(result["status"], "PLANNING")
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    async def test_create_project_retry_failure(self, mock_retry):
        """Test create_project method with retry failure."""
        # Configure mock_retry to raise MaxRetriesExceededError
        mock_retry.side_effect = MaxRetriesExceededError(
            attempts=3,
            last_error=ServiceUnavailableError("Service unavailable")
        )
        
        # Call create_project and verify it raises MaxRetriesExceededError
        with self.assertRaises(MaxRetriesExceededError):
            await self.client.create_project(
                name="Test Project",
                description="Test description"
            )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.put")
    async def test_update_project_success(self, mock_put, mock_retry):
        """Test update_project method with successful response."""
        # Mock response
        mock_put.return_value = {
            "id": "1",
            "name": "Updated Project",
            "description": "Updated description",
            "status": "DEVELOPMENT"
        }
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call update_project
        result = await self.client.update_project(
            project_id="1",
            name="Updated Project",
            description="Updated description",
            status="DEVELOPMENT",
            metadata={"key": "value"}
        )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify put was called with correct parameters
        mock_put.assert_called_once_with(
            "/projects/1",
            data={
                "name": "Updated Project",
                "description": "Updated description",
                "status": "DEVELOPMENT",
                "metadata": {"key": "value"}
            }
        )
        
        # Verify result
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["name"], "Updated Project")
        self.assertEqual(result["status"], "DEVELOPMENT")
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    async def test_update_project_retry_failure(self, mock_retry):
        """Test update_project method with retry failure."""
        # Configure mock_retry to raise MaxRetriesExceededError
        mock_retry.side_effect = MaxRetriesExceededError(
            attempts=3,
            last_error=ServiceUnavailableError("Service unavailable")
        )
        
        # Call update_project and verify it raises MaxRetriesExceededError
        with self.assertRaises(MaxRetriesExceededError):
            await self.client.update_project(
                project_id="1",
                name="Updated Project"
            )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.delete")
    async def test_delete_project_success(self, mock_delete, mock_retry):
        """Test delete_project method with successful response."""
        # Mock response
        mock_delete.return_value = {"success": True}
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call delete_project
        result = await self.client.delete_project("1")
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify delete was called with correct parameters
        mock_delete.assert_called_once_with("/projects/1")
        
        # Verify result
        self.assertEqual(result["success"], True)
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    async def test_delete_project_retry_failure(self, mock_retry):
        """Test delete_project method with retry failure."""
        # Configure mock_retry to raise MaxRetriesExceededError
        mock_retry.side_effect = MaxRetriesExceededError(
            attempts=2,  # Fewer retries for deletion operations
            last_error=ServiceUnavailableError("Service unavailable")
        )
        
        # Call delete_project and verify it raises MaxRetriesExceededError
        with self.assertRaises(MaxRetriesExceededError):
            await self.client.delete_project("1")
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.get")
    def test_get_project_tasks(self, mock_get):
        """Test get_project_tasks method."""
        # Mock response
        mock_get.return_value = {
            "items": [
                {"id": "1", "name": "Task 1", "status": "TODO"},
                {"id": "2", "name": "Task 2", "status": "IN_PROGRESS"}
            ],
            "total": 2
        }
        
        # Call get_project_tasks
        result = self.client.get_project_tasks("1")
        
        # Verify get was called with correct parameters
        mock_get.assert_called_once_with("/projects/1/tasks")
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Task 1")
        self.assertEqual(result[1]["name"], "Task 2")
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.get")
    def test_get_project_agents(self, mock_get):
        """Test get_project_agents method."""
        # Mock response
        mock_get.return_value = {
            "items": [
                {"id": "1", "name": "Agent 1", "role": "DEVELOPER"},
                {"id": "2", "name": "Agent 2", "role": "TESTER"}
            ],
            "total": 2
        }
        
        # Call get_project_agents
        result = self.client.get_project_agents("1")
        
        # Verify get was called with correct parameters
        mock_get.assert_called_once_with("/projects/1/agents")
        
        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Agent 1")
        self.assertEqual(result[1]["name"], "Agent 2")
    
    @patch("shared.utils.src.clients.base.BaseAPIClient.get")
    def test_get_project_activities(self, mock_get):
        """Test get_project_activities method."""
        # Mock response
        mock_get.return_value = {
            "items": [
                {"id": "1", "type": "CREATE", "timestamp": "2025-03-27T12:00:00Z"},
                {"id": "2", "type": "UPDATE", "timestamp": "2025-03-27T13:00:00Z"}
            ],
            "total": 2,
            "page": 1,
            "per_page": 10
        }
        
        # Call get_project_activities
        result = self.client.get_project_activities("1", page=2, per_page=5)
        
        # Verify get was called with correct parameters
        mock_get.assert_called_once_with(
            "/projects/1/activities",
            params={"page": 2, "per_page": 5}
        )
        
        # Verify result
        self.assertEqual(result["items"][0]["type"], "CREATE")
        self.assertEqual(result["items"][1]["type"], "UPDATE")
        self.assertEqual(result["total"], 2)
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.post")
    async def test_assign_agent_to_project_success(self, mock_post, mock_retry):
        """Test assign_agent_to_project method with successful response."""
        # Mock response
        mock_post.return_value = {
            "project_id": "1",
            "agent_id": "2",
            "role": "DEVELOPER",
            "assigned_at": "2025-03-27T12:00:00Z"
        }
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call assign_agent_to_project
        result = await self.client.assign_agent_to_project(
            project_id="1",
            agent_id="2",
            role="DEVELOPER"
        )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify post was called with correct parameters
        mock_post.assert_called_once_with(
            "/projects/1/agents",
            data={"agent_id": "2", "role": "DEVELOPER"}
        )
        
        # Verify result
        self.assertEqual(result["project_id"], "1")
        self.assertEqual(result["agent_id"], "2")
        self.assertEqual(result["role"], "DEVELOPER")
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.delete")
    async def test_remove_agent_from_project_success(self, mock_delete, mock_retry):
        """Test remove_agent_from_project method with successful response."""
        # Mock response
        mock_delete.return_value = {"success": True}
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call remove_agent_from_project
        result = await self.client.remove_agent_from_project(
            project_id="1",
            agent_id="2"
        )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify delete was called with correct parameters
        mock_delete.assert_called_once_with("/projects/1/agents/2")
        
        # Verify result
        self.assertEqual(result["success"], True)
    
    @patch("shared.utils.src.retry.retry_with_backoff")
    @patch("shared.utils.src.clients.base.BaseAPIClient.post")
    async def test_send_chat_message_success(self, mock_post, mock_retry):
        """Test send_chat_message method with successful response."""
        # Mock response
        mock_post.return_value = {
            "message_id": "1",
            "response": "Hello, how can I help you?",
            "timestamp": "2025-03-27T12:00:00Z"
        }
        
        # Configure mock_retry to call the operation function
        async def side_effect(operation, policy, operation_name):
            return await operation()
        
        mock_retry.side_effect = side_effect
        
        # Call send_chat_message
        result = await self.client.send_chat_message(
            message="Hello",
            session_id="session-123",
            user_id="user-456",
            history=[
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        )
        
        # Verify retry_with_backoff was called
        mock_retry.assert_called_once()
        
        # Verify post was called with correct parameters
        mock_post.assert_called_once_with(
            "/chat/message",
            data={
                "message": "Hello",
                "session_id": "session-123",
                "user_id": "user-456",
                "history": [
                    {"role": "user", "content": "Previous message"},
                    {"role": "assistant", "content": "Previous response"}
                ]
            }
        )
        
        # Verify result
        self.assertEqual(result["message_id"], "1")
        self.assertEqual(result["response"], "Hello, how can I help you?")


if __name__ == "__main__":
    unittest.main()
