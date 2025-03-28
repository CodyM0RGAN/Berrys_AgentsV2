"""
Main service implementation for the Tool Curator component.

This module provides the main service interface for the Tool Curator component,
integrating tool discovery, evaluation, recommendation, and versioning functionality.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from uuid import UUID
from datetime import datetime

from shared.models.src.tool import (
    ToolSource,
    ToolStatus,
    IntegrationType,
    ToolBase,
    ToolCreate,
    ToolUpdate,
    Tool,
    ToolSummary,
    ToolRequirement,
    ToolDiscoveryRequest,
    ToolEvaluationResult,
)

from ..discovery import DiscoveryService
from ..evaluation import ToolEvaluationService
from ..repository import ToolRepository
from ..registry import ToolRegistry

from .models import (
    ToolMatchScore,
    ToolRecommendation,
    ToolCapabilityMatch,
    ToolCompatibilityResult,
    ToolVersion,
    ToolVersionStatus,
    ToolCurationResult,
    ToolUsageStatistics,
)
from .recommendation import RecommendationEngine
from .versioning import ToolVersioningService

logger = logging.getLogger(__name__)


class ToolCuratorService:
    """
    Service for curating tools based on requirements and capabilities.
    
    This service integrates tool discovery, evaluation, recommendation, and versioning
    to provide a comprehensive tool curation solution.
    """
    
    def __init__(
        self,
        repository: ToolRepository,
        registry: ToolRegistry,
        discovery_service: DiscoveryService,
        evaluation_service: ToolEvaluationService,
        recommendation_engine: Optional[RecommendationEngine] = None,
        versioning_service: Optional[ToolVersioningService] = None,
    ):
        """
        Initialize the tool curator service.
        
        Args:
            repository: Tool repository
            registry: Tool registry
            discovery_service: Tool discovery service
            evaluation_service: Tool evaluation service
            recommendation_engine: Optional recommendation engine (created if not provided)
            versioning_service: Optional versioning service (created if not provided)
        """
        self.repository = repository
        self.registry = registry
        self.discovery_service = discovery_service
        self.evaluation_service = evaluation_service
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.versioning_service = versioning_service or ToolVersioningService()
        
        logger.info("Initialized ToolCuratorService")
    
    async def discover_tools_for_requirements(
        self,
        requirements: List[ToolRequirement],
        context: Optional[Dict[str, Any]] = None,
        sources: Optional[List[ToolSource]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover tools that match the given requirements.
        
        Args:
            requirements: List of tool requirements
            context: Optional discovery context
            sources: Optional list of tool sources to search
            
        Returns:
            List[Dict[str, Any]]: List of discovered tools
        """
        logger.info(f"Discovering tools for {len(requirements)} requirements")
        
        # Extract requirement strings for discovery
        requirement_strings = [req.description for req in requirements]
        
        # Discover tools
        discovered_tools = await self.discovery_service.discover_tools(
            requirement_strings,
            context,
            sources=[s.value for s in sources] if sources else None,
        )
        
        logger.info(f"Discovered {len(discovered_tools)} tools")
        return discovered_tools
    
    async def evaluate_tool_capabilities(
        self,
        tool_id: UUID,
        requirements: List[str],
    ) -> List[ToolCapabilityMatch]:
        """
        Evaluate a tool's capabilities against requirements.
        
        Args:
            tool_id: ID of the tool to evaluate
            requirements: List of requirements to evaluate against
            
        Returns:
            List[ToolCapabilityMatch]: List of capability matches
            
        Raises:
            ValueError: If the tool is not found
        """
        logger.info(f"Evaluating capabilities of tool {tool_id}")
        
        # Get the tool
        tool = await self.registry.get_tool(tool_id)
        
        # Extract capabilities from the tool
        capabilities = []
        if tool.capability:
            capabilities.append(tool.capability)
        
        # Add capabilities from schema if available
        if tool.schema and isinstance(tool.schema, dict):
            if "description" in tool.schema:
                capabilities.append(tool.schema["description"])
            
            if "properties" in tool.schema:
                for prop_name, prop_info in tool.schema["properties"].items():
                    if "description" in prop_info:
                        capabilities.append(prop_info["description"])
        
        # Match capabilities against requirements
        capability_matches = await self.recommendation_engine.match_tool_capabilities(
            capabilities, requirements, tool_id
        )
        
        logger.info(f"Found {len(capability_matches)} capability matches for tool {tool_id}")
        return capability_matches
    
    async def recommend_tools_for_requirements(
        self,
        requirements: List[ToolRequirement],
        context: Optional[Dict[str, Any]] = None,
        min_score: float = 0.5,
        max_recommendations: int = 5,
    ) -> Dict[UUID, List[ToolRecommendation]]:
        """
        Recommend tools for the given requirements.
        
        Args:
            requirements: List of tool requirements
            context: Optional recommendation context
            min_score: Minimum score for a tool to be recommended
            max_recommendations: Maximum number of recommendations per requirement
            
        Returns:
            Dict[UUID, List[ToolRecommendation]]: Recommendations by requirement ID
        """
        logger.info(f"Recommending tools for {len(requirements)} requirements")
        
        # Initialize results
        recommendations_by_requirement = {}
        
        # Process each requirement
        for requirement in requirements:
            requirement_id = requirement.id or uuid.uuid4()
            
            # Get all tools from the registry
            tools, _ = await self.registry.list_tools(
                status=ToolStatus.APPROVED.value,
                page=1,
                page_size=100,  # Adjust as needed
            )
            
            # Evaluate each tool against this requirement
            match_scores = []
            
            for tool in tools:
                # Match capabilities
                capability_matches = await self.recommendation_engine.match_tool_capabilities(
                    [tool.capability] if tool.capability else [],
                    [requirement.description],
                    tool.id,
                )
                
                if not capability_matches:
                    continue
                
                # Get compatibility information if available
                compatibility_result = None
                # In a real implementation, you would get compatibility information from somewhere
                
                # Get usage statistics if available
                usage_statistics = None
                # In a real implementation, you would get usage statistics from somewhere
                
                # Calculate match score
                match_score = await self.recommendation_engine.calculate_tool_match_score(
                    capability_matches,
                    compatibility_result,
                    usage_statistics,
                    requirement_id,
                )
                
                match_scores.append(match_score)
            
            # Generate recommendations
            recommendations = await self.recommendation_engine.generate_recommendations(
                match_scores,
                requirement_id,
                context,
            )
            
            # Store recommendations for this requirement
            recommendations_by_requirement[requirement_id] = recommendations
        
        logger.info(f"Generated recommendations for {len(recommendations_by_requirement)} requirements")
        return recommendations_by_requirement
    
    async def track_tool_version(
        self,
        tool_id: UUID,
        version_number: str,
        status: ToolVersionStatus = ToolVersionStatus.CURRENT,
        release_notes: Optional[str] = None,
        changes: Optional[List[str]] = None,
        compatibility: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> ToolVersion:
        """
        Track a new version of a tool.
        
        Args:
            tool_id: ID of the tool
            version_number: Version number (semantic versioning)
            status: Status of this version
            release_notes: Optional release notes
            changes: Optional list of changes
            compatibility: Optional compatibility information
            created_by: Optional creator identifier
            
        Returns:
            ToolVersion: Created version
            
        Raises:
            ValueError: If the version number is invalid or the tool is not found
        """
        logger.info(f"Tracking version {version_number} for tool {tool_id}")
        
        # Ensure the tool exists
        await self.registry.get_tool(tool_id)
        
        # Create the version
        version = await self.versioning_service.create_version(
            tool_id,
            version_number,
            status,
            release_notes,
            changes,
            compatibility,
            created_by,
        )
        
        # Store the version in the repository
        # In a real implementation, you would store the version in a database
        # For now, we'll just return the created version
        
        logger.info(f"Tracked version {version_number} for tool {tool_id}")
        return version
    
    async def update_tool_version_status(
        self,
        tool_id: UUID,
        version_number: str,
        new_status: ToolVersionStatus,
    ) -> ToolVersion:
        """
        Update the status of a tool version.
        
        Args:
            tool_id: ID of the tool
            version_number: Version number
            new_status: New status
            
        Returns:
            ToolVersion: Updated version
            
        Raises:
            ValueError: If the version is not found
        """
        logger.info(f"Updating status of version {version_number} for tool {tool_id} to {new_status}")
        
        # In a real implementation, you would get the version from a database
        # For now, we'll create a dummy version
        version = ToolVersion(
            tool_id=tool_id,
            version_number=version_number,
            status=ToolVersionStatus.CURRENT,  # Placeholder
        )
        
        # Update the status
        updated_version = await self.versioning_service.update_version_status(
            version,
            new_status,
        )
        
        # Store the updated version in the repository
        # In a real implementation, you would update the version in a database
        
        logger.info(f"Updated status of version {version_number} for tool {tool_id} to {new_status}")
        return updated_version
    
    async def check_tool_compatibility(
        self,
        tool_id: UUID,
        version1: str,
        version2: str,
    ) -> Dict[str, Any]:
        """
        Check compatibility between two versions of a tool.
        
        Args:
            tool_id: ID of the tool
            version1: First version string
            version2: Second version string
            
        Returns:
            Dict[str, Any]: Compatibility information
            
        Raises:
            ValueError: If either version string is invalid or the tool is not found
        """
        logger.info(f"Checking compatibility between versions {version1} and {version2} for tool {tool_id}")
        
        # Ensure the tool exists
        await self.registry.get_tool(tool_id)
        
        # Check compatibility
        compatibility_info = await self.versioning_service.check_version_compatibility(
            tool_id,
            version1,
            version2,
        )
        
        logger.info(
            f"Checked compatibility between versions {version1} and {version2} for tool {tool_id}: "
            f"{'compatible' if compatibility_info['is_compatible'] else 'incompatible'}"
        )
        
        return compatibility_info
    
    async def curate_tools_for_agent(
        self,
        agent_id: UUID,
        requirements: List[ToolRequirement],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolRecommendation]:
        """
        Curate a set of tools for an agent based on requirements.
        
        This is a high-level method that combines discovery, evaluation, and recommendation
        to provide a comprehensive tool curation solution.
        
        Args:
            agent_id: ID of the agent
            requirements: List of tool requirements
            context: Optional curation context
            
        Returns:
            List[ToolRecommendation]: List of tool recommendations
        """
        logger.info(f"Curating tools for agent {agent_id} with {len(requirements)} requirements")
        
        # Add agent information to context
        if context is None:
            context = {}
        context["agent_id"] = str(agent_id)
        
        # Get all recommendations by requirement
        recommendations_by_requirement = await self.recommend_tools_for_requirements(
            requirements,
            context,
        )
        
        # Flatten recommendations
        all_recommendations = []
        for req_id, recommendations in recommendations_by_requirement.items():
            all_recommendations.extend(recommendations)
        
        # Sort by score
        all_recommendations.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Curated {len(all_recommendations)} tools for agent {agent_id}")
        return all_recommendations
    
    async def get_tool_usage_statistics(
        self,
        tool_id: UUID,
    ) -> ToolUsageStatistics:
        """
        Get usage statistics for a tool.
        
        Args:
            tool_id: ID of the tool
            
        Returns:
            ToolUsageStatistics: Usage statistics
            
        Raises:
            ValueError: If the tool is not found
        """
        logger.info(f"Getting usage statistics for tool {tool_id}")
        
        # Ensure the tool exists
        await self.registry.get_tool(tool_id)
        
        # In a real implementation, you would get usage statistics from a database
        # For now, we'll create dummy statistics
        statistics = ToolUsageStatistics(
            tool_id=tool_id,
            total_executions=0,
            successful_executions=0,
            failed_executions=0,
        )
        
        logger.info(f"Got usage statistics for tool {tool_id}")
        return statistics
    
    async def perform_curation_operation(
        self,
        tool_id: UUID,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        performed_by: Optional[str] = None,
    ) -> ToolCurationResult:
        """
        Perform a curation operation on a tool.
        
        Args:
            tool_id: ID of the tool
            operation: Curation operation to perform
            parameters: Optional operation parameters
            performed_by: Optional identifier of who performed the operation
            
        Returns:
            ToolCurationResult: Result of the curation operation
            
        Raises:
            ValueError: If the tool is not found or the operation is invalid
        """
        logger.info(f"Performing curation operation {operation} on tool {tool_id}")
        
        # Ensure the tool exists
        await self.registry.get_tool(tool_id)
        
        # Initialize result
        result = ToolCurationResult(
            tool_id=tool_id,
            operation=operation,
            success=False,
            details={},
            performed_by=performed_by,
        )
        
        # Perform the operation
        if operation == "approve":
            # Approve the tool
            await self.registry.approve_tool(tool_id)
            result.success = True
            result.details = {"status": "APPROVED"}
        
        elif operation == "deprecate":
            # Deprecate the tool
            await self.registry.deprecate_tool(tool_id)
            result.success = True
            result.details = {"status": "DEPRECATED"}
        
        elif operation == "update_version":
            # Update the tool version
            if parameters and "version" in parameters:
                version = parameters["version"]
                await self.track_tool_version(
                    tool_id,
                    version,
                    status=ToolVersionStatus.CURRENT,
                    release_notes=parameters.get("release_notes"),
                    changes=parameters.get("changes"),
                    created_by=performed_by,
                )
                result.success = True
                result.details = {"version": version}
            else:
                result.details = {"error": "Missing version parameter"}
        
        elif operation == "evaluate":
            # Evaluate the tool
            if parameters and "requirements" in parameters:
                requirements = parameters["requirements"]
                capability_matches = await self.evaluate_tool_capabilities(
                    tool_id,
                    requirements,
                )
                result.success = True
                result.details = {
                    "capability_matches": [match.dict() for match in capability_matches],
                }
            else:
                result.details = {"error": "Missing requirements parameter"}
        
        else:
            # Invalid operation
            result.details = {"error": f"Invalid operation: {operation}"}
        
        logger.info(
            f"Performed curation operation {operation} on tool {tool_id}: "
            f"{'success' if result.success else 'failure'}"
        )
        
        return result
