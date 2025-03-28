"""
Tests for the Tool Curator API endpoints.

This module contains tests for the Tool Curator API endpoints in the Tool Integration service.
"""

import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from httpx import AsyncClient

from shared.utils.tests.framework import (
    BaseAPITest,
    APITestHelper,
    MockUtils,
    AssertionUtils,
    test_app,
    test_client,
    async_client,
    tool_integration_db,
)

from shared.models.src.tool import (
    ToolRequirement,
    ToolStatus,
)

from ..src.main import app
from ..src.dependencies import get_tool_service
from ..src.services.tool_service import ToolService
from ..src.services.tool_curator.models import (
    ToolMatchScore,
    ToolRecommendation,
    ToolCapabilityMatch,
    ToolCompatibilityResult,
    ToolVersion,
    ToolVersionStatus,
    ToolCurationResult,
    ToolUsageStatistics,
)


class TestToolCuratorAPI(BaseAPITest):
    """Test cases for Tool Curator API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock tool service
        self.mock_tool_service = MockUtils.create_async_mock(spec=ToolService)
        
        # Override dependency
        app.dependency_overrides[get_tool_service] = lambda: self.mock_tool_service
    
    def teardown_method(self):
        """Tear down test fixtures."""
        # Clear dependency overrides
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_recommend_tools(self, async_client):
        """Test recommend_tools endpoint."""
        # Arrange
        req_id1 = str(uuid.uuid4())
        req_id2 = str(uuid.uuid4())
        
        # Create request data
        request_data = {
            "requirements": [
                {"id": req_id1, "description": "Requirement 1"},
                {"id": req_id2, "description": "Requirement 2"},
            ],
            "context": {"project_id": str(uuid.uuid4())},
            "min_score": 0.5,
            "max_recommendations": 3,
        }
        
        # Mock tool service
        recommendations = {
            req_id1: [
                ToolRecommendation(
                    tool_id=uuid.uuid4(),
                    requirement_id=uuid.UUID(req_id1),
                    score=0.8,
                    reason="Good match",
                ),
            ],
            req_id2: [
                ToolRecommendation(
                    tool_id=uuid.uuid4(),
                    requirement_id=uuid.UUID(req_id2),
                    score=0.7,
                    reason="Good match",
                ),
            ],
        }
        self.mock_tool_service.curator.recommend_tools_for_requirements.return_value = recommendations
        
        # Act
        response = await async_client.post("/api/v1/tools/recommend", json=request_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert req_id1 in response_data
        assert req_id2 in response_data
        assert len(response_data[req_id1]) == 1
        assert len(response_data[req_id2]) == 1
        assert response_data[req_id1][0]["score"] == 0.8
        assert response_data[req_id2][0]["score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_discover_tools(self, async_client):
        """Test discover_tools endpoint."""
        # Arrange
        req_id1 = str(uuid.uuid4())
        req_id2 = str(uuid.uuid4())
        
        # Create request data
        request_data = {
            "requirements": [
                {"id": req_id1, "description": "Requirement 1"},
                {"id": req_id2, "description": "Requirement 2"},
            ],
            "context": {"project_id": str(uuid.uuid4())},
        }
        
        # Mock tool service
        discovered_tools = [
            {"name": "Tool 1", "capability": "Capability 1", "source": "INTERNAL"},
            {"name": "Tool 2", "capability": "Capability 2", "source": "EXTERNAL"},
        ]
        self.mock_tool_service.curator.discover_tools_for_requirements.return_value = discovered_tools
        
        # Act
        response = await async_client.post("/api/v1/tools/discover", json=request_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["name"] == "Tool 1"
        assert response_data[1]["name"] == "Tool 2"
    
    @pytest.mark.asyncio
    async def test_evaluate_tool(self, async_client):
        """Test evaluate_tool endpoint."""
        # Arrange
        tool_id = str(uuid.uuid4())
        
        # Create request data
        request_data = {
            "requirements": ["Requirement 1", "Requirement 2"],
        }
        
        # Mock tool service
        capability_matches = [
            ToolCapabilityMatch(
                tool_id=uuid.UUID(tool_id),
                requirement="Requirement 1",
                capability="Capability",
                score=0.8,
            ),
        ]
        self.mock_tool_service.curator.evaluate_tool_capabilities.return_value = capability_matches
        
        # Act
        response = await async_client.post(f"/api/v1/tools/{tool_id}/evaluate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 1
        assert response_data[0]["requirement"] == "Requirement 1"
        assert response_data[0]["score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_track_tool_version(self, async_client):
        """Test track_tool_version endpoint."""
        # Arrange
        tool_id = str(uuid.uuid4())
        
        # Create request data
        request_data = {
            "version_number": "1.0.0",
            "status": "CURRENT",
            "release_notes": "Release notes",
            "changes": ["Change 1", "Change 2"],
            "compatibility": {"min_version": "0.5.0"},
            "created_by": "user1",
        }
        
        # Mock tool service
        version = ToolVersion(
            tool_id=uuid.UUID(tool_id),
            version_number=request_data["version_number"],
            status=ToolVersionStatus.CURRENT,
            release_notes=request_data["release_notes"],
            changes=request_data["changes"],
            compatibility=request_data["compatibility"],
            created_by=request_data["created_by"],
            created_at=datetime.now(),
        )
        self.mock_tool_service.curator.track_tool_version.return_value = version
        
        # Act
        response = await async_client.post(f"/api/v1/tools/{tool_id}/versions", json=request_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["tool_id"] == tool_id
        assert response_data["version_number"] == request_data["version_number"]
        assert response_data["status"] == request_data["status"]
    
    @pytest.mark.asyncio
    async def test_check_tool_compatibility(self, async_client):
        """Test check_tool_compatibility endpoint."""
        # Arrange
        tool_id = str(uuid.uuid4())
        version1 = "1.0.0"
        version2 = "2.0.0"
        
        # Mock tool service
        compatibility_info = {
            "is_compatible": True,
            "compatibility_level": "FULL",
            "breaking_changes": [],
            "notes": "Fully compatible",
        }
        self.mock_tool_service.curator.check_tool_compatibility.return_value = compatibility_info
        
        # Act
        response = await async_client.get(
            f"/api/v1/tools/{tool_id}/compatibility",
            params={"version1": version1, "version2": version2},
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_compatible"] is True
        assert response_data["compatibility_level"] == "FULL"
    
    @pytest.mark.asyncio
    async def test_curate_tools_for_agent(self, async_client):
        """Test curate_tools_for_agent endpoint."""
        # Arrange
        agent_id = str(uuid.uuid4())
        req_id1 = str(uuid.uuid4())
        req_id2 = str(uuid.uuid4())
        
        # Create request data
        request_data = {
            "requirements": [
                {"id": req_id1, "description": "Requirement 1"},
                {"id": req_id2, "description": "Requirement 2"},
            ],
            "context": {"project_id": str(uuid.uuid4())},
        }
        
        # Mock tool service
        recommendations = [
            ToolRecommendation(
                tool_id=uuid.uuid4(),
                requirement_id=uuid.UUID(req_id1),
                score=0.8,
                reason="Good match",
            ),
            ToolRecommendation(
                tool_id=uuid.uuid4(),
                requirement_id=uuid.UUID(req_id2),
                score=0.7,
                reason="Good match",
            ),
        ]
        self.mock_tool_service.curator.curate_tools_for_agent.return_value = recommendations
        
        # Act
        response = await async_client.post(f"/api/v1/agents/{agent_id}/tools/curate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["score"] == 0.8
        assert response_data[1]["score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_get_tool_usage_statistics(self, async_client):
        """Test get_tool_usage_statistics endpoint."""
        # Arrange
        tool_id = str(uuid.uuid4())
        
        # Mock tool service
        statistics = ToolUsageStatistics(
            tool_id=uuid.UUID(tool_id),
            total_executions=100,
            successful_executions=90,
            failed_executions=10,
            average_execution_time=0.5,
            last_execution_time=datetime.now(),
            usage_by_agent={},
            usage_by_project={},
        )
        self.mock_tool_service.curator.get_tool_usage_statistics.return_value = statistics
        
        # Act
        response = await async_client.get(f"/api/v1/tools/{tool_id}/usage")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["tool_id"] == tool_id
        assert response_data["total_executions"] == 100
        assert response_data["successful_executions"] == 90
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation(self, async_client):
        """Test perform_curation_operation endpoint."""
        # Arrange
        tool_id = str(uuid.uuid4())
        operation = "approve"
        
        # Create request data
        request_data = {
            "operation": operation,
            "parameters": {},
            "performed_by": "user1",
        }
        
        # Mock tool service
        result = ToolCurationResult(
            tool_id=uuid.UUID(tool_id),
            operation=operation,
            success=True,
            performed_by="user1",
            performed_at=datetime.now(),
            details={},
        )
        self.mock_tool_service.curator.perform_curation_operation.return_value = result
        
        # Act
        response = await async_client.post(f"/api/v1/tools/{tool_id}/curate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["tool_id"] == tool_id
        assert response_data["operation"] == operation
        assert response_data["success"] is True
        assert response_data["performed_by"] == "user1"


class TestToolCuratorAPIIntegration:
    """Integration tests for Tool Curator API endpoints."""
    
    @pytest.mark.asyncio
    async def test_recommend_tools_integration(self, tool_integration_db, async_client):
        """Test recommend_tools endpoint with database integration."""
        # This test would use the actual database session and repository
        # For now, we'll just demonstrate the pattern
        pass
    
    @pytest.mark.asyncio
    async def test_discover_tools_integration(self, tool_integration_db, async_client):
        """Test discover_tools endpoint with database integration."""
        # This test would use the actual database session and repository
        # For now, we'll just demonstrate the pattern
        pass
