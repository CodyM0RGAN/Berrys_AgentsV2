"""
Tests for the Tool Curator component.

This module contains tests for the Tool Curator component in the Tool Integration service.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from shared.utils.tests.framework import (
    BaseAsyncTest,
    BaseServiceTest,
    MockUtils,
    AssertionUtils,
    db_session,
    tool_integration_db,
)

from shared.models.src.tool import (
    ToolRequirement,
    ToolStatus,
)

from ..src.services.tool_curator.service import ToolCuratorService
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
from ..src.services.tool_curator.recommendation import RecommendationEngine
from ..src.services.tool_curator.versioning import ToolVersioningService


class TestToolCuratorService(BaseServiceTest):
    """Test cases for ToolCuratorService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock dependencies
        self.mock_repository = MockUtils.create_async_mock()
        self.mock_registry = MockUtils.create_async_mock()
        self.mock_discovery_service = MockUtils.create_async_mock()
        self.mock_evaluation_service = MockUtils.create_async_mock()
        self.mock_recommendation_engine = MockUtils.create_mock()
        self.mock_versioning_service = MockUtils.create_mock()
        
        # Create service
        self.service = ToolCuratorService(
            repository=self.mock_repository,
            registry=self.mock_registry,
            discovery_service=self.mock_discovery_service,
            evaluation_service=self.mock_evaluation_service,
            recommendation_engine=self.mock_recommendation_engine,
            versioning_service=self.mock_versioning_service,
        )
    
    @pytest.mark.asyncio
    async def test_discover_tools_for_requirements(self):
        """Test discovering tools for requirements."""
        # Arrange
        requirements = [
            ToolRequirement(id=uuid.uuid4(), description="Requirement 1"),
            ToolRequirement(id=uuid.uuid4(), description="Requirement 2"),
        ]
        context = {"project_id": str(uuid.uuid4())}
        
        # Mock discovery service
        discovered_tools = [
            {"name": "Tool 1", "capability": "Capability 1", "source": "INTERNAL"},
            {"name": "Tool 2", "capability": "Capability 2", "source": "EXTERNAL"},
        ]
        self.mock_discovery_service.discover_tools.return_value = discovered_tools
        
        # Act
        result = await self.service.discover_tools_for_requirements(requirements, context)
        
        # Assert
        self.mock_discovery_service.discover_tools.assert_called_once_with(
            ["Requirement 1", "Requirement 2"],
            context,
            None,
        )
        assert result == discovered_tools
    
    @pytest.mark.asyncio
    async def test_evaluate_tool_capabilities(self):
        """Test evaluating tool capabilities."""
        # Arrange
        tool_id = uuid.uuid4()
        requirements = ["Requirement 1", "Requirement 2"]
        
        # Mock registry
        mock_tool = MagicMock()
        mock_tool.capability = "Capability"
        mock_tool.schema = {
            "description": "Schema description",
            "properties": {
                "prop1": {"description": "Property 1 description"},
                "prop2": {"description": "Property 2 description"},
            },
        }
        self.mock_registry.get_tool.return_value = mock_tool
        
        # Mock recommendation engine
        capability_matches = [
            ToolCapabilityMatch(
                tool_id=tool_id,
                requirement="Requirement 1",
                capability="Capability",
                score=0.8,
            ),
        ]
        self.mock_recommendation_engine.match_tool_capabilities.return_value = capability_matches
        
        # Act
        result = await self.service.evaluate_tool_capabilities(tool_id, requirements)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        self.mock_recommendation_engine.match_tool_capabilities.assert_called_once_with(
            ["Capability", "Schema description", "Property 1 description", "Property 2 description"],
            requirements,
            tool_id,
        )
        assert result == capability_matches
    
    @pytest.mark.asyncio
    async def test_recommend_tools_for_requirements(self):
        """Test recommending tools for requirements."""
        # Arrange
        requirements = [
            ToolRequirement(id=uuid.uuid4(), description="Requirement 1"),
            ToolRequirement(id=uuid.uuid4(), description="Requirement 2"),
        ]
        context = {"project_id": str(uuid.uuid4())}
        min_score = 0.5
        max_recommendations = 3
        
        # Mock registry
        mock_tools = [MagicMock(), MagicMock()]
        self.mock_registry.list_tools.return_value = (mock_tools, 2)
        
        # Mock recommendation engine
        capability_matches = [
            ToolCapabilityMatch(
                tool_id=uuid.uuid4(),
                requirement="Requirement 1",
                capability="Capability",
                score=0.8,
            ),
        ]
        self.mock_recommendation_engine.match_tool_capabilities.return_value = capability_matches
        
        match_score = ToolMatchScore(
            tool_id=uuid.uuid4(),
            requirement_id=requirements[0].id,
            score=0.8,
            capability_score=0.8,
            compatibility_score=None,
            usage_score=None,
        )
        self.mock_recommendation_engine.calculate_tool_match_score.return_value = match_score
        
        recommendations = [
            ToolRecommendation(
                tool_id=uuid.uuid4(),
                requirement_id=requirements[0].id,
                score=0.8,
                reason="Good match",
            ),
        ]
        self.mock_recommendation_engine.generate_recommendations.return_value = recommendations
        
        # Act
        result = await self.service.recommend_tools_for_requirements(
            requirements,
            context,
            min_score,
            max_recommendations,
        )
        
        # Assert
        self.mock_registry.list_tools.assert_called_once_with(
            status=ToolStatus.APPROVED.value,
            page=1,
            page_size=100,
        )
        assert result == {requirements[0].id: recommendations}
    
    @pytest.mark.asyncio
    async def test_track_tool_version(self):
        """Test tracking tool version."""
        # Arrange
        tool_id = uuid.uuid4()
        version_number = "1.0.0"
        status = ToolVersionStatus.CURRENT
        release_notes = "Release notes"
        changes = ["Change 1", "Change 2"]
        compatibility = {"min_version": "0.5.0"}
        created_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Mock versioning service
        version = ToolVersion(
            tool_id=tool_id,
            version_number=version_number,
            status=status,
            release_notes=release_notes,
            changes=changes,
            compatibility=compatibility,
            created_by=created_by,
            created_at=datetime.now(),
        )
        self.mock_versioning_service.create_version.return_value = version
        
        # Act
        result = await self.service.track_tool_version(
            tool_id,
            version_number,
            status,
            release_notes,
            changes,
            compatibility,
            created_by,
        )
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        self.mock_versioning_service.create_version.assert_called_once_with(
            tool_id,
            version_number,
            status,
            release_notes,
            changes,
            compatibility,
            created_by,
        )
        assert result == version
    
    @pytest.mark.asyncio
    async def test_check_tool_compatibility(self):
        """Test checking tool compatibility."""
        # Arrange
        tool_id = uuid.uuid4()
        version1 = "1.0.0"
        version2 = "2.0.0"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Mock versioning service
        compatibility_info = {
            "is_compatible": True,
            "compatibility_level": "FULL",
            "breaking_changes": [],
            "notes": "Fully compatible",
        }
        self.mock_versioning_service.check_version_compatibility.return_value = compatibility_info
        
        # Act
        result = await self.service.check_tool_compatibility(tool_id, version1, version2)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        self.mock_versioning_service.check_version_compatibility.assert_called_once_with(
            tool_id,
            version1,
            version2,
        )
        assert result == compatibility_info
    
    @pytest.mark.asyncio
    async def test_curate_tools_for_agent(self):
        """Test curating tools for agent."""
        # Arrange
        agent_id = uuid.uuid4()
        requirements = [
            ToolRequirement(id=uuid.uuid4(), description="Requirement 1"),
            ToolRequirement(id=uuid.uuid4(), description="Requirement 2"),
        ]
        context = {"project_id": str(uuid.uuid4())}
        
        # Mock recommend_tools_for_requirements
        recommendations1 = [
            ToolRecommendation(
                tool_id=uuid.uuid4(),
                requirement_id=requirements[0].id,
                score=0.8,
                reason="Good match",
            ),
        ]
        recommendations2 = [
            ToolRecommendation(
                tool_id=uuid.uuid4(),
                requirement_id=requirements[1].id,
                score=0.7,
                reason="Good match",
            ),
        ]
        
        # Use patch to mock the method on the actual instance
        with patch.object(
            self.service,
            "recommend_tools_for_requirements",
            return_value={
                requirements[0].id: recommendations1,
                requirements[1].id: recommendations2,
            },
        ):
            # Act
            result = await self.service.curate_tools_for_agent(agent_id, requirements, context)
            
            # Assert
            assert len(result) == 2
            assert result[0].score >= result[1].score  # Should be sorted by score
    
    @pytest.mark.asyncio
    async def test_get_tool_usage_statistics(self):
        """Test getting tool usage statistics."""
        # Arrange
        tool_id = uuid.uuid4()
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Act
        result = await self.service.get_tool_usage_statistics(tool_id)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        assert result.tool_id == tool_id
        assert result.total_executions == 0  # Default value
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation_approve(self):
        """Test performing approve curation operation."""
        # Arrange
        tool_id = uuid.uuid4()
        operation = "approve"
        performed_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        self.mock_registry.approve_tool.return_value = MagicMock()
        
        # Act
        result = await self.service.perform_curation_operation(tool_id, operation, performed_by=performed_by)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        self.mock_registry.approve_tool.assert_called_once_with(tool_id)
        assert result.tool_id == tool_id
        assert result.operation == operation
        assert result.success is True
        assert result.performed_by == performed_by
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation_deprecate(self):
        """Test performing deprecate curation operation."""
        # Arrange
        tool_id = uuid.uuid4()
        operation = "deprecate"
        performed_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        self.mock_registry.deprecate_tool.return_value = MagicMock()
        
        # Act
        result = await self.service.perform_curation_operation(tool_id, operation, performed_by=performed_by)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        self.mock_registry.deprecate_tool.assert_called_once_with(tool_id)
        assert result.tool_id == tool_id
        assert result.operation == operation
        assert result.success is True
        assert result.performed_by == performed_by
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation_update_version(self):
        """Test performing update_version curation operation."""
        # Arrange
        tool_id = uuid.uuid4()
        operation = "update_version"
        parameters = {
            "version": "1.0.0",
            "release_notes": "Release notes",
            "changes": ["Change 1", "Change 2"],
        }
        performed_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Mock track_tool_version
        version = ToolVersion(
            tool_id=tool_id,
            version_number=parameters["version"],
            status=ToolVersionStatus.CURRENT,
            release_notes=parameters["release_notes"],
            changes=parameters["changes"],
            created_by=performed_by,
            created_at=datetime.now(),
        )
        
        # Use patch to mock the method on the actual instance
        with patch.object(
            self.service,
            "track_tool_version",
            return_value=version,
        ):
            # Act
            result = await self.service.perform_curation_operation(
                tool_id,
                operation,
                parameters,
                performed_by,
            )
            
            # Assert
            self.mock_registry.get_tool.assert_called_once_with(tool_id)
            assert result.tool_id == tool_id
            assert result.operation == operation
            assert result.success is True
            assert result.performed_by == performed_by
            assert result.details == {"version": parameters["version"]}
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation_evaluate(self):
        """Test performing evaluate curation operation."""
        # Arrange
        tool_id = uuid.uuid4()
        operation = "evaluate"
        parameters = {
            "requirements": ["Requirement 1", "Requirement 2"],
        }
        performed_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Mock evaluate_tool_capabilities
        capability_matches = [
            ToolCapabilityMatch(
                tool_id=tool_id,
                requirement="Requirement 1",
                capability="Capability",
                score=0.8,
            ),
        ]
        
        # Use patch to mock the method on the actual instance
        with patch.object(
            self.service,
            "evaluate_tool_capabilities",
            return_value=capability_matches,
        ):
            # Act
            result = await self.service.perform_curation_operation(
                tool_id,
                operation,
                parameters,
                performed_by,
            )
            
            # Assert
            self.mock_registry.get_tool.assert_called_once_with(tool_id)
            assert result.tool_id == tool_id
            assert result.operation == operation
            assert result.success is True
            assert result.performed_by == performed_by
            assert "capability_matches" in result.details
    
    @pytest.mark.asyncio
    async def test_perform_curation_operation_invalid(self):
        """Test performing invalid curation operation."""
        # Arrange
        tool_id = uuid.uuid4()
        operation = "invalid_operation"
        performed_by = "user1"
        
        # Mock registry
        self.mock_registry.get_tool.return_value = MagicMock()
        
        # Act
        result = await self.service.perform_curation_operation(tool_id, operation, performed_by=performed_by)
        
        # Assert
        self.mock_registry.get_tool.assert_called_once_with(tool_id)
        assert result.tool_id == tool_id
        assert result.operation == operation
        assert result.success is False
        assert result.performed_by == performed_by
        assert "error" in result.details


class TestToolCuratorServiceIntegration:
    """Integration tests for ToolCuratorService."""
    
    @pytest.mark.asyncio
    async def test_discover_tools_for_requirements_integration(self, tool_integration_db):
        """Test discovering tools for requirements with database integration."""
        # This test would use the actual database session and repository
        # For now, we'll just demonstrate the pattern
        pass
    
    @pytest.mark.asyncio
    async def test_recommend_tools_for_requirements_integration(self, tool_integration_db):
        """Test recommending tools for requirements with database integration."""
        # This test would use the actual database session and repository
        # For now, we'll just demonstrate the pattern
        pass
