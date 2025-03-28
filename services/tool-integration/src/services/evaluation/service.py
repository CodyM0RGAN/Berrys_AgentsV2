"""
Tool Evaluation Service module.

This module defines the main evaluation service for evaluating tools,
providing a unified interface for evaluating tools against various criteria.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ...models.internal import Tool as ToolModel
from ...exceptions import ToolEvaluationError
from ..repository import ToolRepository
from ..security import SecurityScanner
from .evaluator import (
    EvaluationCriteria,
    SecurityEvaluator,
    PerformanceEvaluator,
    CompatibilityEvaluator,
    UsabilityEvaluator,
    SchemaValidator,
    ComprehensiveEvaluationResult,
    EvaluationCriteriaType,
)

logger = logging.getLogger(__name__)


class ToolEvaluationService:
    """Service for evaluating tools against various criteria."""
    
    def __init__(
        self,
        repository: ToolRepository,
        security_scanner: SecurityScanner,
        schema_validation_enabled: bool = True,
        performance_execution_timeout: int = 30,
        max_tool_memory_mb: int = 500,
    ):
        """
        Initialize the evaluation service.
        
        Args:
            repository: Tool repository
            security_scanner: Security scanner service
            schema_validation_enabled: Whether schema validation is enabled
            performance_execution_timeout: Execution timeout for performance evaluation
            max_tool_memory_mb: Maximum allowed memory usage for tools
        """
        self.repository = repository
        
        # Initialize evaluators
        self.security_evaluator = SecurityEvaluator(security_scanner)
        self.performance_evaluator = PerformanceEvaluator(
            execution_timeout=performance_execution_timeout,
            max_memory_mb=max_tool_memory_mb,
        )
        self.compatibility_evaluator = CompatibilityEvaluator()
        self.usability_evaluator = UsabilityEvaluator()
        self.schema_validator = SchemaValidator(enabled=schema_validation_enabled)
        
        logger.info("Tool evaluation service initialized")
    
    async def evaluate_tool(
        self,
        tool: ToolModel,
        criteria: Dict[EvaluationCriteriaType, bool],
        context: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveEvaluationResult:
        """
        Evaluate a tool against specified criteria.
        
        Args:
            tool: Tool to evaluate
            criteria: Evaluation criteria
            context: Optional evaluation context
            
        Returns:
            ComprehensiveEvaluationResult: Comprehensive evaluation result
            
        Raises:
            ToolEvaluationError: If evaluation fails
        """
        logger.info(f"Evaluating tool: {tool.id}")
        
        evaluation_id = str(uuid.uuid4())
        evaluation_timestamp = datetime.utcnow()
        context = context or {}
        
        # Initialize result with default values
        result = ComprehensiveEvaluationResult(
            tool_id=str(tool.id),
            evaluation_id=evaluation_id,
            evaluation_timestamp=evaluation_timestamp,
            overall_score=0.0,
            recommendation="",
            context=context,
        )
        
        # Validation errors
        validation_errors = []
        
        # Check if schema validation is requested
        if EvaluationCriteriaType.SECURITY in criteria and criteria[EvaluationCriteriaType.SECURITY]:
            # Validate schema
            if tool.schema:
                schema_errors = self.schema_validator.validate_schema(tool.schema)
                if schema_errors:
                    validation_errors.extend(schema_errors)
        
        # If there are validation errors and they are critical, fail early
        if validation_errors:
            logger.warning(f"Schema validation errors for tool {tool.id}: {validation_errors}")
            # We'll continue evaluation but note the errors
        
        try:
            # Evaluate security if requested
            if EvaluationCriteriaType.SECURITY in criteria and criteria[EvaluationCriteriaType.SECURITY]:
                logger.info(f"Evaluating security for tool: {tool.id}")
                try:
                    security_result = await self.security_evaluator.evaluate(tool, context)
                    result.security = security_result
                except Exception as e:
                    logger.error(f"Error evaluating security for tool {tool.id}: {str(e)}")
                    raise ToolEvaluationError(
                        f"Security evaluation failed: {str(e)}",
                        tool_id=str(tool.id),
                        evaluation_type=EvaluationCriteriaType.SECURITY.name,
                    )
            
            # Evaluate performance if requested
            if EvaluationCriteriaType.PERFORMANCE in criteria and criteria[EvaluationCriteriaType.PERFORMANCE]:
                logger.info(f"Evaluating performance for tool: {tool.id}")
                try:
                    performance_result = await self.performance_evaluator.evaluate(tool, context)
                    result.performance = performance_result
                except Exception as e:
                    logger.error(f"Error evaluating performance for tool {tool.id}: {str(e)}")
                    raise ToolEvaluationError(
                        f"Performance evaluation failed: {str(e)}",
                        tool_id=str(tool.id),
                        evaluation_type=EvaluationCriteriaType.PERFORMANCE.name,
                    )
            
            # Evaluate compatibility if requested
            if EvaluationCriteriaType.COMPATIBILITY in criteria and criteria[EvaluationCriteriaType.COMPATIBILITY]:
                logger.info(f"Evaluating compatibility for tool: {tool.id}")
                try:
                    compatibility_result = await self.compatibility_evaluator.evaluate(tool, context)
                    result.compatibility = compatibility_result
                except Exception as e:
                    logger.error(f"Error evaluating compatibility for tool {tool.id}: {str(e)}")
                    raise ToolEvaluationError(
                        f"Compatibility evaluation failed: {str(e)}",
                        tool_id=str(tool.id),
                        evaluation_type=EvaluationCriteriaType.COMPATIBILITY.name,
                    )
            
            # Evaluate usability if requested
            if EvaluationCriteriaType.USABILITY in criteria and criteria[EvaluationCriteriaType.USABILITY]:
                logger.info(f"Evaluating usability for tool: {tool.id}")
                try:
                    usability_result = await self.usability_evaluator.evaluate(tool, context)
                    result.usability_score = usability_result.score
                except Exception as e:
                    logger.error(f"Error evaluating usability for tool {tool.id}: {str(e)}")
                    raise ToolEvaluationError(
                        f"Usability evaluation failed: {str(e)}",
                        tool_id=str(tool.id),
                        evaluation_type=EvaluationCriteriaType.USABILITY.name,
                    )
            
            # Calculate overall score
            result.overall_score = self._calculate_overall_score(result)
            
            # Generate recommendation
            result.recommendation = self._generate_recommendation(result)
            
            # Store evaluation result in database
            await self._store_evaluation_result(tool.id, result)
            
            return result
        except Exception as e:
            if isinstance(e, ToolEvaluationError):
                raise
            logger.error(f"Error evaluating tool {tool.id}: {str(e)}")
            raise ToolEvaluationError(
                f"Tool evaluation failed: {str(e)}",
                tool_id=str(tool.id),
            )
    
    async def batch_evaluate_tools(
        self,
        tools: List[ToolModel],
        criteria: Dict[EvaluationCriteriaType, bool],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ComprehensiveEvaluationResult]:
        """
        Evaluate multiple tools in a batch.
        
        Args:
            tools: Tools to evaluate
            criteria: Evaluation criteria
            context: Optional evaluation context
            
        Returns:
            Dict[str, ComprehensiveEvaluationResult]: Evaluation results by tool ID
        """
        logger.info(f"Batch evaluating {len(tools)} tools")
        
        results = {}
        
        for tool in tools:
            try:
                result = await self.evaluate_tool(tool, criteria, context)
                results[str(tool.id)] = result
            except Exception as e:
                logger.error(f"Error evaluating tool {tool.id}: {str(e)}")
                # Continue with next tool
        
        return results
    
    def _calculate_overall_score(self, result: ComprehensiveEvaluationResult) -> float:
        """
        Calculate overall score from individual evaluation scores.
        
        Args:
            result: Evaluation result
            
        Returns:
            float: Overall score
        """
        scores = []
        weights = []
        
        # Add security score if available
        if result.security:
            scores.append(result.security.score)
            weights.append(0.4)  # Security has highest weight
        
        # Add performance score if available
        if result.performance:
            scores.append(result.performance.score)
            weights.append(0.2)  # Performance weight
        
        # Add compatibility score if available
        if result.compatibility:
            scores.append(result.compatibility.score)
            weights.append(0.2)  # Compatibility weight
        
        # Add usability score if available
        if result.usability_score is not None:
            scores.append(result.usability_score)
            weights.append(0.2)  # Usability weight
        
        # Calculate weighted average
        if scores:
            total_weight = sum(weights)
            weighted_score = sum(score * weight for score, weight in zip(scores, weights))
            return weighted_score / total_weight if total_weight > 0 else 0.0
        else:
            return 0.0
    
    def _generate_recommendation(self, result: ComprehensiveEvaluationResult) -> str:
        """
        Generate recommendation based on evaluation results.
        
        Args:
            result: Evaluation result
            
        Returns:
            str: Recommendation
        """
        overall_score = result.overall_score
        
        # Generate recommendation based on overall score
        if overall_score >= 0.8:
            recommendation = "APPROVED - This tool meets all requirements"
        elif overall_score >= 0.6:
            recommendation = "APPROVED WITH RESERVATIONS - This tool meets most requirements but has some issues"
        elif overall_score >= 0.4:
            recommendation = "NEEDS IMPROVEMENT - This tool has significant issues that should be addressed"
        else:
            recommendation = "NOT RECOMMENDED - This tool has critical issues that make it unsuitable for use"
        
        # Add specific warnings for individual evaluations
        warnings = []
        
        if result.security and result.security.score < 0.6:
            warnings.append(f"Security concerns (score: {result.security.score:.2f})")
        
        if result.performance and result.performance.score < 0.6:
            warnings.append(f"Performance concerns (score: {result.performance.score:.2f})")
        
        if result.compatibility and result.compatibility.score < 0.6:
            warnings.append(f"Compatibility concerns (score: {result.compatibility.score:.2f})")
        
        if result.usability_score is not None and result.usability_score < 0.6:
            warnings.append(f"Usability concerns (score: {result.usability_score:.2f})")
        
        # Add warnings to recommendation if any
        if warnings:
            recommendation += ". Warning: " + ", ".join(warnings)
        
        return recommendation
    
    async def _store_evaluation_result(
        self,
        tool_id: Any,  # UUID
        result: ComprehensiveEvaluationResult,
    ) -> None:
        """
        Store evaluation result in database.
        
        Args:
            tool_id: Tool ID
            result: Evaluation result
        """
        # In a real implementation, this would store the result in a database
        # For now, we'll just log it
        logger.info(f"Storing evaluation result for tool {tool_id}: {result.overall_score}")
        
        # Example: convert result to database model
        evaluation_data = {
            "id": result.evaluation_id,
            "tool_id": tool_id,
            "evaluation_timestamp": result.evaluation_timestamp,
            "overall_score": result.overall_score,
            "recommendation": result.recommendation,
        }
        
        # Add individual evaluation results if available
        if result.security:
            evaluation_data["security_evaluation"] = {
                "score": result.security.score,
                "passed": result.security.passed,
                "issues": result.security.issues,
                "vulnerabilities": result.security.vulnerabilities,
                "risk_level": result.security.risk_level,
            }
        
        if result.performance:
            evaluation_data["performance_evaluation"] = {
                "score": result.performance.score,
                "passed": result.performance.passed,
                "issues": result.performance.issues,
                "execution_time_ms": result.performance.execution_time_ms,
                "memory_usage_mb": result.performance.memory_usage_mb,
                "cpu_usage_percent": result.performance.cpu_usage_percent,
                "network_requests": result.performance.network_requests,
            }
        
        if result.compatibility:
            evaluation_data["compatibility_evaluation"] = {
                "score": result.compatibility.score,
                "passed": result.compatibility.passed,
                "issues": result.compatibility.issues,
                "compatible_environments": result.compatibility.compatible_environments,
                "compatible_versions": result.compatibility.compatible_versions,
                "incompatible_environments": result.compatibility.incompatible_environments,
                "incompatible_versions": result.compatibility.incompatible_versions,
            }
        
        if result.usability_score is not None:
            evaluation_data["usability_score"] = result.usability_score
        
        # Store in database
        try:
            await self.repository.create_evaluation(evaluation_data)
        except Exception as e:
            logger.error(f"Error storing evaluation for tool {tool_id}: {str(e)}")
