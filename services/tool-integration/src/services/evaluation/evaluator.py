"""
Tool Evaluator module.

This module defines the evaluators for different evaluation criteria,
providing functionality for evaluating tools against security, performance,
compatibility, and usability criteria.
"""

import logging
import abc
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
import time
import json
import jsonschema

from ...models.internal import Tool as ToolModel
from ...exceptions import ToolEvaluationError
from ..security import SecurityScanner

logger = logging.getLogger(__name__)


class EvaluationCriteriaType(Enum):
    """Types of evaluation criteria."""
    SECURITY = auto()
    PERFORMANCE = auto()
    COMPATIBILITY = auto()
    USABILITY = auto()


@dataclass
class EvaluationCriteria:
    """Criteria for tool evaluation."""
    security: bool = True
    performance: bool = True
    compatibility: bool = True
    usability: bool = True
    schema_validation: bool = True


@dataclass
class EvaluationResult:
    """Base result of an evaluation."""
    score: float  # 0.0 to 1.0
    passed: bool
    issues: List[str]
    details: Dict[str, Any]


@dataclass
class SecurityEvaluationResult(EvaluationResult):
    """Result of a security evaluation."""
    vulnerabilities: List[Dict[str, Any]]
    risk_level: str


@dataclass
class PerformanceEvaluationResult(EvaluationResult):
    """Result of a performance evaluation."""
    execution_time_ms: int
    memory_usage_mb: float
    cpu_usage_percent: float
    network_requests: int


@dataclass
class CompatibilityEvaluationResult(EvaluationResult):
    """Result of a compatibility evaluation."""
    compatible_environments: List[str]
    compatible_versions: List[str]
    incompatible_environments: List[str]
    incompatible_versions: List[str]


@dataclass
class UsabilityEvaluationResult(EvaluationResult):
    """Result of a usability evaluation."""
    documentation_quality: float  # 0.0 to 1.0
    parameter_clarity: float  # 0.0 to 1.0
    error_handling: float  # 0.0 to 1.0


@dataclass
class ComprehensiveEvaluationResult:
    """Comprehensive result of all evaluations."""
    tool_id: str
    evaluation_id: str
    evaluation_timestamp: Any  # datetime
    overall_score: float  # 0.0 to 1.0
    security: Optional[SecurityEvaluationResult] = None
    performance: Optional[PerformanceEvaluationResult] = None
    compatibility: Optional[CompatibilityEvaluationResult] = None
    usability_score: Optional[float] = None
    reliability_score: Optional[float] = None
    recommendation: str = ""
    context: Optional[Dict[str, Any]] = None


class Evaluator(Protocol):
    """Protocol for tool evaluators."""
    
    @abc.abstractmethod
    async def evaluate(
        self,
        tool: ToolModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a tool.
        
        Args:
            tool: Tool to evaluate
            context: Optional evaluation context
            
        Returns:
            EvaluationResult: Evaluation result
        """
        pass


class SecurityEvaluator:
    """Evaluator for security criteria."""
    
    def __init__(self, security_scanner: SecurityScanner):
        """
        Initialize the security evaluator.
        
        Args:
            security_scanner: Security scanner service
        """
        self.security_scanner = security_scanner
    
    async def evaluate(
        self,
        tool: ToolModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvaluationResult:
        """
        Evaluate a tool for security.
        
        Args:
            tool: Tool to evaluate
            context: Optional evaluation context
            
        Returns:
            SecurityEvaluationResult: Security evaluation result
        """
        logger.info(f"Evaluating security for tool: {tool.id}")
        
        # Scan tool for security issues
        security_check = await self.security_scanner.scan_tool(tool)
        
        # Process results
        vulnerabilities = []
        issues = []
        
        if not security_check.approved:
            issues.append(security_check.reason or "Security check failed")
            if security_check.violation_type:
                vulnerabilities.append({
                    "type": security_check.violation_type,
                    "description": security_check.reason,
                    "severity": "HIGH",
                    "details": security_check.details,
                })
        
        # Calculate security score
        # In a real implementation, this would be more sophisticated
        score = 1.0 if security_check.approved else 0.2
        
        # Determine risk level
        risk_level = "LOW" if score > 0.7 else "MEDIUM" if score > 0.4 else "HIGH"
        
        return SecurityEvaluationResult(
            score=score,
            passed=security_check.approved,
            issues=issues,
            details={"security_scan_result": str(security_check)},
            vulnerabilities=vulnerabilities,
            risk_level=risk_level,
        )


class PerformanceEvaluator:
    """Evaluator for performance criteria."""
    
    def __init__(
        self,
        execution_timeout: int = 30,
        max_memory_mb: int = 500,
    ):
        """
        Initialize the performance evaluator.
        
        Args:
            execution_timeout: Execution timeout in seconds
            max_memory_mb: Maximum allowed memory usage in MB
        """
        self.execution_timeout = execution_timeout
        self.max_memory_mb = max_memory_mb
    
    async def evaluate(
        self,
        tool: ToolModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerformanceEvaluationResult:
        """
        Evaluate a tool for performance.
        
        Args:
            tool: Tool to evaluate
            context: Optional evaluation context
            
        Returns:
            PerformanceEvaluationResult: Performance evaluation result
        """
        logger.info(f"Evaluating performance for tool: {tool.id}")
        
        # In a real implementation, this would actually test the tool's performance
        # For now, simulate some performance metrics
        
        # Simulate execution time
        execution_time_ms = 150  # milliseconds
        
        # Simulate memory usage
        memory_usage_mb = 200.0  # MB
        
        # Simulate CPU usage
        cpu_usage_percent = 25.0  # percent
        
        # Simulate network requests
        network_requests = 5
        
        # Calculate performance score based on metrics
        # In a real implementation, this would be more sophisticated
        time_score = min(1.0, 5000 / max(execution_time_ms, 10))
        memory_score = min(1.0, self.max_memory_mb / max(memory_usage_mb, 10))
        cpu_score = min(1.0, 100 / max(cpu_usage_percent, 5))
        network_score = min(1.0, 20 / max(network_requests, 1))
        
        # Weighted average score
        score = (time_score * 0.4 + memory_score * 0.3 + cpu_score * 0.2 + network_score * 0.1)
        
        # Identify issues
        issues = []
        if execution_time_ms > 1000:
            issues.append(f"Execution time ({execution_time_ms}ms) exceeds recommended maximum (1000ms)")
        if memory_usage_mb > self.max_memory_mb * 0.8:
            issues.append(f"Memory usage ({memory_usage_mb}MB) is close to maximum ({self.max_memory_mb}MB)")
        if cpu_usage_percent > 80:
            issues.append(f"CPU usage ({cpu_usage_percent}%) is high")
        if network_requests > 10:
            issues.append(f"Many network requests ({network_requests})")
        
        return PerformanceEvaluationResult(
            score=score,
            passed=not issues,
            issues=issues,
            details={},
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            network_requests=network_requests,
        )


class CompatibilityEvaluator:
    """Evaluator for compatibility criteria."""
    
    def __init__(
        self,
        environments: Optional[List[str]] = None,
        versions: Optional[List[str]] = None,
    ):
        """
        Initialize the compatibility evaluator.
        
        Args:
            environments: Supported environments
            versions: Supported versions
        """
        self.environments = environments or ["python", "node", "browser"]
        self.versions = versions or ["3.8", "3.9", "3.10", "3.11", "16", "18", "20"]
    
    async def evaluate(
        self,
        tool: ToolModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> CompatibilityEvaluationResult:
        """
        Evaluate a tool for compatibility.
        
        Args:
            tool: Tool to evaluate
            context: Optional evaluation context
            
        Returns:
            CompatibilityEvaluationResult: Compatibility evaluation result
        """
        logger.info(f"Evaluating compatibility for tool: {tool.id}")
        
        # In a real implementation, this would actually test compatibility
        # For now, simulate compatibility check
        
        # Extract compatibility information from tool schema or metadata
        compatible_environments = []
        compatible_versions = []
        incompatible_environments = []
        incompatible_versions = []
        
        # Analyze schema if available
        if tool.schema:
            # Example: check for environment-specific fields in schema
            if "environment" in tool.schema:
                compatible_environments = [
                    env for env in self.environments 
                    if env in tool.schema.get("environment", {}).get("compatible", [])
                ]
                incompatible_environments = [
                    env for env in self.environments
                    if env in tool.schema.get("environment", {}).get("incompatible", [])
                ]
            
            # Example: check for version-specific fields in schema
            if "version" in tool.schema:
                compatible_versions = [
                    ver for ver in self.versions
                    if ver in tool.schema.get("version", {}).get("compatible", [])
                ]
                incompatible_versions = [
                    ver for ver in self.versions
                    if ver in tool.schema.get("version", {}).get("incompatible", [])
                ]
        
        # If no explicit compatibility info, make assumptions based on tool source
        if not compatible_environments:
            if tool.source == "MCP":
                compatible_environments = ["python", "node", "browser"]
            elif tool.source == "EXTERNAL_API":
                compatible_environments = ["python", "node", "browser"]
            elif tool.source == "CODE_REPOSITORY":
                compatible_environments = ["python"]
            elif tool.source == "LOCAL_SCRIPT":
                compatible_environments = ["python"]
        
        # Calculate compatibility score
        total_environments = len(self.environments)
        total_versions = len(self.versions)
        
        env_score = len(compatible_environments) / total_environments if total_environments > 0 else 0.0
        ver_score = len(compatible_versions) / total_versions if total_versions > 0 else 0.0
        
        # Weighted score
        score = env_score * 0.7 + ver_score * 0.3
        
        # Identify issues
        issues = []
        if len(compatible_environments) == 0:
            issues.append("No compatible environments identified")
        if len(compatible_versions) == 0:
            issues.append("No compatible versions identified")
        if len(incompatible_environments) > 0:
            issues.append(f"Incompatible with environments: {', '.join(incompatible_environments)}")
        if len(incompatible_versions) > 0:
            issues.append(f"Incompatible with versions: {', '.join(incompatible_versions)}")
        
        return CompatibilityEvaluationResult(
            score=score,
            passed=not issues,
            issues=issues,
            details={},
            compatible_environments=compatible_environments,
            compatible_versions=compatible_versions,
            incompatible_environments=incompatible_environments,
            incompatible_versions=incompatible_versions,
        )


class UsabilityEvaluator:
    """Evaluator for usability criteria."""
    
    async def evaluate(
        self,
        tool: ToolModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> UsabilityEvaluationResult:
        """
        Evaluate a tool for usability.
        
        Args:
            tool: Tool to evaluate
            context: Optional evaluation context
            
        Returns:
            UsabilityEvaluationResult: Usability evaluation result
        """
        logger.info(f"Evaluating usability for tool: {tool.id}")
        
        # In a real implementation, this would actually evaluate usability
        # For now, simulate usability evaluation
        
        # Evaluate documentation quality
        documentation_quality = self._evaluate_documentation(tool)
        
        # Evaluate parameter clarity
        parameter_clarity = self._evaluate_parameters(tool)
        
        # Evaluate error handling
        error_handling = self._evaluate_error_handling(tool)
        
        # Calculate overall usability score
        score = (documentation_quality * 0.4 + parameter_clarity * 0.4 + error_handling * 0.2)
        
        # Identify issues
        issues = []
        if documentation_quality < 0.5:
            issues.append("Documentation quality is poor")
        if parameter_clarity < 0.5:
            issues.append("Parameter descriptions are unclear")
        if error_handling < 0.5:
            issues.append("Error handling is inadequate")
        
        return UsabilityEvaluationResult(
            score=score,
            passed=not issues,
            issues=issues,
            details={},
            documentation_quality=documentation_quality,
            parameter_clarity=parameter_clarity,
            error_handling=error_handling,
        )
    
    def _evaluate_documentation(self, tool: ToolModel) -> float:
        """Evaluate documentation quality."""
        # Simple heuristic: check for description and documentation URL
        score = 0.0
        
        if tool.description:
            score += len(tool.description.split()) / 100  # Longer descriptions get higher scores
            score = min(score, 0.7)  # Cap at 0.7
        
        if tool.documentation_url:
            score += 0.3  # Documentation URL adds 0.3
        
        return min(score, 1.0)
    
    def _evaluate_parameters(self, tool: ToolModel) -> float:
        """Evaluate parameter clarity."""
        # Simple heuristic: check for schema and parameter descriptions
        score = 0.0
        
        if not tool.schema:
            return 0.3  # No schema, poor clarity
        
        # Check for parameters
        properties = tool.schema.get("properties", {})
        if not properties:
            return 0.1  # No properties defined
        
        # Check for parameter descriptions
        total_params = len(properties)
        params_with_descriptions = sum(
            1 for prop in properties.values()
            if isinstance(prop, dict) and "description" in prop
        )
        
        if total_params > 0:
            score = 0.3 + (0.7 * (params_with_descriptions / total_params))
        
        return score
    
    def _evaluate_error_handling(self, tool: ToolModel) -> float:
        """Evaluate error handling."""
        # Simple heuristic: look for error handling in schema
        score = 0.5  # Default score
        
        if not tool.schema:
            return 0.3  # No schema, poor error handling
        
        # Check for error responses in schema
        if "errorResponses" in tool.schema:
            score += 0.3
        
        # Check for required fields
        if "required" in tool.schema:
            score += 0.2
        
        return min(score, 1.0)


class SchemaValidator:
    """Validator for tool schemas."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize the schema validator.
        
        Args:
            enabled: Whether schema validation is enabled
        """
        self.enabled = enabled
    
    def validate_schema(self, schema: Dict[str, Any]) -> List[str]:
        """
        Validate a tool schema.
        
        Args:
            schema: Tool schema
            
        Returns:
            List[str]: Validation errors, empty if valid
        """
        if not self.enabled:
            return []
        
        try:
            # Validate against meta-schema
            jsonschema.Draft7Validator.check_schema(schema)
            return []
        except jsonschema.exceptions.SchemaError as e:
            return [str(e)]
        except Exception as e:
            return [f"Schema validation error: {str(e)}"]
