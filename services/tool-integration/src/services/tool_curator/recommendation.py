"""
Recommendation engine for the Tool Curator component.

This module provides functionality for recommending tools based on requirements,
capabilities, and historical usage data.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import UUID
from datetime import datetime

from .models import (
    ToolMatchScore,
    ToolRecommendation,
    ToolCapabilityMatch,
    ToolCompatibilityResult,
    ToolUsageStatistics,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Engine for recommending tools based on requirements and capabilities.
    
    This class implements algorithms for matching tools to requirements,
    evaluating tool capabilities, and generating recommendations.
    """
    
    def __init__(
        self,
        semantic_similarity_threshold: float = 0.7,
        min_recommendation_score: float = 0.5,
        max_recommendations: int = 5,
        usage_weight: float = 0.2,
        capability_weight: float = 0.5,
        compatibility_weight: float = 0.3,
    ):
        """
        Initialize the recommendation engine.
        
        Args:
            semantic_similarity_threshold: Threshold for semantic similarity matching
            min_recommendation_score: Minimum score for a tool to be recommended
            max_recommendations: Maximum number of recommendations to return
            usage_weight: Weight for usage statistics in recommendation scoring
            capability_weight: Weight for capability matching in recommendation scoring
            compatibility_weight: Weight for compatibility in recommendation scoring
        """
        self.semantic_similarity_threshold = semantic_similarity_threshold
        self.min_recommendation_score = min_recommendation_score
        self.max_recommendations = max_recommendations
        self.usage_weight = usage_weight
        self.capability_weight = capability_weight
        self.compatibility_weight = compatibility_weight
        
        logger.info(
            f"Initialized RecommendationEngine with semantic_similarity_threshold={semantic_similarity_threshold}, "
            f"min_recommendation_score={min_recommendation_score}, max_recommendations={max_recommendations}"
        )
    
    async def match_tool_capabilities(
        self,
        tool_capabilities: List[str],
        requirements: List[str],
        tool_id: UUID,
    ) -> List[ToolCapabilityMatch]:
        """
        Match tool capabilities against requirements.
        
        Args:
            tool_capabilities: List of tool capabilities
            requirements: List of requirements to match against
            tool_id: ID of the tool
            
        Returns:
            List[ToolCapabilityMatch]: List of capability matches
        """
        logger.debug(f"Matching capabilities for tool {tool_id}")
        
        matches = []
        
        for requirement in requirements:
            requirement_id = str(uuid.uuid4())  # Generate a unique ID for this requirement
            
            # Find the best matching capability for this requirement
            best_match = None
            best_score = 0.0
            best_match_type = "none"
            
            for capability in tool_capabilities:
                # Check for exact match
                if capability.lower() == requirement.lower():
                    match_score = 1.0
                    match_type = "exact"
                # Check for partial match (capability contains requirement or vice versa)
                elif capability.lower() in requirement.lower() or requirement.lower() in capability.lower():
                    match_score = 0.8
                    match_type = "partial"
                # Check for semantic similarity (in a real implementation, this would use embeddings)
                else:
                    # Simplified semantic matching for demonstration
                    # In a real implementation, this would use embeddings and vector similarity
                    common_words = set(capability.lower().split()) & set(requirement.lower().split())
                    total_words = set(capability.lower().split()) | set(requirement.lower().split())
                    
                    if total_words:
                        match_score = len(common_words) / len(total_words)
                    else:
                        match_score = 0.0
                    
                    match_type = "semantic"
                
                # Update best match if this is better
                if match_score > best_score:
                    best_score = match_score
                    best_match = capability
                    best_match_type = match_type
            
            # If we found a match above the threshold, add it to the results
            if best_match and best_score >= self.semantic_similarity_threshold:
                matches.append(
                    ToolCapabilityMatch(
                        tool_id=tool_id,
                        capability=best_match,
                        requirement=requirement,
                        score=best_score,
                        match_type=best_match_type,
                        details={
                            "requirement_id": requirement_id,
                            "score": best_score,
                            "match_type": best_match_type,
                        },
                    )
                )
        
        logger.debug(f"Found {len(matches)} capability matches for tool {tool_id}")
        return matches
    
    async def calculate_tool_match_score(
        self,
        capability_matches: List[ToolCapabilityMatch],
        compatibility_result: Optional[ToolCompatibilityResult] = None,
        usage_statistics: Optional[ToolUsageStatistics] = None,
        requirement_id: Optional[UUID] = None,
    ) -> ToolMatchScore:
        """
        Calculate an overall match score for a tool based on capability matches,
        compatibility, and usage statistics.
        
        Args:
            capability_matches: List of capability matches
            compatibility_result: Optional compatibility result
            usage_statistics: Optional usage statistics
            requirement_id: Optional requirement ID
            
        Returns:
            ToolMatchScore: Overall match score
        """
        if not capability_matches:
            return ToolMatchScore(
                tool_id=UUID(int=0),  # This is a placeholder, should be replaced with actual tool ID
                requirement_id=requirement_id or UUID(int=0),
                score=0.0,
                match_details={"error": "No capability matches provided"},
            )
        
        tool_id = capability_matches[0].tool_id
        
        # Calculate capability score (average of all capability match scores)
        capability_score = sum(match.score for match in capability_matches) / len(capability_matches)
        
        # Get compatibility score if available
        compatibility_score = compatibility_result.compatibility_score if compatibility_result else 1.0
        
        # Calculate usage score if available
        usage_score = 0.0
        if usage_statistics:
            # Simple usage score based on success rate
            if usage_statistics.total_executions > 0:
                usage_score = usage_statistics.successful_executions / usage_statistics.total_executions
        
        # Calculate weighted overall score
        overall_score = (
            self.capability_weight * capability_score +
            self.compatibility_weight * compatibility_score +
            self.usage_weight * usage_score
        )
        
        # Create match details
        match_details = {
            "capability_score": capability_score,
            "compatibility_score": compatibility_score,
            "usage_score": usage_score,
            "capability_weight": self.capability_weight,
            "compatibility_weight": self.compatibility_weight,
            "usage_weight": self.usage_weight,
            "capability_matches": [match.dict() for match in capability_matches],
        }
        
        if compatibility_result:
            match_details["compatibility_result"] = compatibility_result.dict()
        
        if usage_statistics:
            match_details["usage_statistics"] = {
                "total_executions": usage_statistics.total_executions,
                "successful_executions": usage_statistics.successful_executions,
                "average_execution_time_ms": usage_statistics.average_execution_time_ms,
            }
        
        return ToolMatchScore(
            tool_id=tool_id,
            requirement_id=requirement_id or UUID(int=0),
            score=overall_score,
            match_details=match_details,
        )
    
    async def generate_recommendations(
        self,
        match_scores: List[ToolMatchScore],
        requirement_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolRecommendation]:
        """
        Generate tool recommendations based on match scores.
        
        Args:
            match_scores: List of tool match scores
            requirement_id: ID of the requirement
            context: Optional context information
            
        Returns:
            List[ToolRecommendation]: List of tool recommendations
        """
        logger.debug(f"Generating recommendations for requirement {requirement_id}")
        
        # Filter out tools below the minimum score
        qualified_matches = [
            match for match in match_scores
            if match.score >= self.min_recommendation_score
        ]
        
        # Sort by score in descending order
        qualified_matches.sort(key=lambda x: x.score, reverse=True)
        
        # Limit to max recommendations
        top_matches = qualified_matches[:self.max_recommendations]
        
        # Generate recommendations
        recommendations = []
        
        for i, match in enumerate(top_matches):
            # Calculate confidence based on score and position
            confidence = match.score * (1.0 - (i * 0.05))  # Slight penalty for lower positions
            
            # Generate reasoning
            reasoning = self._generate_recommendation_reasoning(match, context)
            
            # Find alternative tools (next best matches that weren't selected)
            alternatives = []
            if i < len(qualified_matches) - 1:
                alternatives = [m.tool_id for m in qualified_matches[i+1:i+4]]  # Up to 3 alternatives
            
            recommendations.append(
                ToolRecommendation(
                    tool_id=match.tool_id,
                    requirement_id=requirement_id,
                    score=match.score,
                    confidence=confidence,
                    reasoning=reasoning,
                    alternatives=alternatives,
                )
            )
        
        logger.debug(f"Generated {len(recommendations)} recommendations for requirement {requirement_id}")
        return recommendations
    
    def _generate_recommendation_reasoning(
        self,
        match: ToolMatchScore,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate reasoning for a tool recommendation.
        
        Args:
            match: Tool match score
            context: Optional context information
            
        Returns:
            str: Recommendation reasoning
        """
        details = match.match_details
        
        # Extract scores
        capability_score = details.get("capability_score", 0.0)
        compatibility_score = details.get("compatibility_score", 0.0)
        usage_score = details.get("usage_score", 0.0)
        
        # Generate reasoning based on scores
        reasons = []
        
        if capability_score >= 0.9:
            reasons.append("This tool provides excellent capability matches for your requirements.")
        elif capability_score >= 0.7:
            reasons.append("This tool provides good capability matches for your requirements.")
        elif capability_score >= 0.5:
            reasons.append("This tool provides adequate capability matches for your requirements.")
        
        if compatibility_score >= 0.9:
            reasons.append("It has excellent compatibility with your environment.")
        elif compatibility_score >= 0.7:
            reasons.append("It has good compatibility with your environment.")
        elif compatibility_score >= 0.5:
            reasons.append("It has adequate compatibility with your environment.")
        
        if usage_score >= 0.9:
            reasons.append("It has a proven track record of successful usage.")
        elif usage_score >= 0.7:
            reasons.append("It has a good track record of successful usage.")
        elif usage_score >= 0.5:
            reasons.append("It has an adequate track record of successful usage.")
        
        # Add capability match details
        capability_matches = details.get("capability_matches", [])
        if capability_matches:
            exact_matches = [m for m in capability_matches if m.get("match_type") == "exact"]
            partial_matches = [m for m in capability_matches if m.get("match_type") == "partial"]
            semantic_matches = [m for m in capability_matches if m.get("match_type") == "semantic"]
            
            if exact_matches:
                reasons.append(f"It exactly matches {len(exact_matches)} of your requirements.")
            
            if partial_matches:
                reasons.append(f"It partially matches {len(partial_matches)} of your requirements.")
            
            if semantic_matches:
                reasons.append(f"It semantically matches {len(semantic_matches)} of your requirements.")
        
        # Add context-specific reasoning if available
        if context:
            if "project_type" in context:
                reasons.append(f"It is suitable for {context['project_type']} projects.")
            
            if "agent_type" in context:
                reasons.append(f"It works well with {context['agent_type']} agents.")
        
        # Combine reasons into a coherent paragraph
        if reasons:
            reasoning = " ".join(reasons)
        else:
            reasoning = "This tool meets your requirements based on overall evaluation."
        
        return reasoning
