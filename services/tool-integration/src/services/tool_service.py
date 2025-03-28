"""
Tool Integration Service main facade.

This module defines the main service interface for the Tool Integration service,
providing a unified API for tool discovery, evaluation, integration, and execution.
"""

import logging
import uuid
from typing import List, Dict, Optional, Any, Tuple, Union, cast
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

from ..models.api import (
    BatchRegistrationResponse,
    BatchEvaluationResponse,
    CompatibilityEvaluationResult,
    ComprehensiveEvaluationResult,
    DiscoveryResponse,
    EvaluationCriteriaType,
    EvaluationRequest,
    ExecutionMode,
    MCPServerInfo,
    MCPServerListResponse,
    MCPToolInfo,
    MCPToolListResponse,
    PaginatedResponse,
    PerformanceEvaluationResult,
    SecurityEvaluationResult,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolIntegrationRequest,
    ToolIntegrationResponse,
    ToolIntegrationUpdateRequest,
)

from ..models.internal import (
    Tool as ToolModel,
    ToolCategory,
    ToolExecution as ToolExecutionModel,
)

from ..exceptions import (
    ToolIntegrationError,
    ToolNotFoundError,
    ToolValidationError,
    ToolSchemaValidationError,
    ToolExecutionError,
    ToolExecutionTimeoutError,
    SecurityViolationError,
    ToolDiscoveryError,
    MCPIntegrationError,
    MCPToolNotAvailableError,
    ToolRegistrationError,
    ToolEvaluationError,
)

from .registry import ToolRegistry
from .repository import ToolRepository
from .discovery import DiscoveryService, DiscoveryStrategyFactory
from .evaluation import ToolEvaluationService
from .integration import ToolIntegrationService, IntegrationAdapterFactory
from .security import SecurityScanner

logger = logging.getLogger(__name__)

class ToolService:
    """
    Facade service for Tool Integration providing unified access to all functionality.
    
    This service orchestrates interactions between specialized components:
    - Tool Registry for management of registered tools
    - Discovery for finding new tools
    - Evaluation for security and performance testing
    - Integration for connecting tools to agents
    - Execution for running tools on behalf of agents
    
    It presents a simplified interface to clients while handling the complexity
    of coordinating these subsystems.
    """
    
    def __init__(
        self, 
        registry: ToolRegistry,
        repository: ToolRepository,
        discovery_service: DiscoveryService,
        evaluation_service: ToolEvaluationService,
        integration_service: ToolIntegrationService,
        security_scanner: SecurityScanner,
    ):
        """
        Initialize the tool service.
        
        Args:
            registry: Tool registry
            repository: Tool repository
            discovery_service: Tool discovery service
            evaluation_service: Tool evaluation service
            integration_service: Tool integration service
            security_scanner: Security scanner
        """
        self.registry = registry
        self.repository = repository
        self.discovery_service = discovery_service
        self.evaluation_service = evaluation_service
        self.integration_service = integration_service
        self.security_scanner = security_scanner

    # Tool registration and management

    async def register_tool(self, tool_data: ToolCreate) -> Tool:
        """
        Register a new tool.
        
        Args:
            tool_data: Tool data for creation
            
        Returns:
            Tool: Registered tool
            
        Raises:
            ToolRegistrationError: If registration fails
            ToolValidationError: If tool data is invalid
        """
        logger.info(f"Registering tool: {tool_data.name}")
        
        # Convert Pydantic model to dict for registry
        tool_dict = tool_data.dict()
        
        try:
            # Register the tool
            tool_model = await self.registry.register_tool(tool_dict)
            
            # Convert DB model to API model
            return Tool(
                id=tool_model.id,
                name=tool_model.name,
                description=tool_model.description,
                capability=tool_model.capability,
                source=tool_model.source,
                documentation_url=tool_model.documentation_url,
                schema=tool_model.schema,
                integration_type=tool_model.integration_type,
                status=tool_model.status,
                version=tool_model.version,
                created_at=tool_model.created_at,
                updated_at=tool_model.updated_at,
                discovery_context=tool_model.discovery_context,
                security_score=tool_model.security_score,
                performance_score=tool_model.performance_score,
                compatibility_score=tool_model.compatibility_score,
                overall_score=tool_model.overall_score,
                last_evaluated_at=tool_model.last_evaluated_at,
            )
        except (ToolRegistrationError, ToolValidationError) as e:
            logger.error(f"Error registering tool: {str(e)}")
            raise
    
    async def get_tool(self, tool_id: UUID) -> Tool:
        """
        Get a tool by ID.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool: Tool if found
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Getting tool: {tool_id}")
        
        try:
            # Get the tool
            tool_model = await self.registry.get_tool(tool_id)
            
            # Convert DB model to API model
            return Tool(
                id=tool_model.id,
                name=tool_model.name,
                description=tool_model.description,
                capability=tool_model.capability,
                source=tool_model.source,
                documentation_url=tool_model.documentation_url,
                schema=tool_model.schema,
                integration_type=tool_model.integration_type,
                status=tool_model.status,
                version=tool_model.version,
                created_at=tool_model.created_at,
                updated_at=tool_model.updated_at,
                discovery_context=tool_model.discovery_context,
                security_score=tool_model.security_score,
                performance_score=tool_model.performance_score,
                compatibility_score=tool_model.compatibility_score,
                overall_score=tool_model.overall_score,
                last_evaluated_at=tool_model.last_evaluated_at,
            )
        except ToolNotFoundError as e:
            logger.error(f"Tool not found: {str(e)}")
            raise
    
    async def update_tool(self, tool_id: UUID, tool_data: ToolUpdate) -> Tool:
        """
        Update a tool.
        
        Args:
            tool_id: Tool ID
            tool_data: Tool data for update
            
        Returns:
            Tool: Updated tool
            
        Raises:
            ToolNotFoundError: If tool not found
            ToolValidationError: If update data is invalid
        """
        logger.info(f"Updating tool: {tool_id}")
        
        # Convert Pydantic model to dict, excluding None values
        update_data = {k: v for k, v in tool_data.dict().items() if v is not None}
        
        try:
            # Update the tool
            tool_model = await self.registry.update_tool(tool_id, update_data)
            
            # Convert DB model to API model
            return Tool(
                id=tool_model.id,
                name=tool_model.name,
                description=tool_model.description,
                capability=tool_model.capability,
                source=tool_model.source,
                documentation_url=tool_model.documentation_url,
                schema=tool_model.schema,
                integration_type=tool_model.integration_type,
                status=tool_model.status,
                version=tool_model.version,
                created_at=tool_model.created_at,
                updated_at=tool_model.updated_at,
                discovery_context=tool_model.discovery_context,
                security_score=tool_model.security_score,
                performance_score=tool_model.performance_score,
                compatibility_score=tool_model.compatibility_score,
                overall_score=tool_model.overall_score,
                last_evaluated_at=tool_model.last_evaluated_at,
            )
        except (ToolNotFoundError, ToolValidationError) as e:
            logger.error(f"Error updating tool: {str(e)}")
            raise
    
    async def delete_tool(self, tool_id: UUID) -> None:
        """
        Delete a tool.
        
        Args:
            tool_id: Tool ID
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Deleting tool: {tool_id}")
        
        try:
            # Delete the tool
            await self.registry.delete_tool(tool_id)
        except ToolNotFoundError as e:
            logger.error(f"Tool not found: {str(e)}")
            raise
    
    async def list_tools(
        self,
        capability: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        integration_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List tools with filtering and pagination.
        
        Args:
            capability: Optional capability filter
            source: Optional source filter
            status: Optional status filter
            integration_type: Optional integration type filter
            page: Page number
            page_size: Page size
            
        Returns:
            PaginatedResponse: Paginated list of tools
        """
        logger.info(f"Listing tools (capability={capability}, source={source}, status={status})")
        
        try:
            # Get tools from registry
            tools, total = await self.registry.list_tools(
                capability=capability,
                source=source,
                status=status,
                integration_type=integration_type,
                page=page,
                page_size=page_size,
            )
            
            # Convert DB models to API models
            tool_items = [
                Tool(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    capability=t.capability,
                    source=t.source,
                    documentation_url=t.documentation_url,
                    schema=t.schema,
                    integration_type=t.integration_type,
                    status=t.status,
                    version=t.version,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    discovery_context=t.discovery_context,
                    security_score=t.security_score,
                    performance_score=t.performance_score,
                    compatibility_score=t.compatibility_score,
                    overall_score=t.overall_score,
                    last_evaluated_at=t.last_evaluated_at,
                )
                for t in tools
            ]
            
            # Calculate pages
            pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            return PaginatedResponse(
                items=tool_items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
            )
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            raise
    
    async def search_tools_by_capability(
        self,
        capability: str,
        min_score: float = 0.5,
        limit: int = 10,
    ) -> List[ToolSummary]:
        """
        Search for tools matching a capability.
        
        Args:
            capability: Capability to search for
            min_score: Minimum match score
            limit: Maximum number of results
            
        Returns:
            List[ToolSummary]: Matching tools
        """
        logger.info(f"Searching for tools with capability: {capability}")
        
        try:
            # Search tools by capability
            tools = await self.registry.search_tools_by_capability(
                capability=capability,
                min_score=min_score,
                limit=limit,
            )
            
            # Convert DB models to API models
            return [
                ToolSummary(
                    id=t.id,
                    name=t.name,
                    capability=t.capability,
                    source=t.source,
                    integration_type=t.integration_type,
                    status=t.status,
                    security_score=t.security_score,
                    overall_score=t.overall_score,
                )
                for t in tools
            ]
        except Exception as e:
            logger.error(f"Error searching tools: {str(e)}")
            raise
    
    async def approve_tool(self, tool_id: UUID) -> Tool:
        """
        Approve a tool for use.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool: Approved tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Approving tool: {tool_id}")
        
        try:
            # Approve the tool
            tool_model = await self.registry.approve_tool(tool_id)
            
            # Convert DB model to API model
            return Tool(
                id=tool_model.id,
                name=tool_model.name,
                description=tool_model.description,
                capability=tool_model.capability,
                source=tool_model.source,
                documentation_url=tool_model.documentation_url,
                schema=tool_model.schema,
                integration_type=tool_model.integration_type,
                status=tool_model.status,
                version=tool_model.version,
                created_at=tool_model.created_at,
                updated_at=tool_model.updated_at,
                discovery_context=tool_model.discovery_context,
                security_score=tool_model.security_score,
                performance_score=tool_model.performance_score,
                compatibility_score=tool_model.compatibility_score,
                overall_score=tool_model.overall_score,
                last_evaluated_at=tool_model.last_evaluated_at,
            )
        except ToolNotFoundError as e:
            logger.error(f"Tool not found: {str(e)}")
            raise
    
    async def deprecate_tool(self, tool_id: UUID) -> Tool:
        """
        Deprecate a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool: Deprecated tool
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Deprecating tool: {tool_id}")
        
        try:
            # Deprecate the tool
            tool_model = await self.registry.deprecate_tool(tool_id)
            
            # Convert DB model to API model
            return Tool(
                id=tool_model.id,
                name=tool_model.name,
                description=tool_model.description,
                capability=tool_model.capability,
                source=tool_model.source,
                documentation_url=tool_model.documentation_url,
                schema=tool_model.schema,
                integration_type=tool_model.integration_type,
                status=tool_model.status,
                version=tool_model.version,
                created_at=tool_model.created_at,
                updated_at=tool_model.updated_at,
                discovery_context=tool_model.discovery_context,
                security_score=tool_model.security_score,
                performance_score=tool_model.performance_score,
                compatibility_score=tool_model.compatibility_score,
                overall_score=tool_model.overall_score,
                last_evaluated_at=tool_model.last_evaluated_at,
            )
        except ToolNotFoundError as e:
            logger.error(f"Tool not found: {str(e)}")
            raise
    
    async def batch_register_tools(self, tools_data: List[ToolCreate]) -> BatchRegistrationResponse:
        """
        Register multiple tools in a batch operation.
        
        Args:
            tools_data: List of tool data for creation
            
        Returns:
            BatchRegistrationResponse: Registration results
        """
        logger.info(f"Batch registering {len(tools_data)} tools")
        
        successful = []
        failed = []
        
        # Convert Pydantic models to dicts
        tools_dicts = [t.dict() for t in tools_data]
        
        try:
            # Register tools in batch
            registered_tools = await self.registry.register_many(tools_dicts)
            
            # Convert DB models to API models
            for t in registered_tools:
                successful.append(
                    Tool(
                        id=t.id,
                        name=t.name,
                        description=t.description,
                        capability=t.capability,
                        source=t.source,
                        documentation_url=t.documentation_url,
                        schema=t.schema,
                        integration_type=t.integration_type,
                        status=t.status,
                        version=t.version,
                        created_at=t.created_at,
                        updated_at=t.updated_at,
                        discovery_context=t.discovery_context,
                        security_score=t.security_score,
                        performance_score=t.performance_score,
                        compatibility_score=t.compatibility_score,
                        overall_score=t.overall_score,
                        last_evaluated_at=t.last_evaluated_at,
                    )
                )
        except ToolRegistrationError as e:
            # If the registry.register_many method fails catastrophically,
            # we won't have individual failure information, just an overall error
            logger.error(f"Batch registration failed: {str(e)}")
            
            # Add all tools to failed list
            for i, t in enumerate(tools_data):
                failed.append({
                    "data": t.dict(),
                    "error": f"Batch registration failed: {str(e)}",
                    "index": i
                })
        
        return BatchRegistrationResponse(
            successful=successful,
            failed=failed,
        )
    
    # Tool discovery operations
    
    async def discover_tools(self, discovery_request: ToolDiscoveryRequest) -> DiscoveryResponse:
        """
        Discover tools based on requirements.
        
        Args:
            discovery_request: Discovery request
            
        Returns:
            DiscoveryResponse: Discovery response with discovered tools
            
        Raises:
            ToolDiscoveryError: If discovery fails
        """
        logger.info(f"Discovering tools for project: {discovery_request.project_id}")
        
        try:
            # Create discovery request record
            discovery_id = uuid.uuid4()
            discovery_data = {
                "id": discovery_id,
                "project_id": discovery_request.project_id,
                "requirements": discovery_request.requirements,
                "context": discovery_request.context,
                "initiated_at": datetime.utcnow(),
                "status": "PENDING",
            }
            
            discovery_record = await self.repository.create_discovery_request(discovery_data)
            
            # Discover tools
            discovered_tools = await self.discovery_service.discover_tools(
                discovery_request.requirements,
                discovery_request.context,
            )
            
            # Update discovery request record
            await self.repository.update_discovery_request(
                discovery_id,
                {
                    "status": "COMPLETED",
                    "completed_at": datetime.utcnow(),
                    "discovered_tool_count": len(discovered_tools),
                }
            )
            
            # Convert discovered tools to API model
            tool_summaries = [
                ToolSummary(
                    id=None,  # These tools are not yet registered
                    name=t["name"],
                    capability=t["capability"],
                    source=t["source"],
                    integration_type=t.get("integration_type"),
                    status=ToolStatus.DISCOVERED,
                    security_score=None,
                    overall_score=t.get("match_score", 0.0),
                )
                for t in discovered_tools
            ]
            
            return DiscoveryResponse(
                request_id=discovery_id,
                discovered_tools=tool_summaries,
                discovery_timestamp=datetime.utcnow(),
                context=discovery_request.context,
            )
        except Exception as e:
            logger.error(f"Error discovering tools from source: {str(e)}")
            
            # Update discovery request record if it was created
            if "discovery_record" in locals():
                await self.repository.update_discovery_request(
                    discovery_id,
                    {
                        "status": "FAILED",
                        "error": str(e),
                    }
                )
            
            raise ToolDiscoveryError(f"Tool discovery failed: {str(e)}")
    
    async def delete_discovery_request(self, discovery_id: UUID) -> None:
        """
        Delete a discovery request.
        
        Args:
            discovery_id: Discovery request ID
            
        Raises:
            ToolDiscoveryError: If discovery request not found
        """
        logger.info(f"Deleting discovery request: {discovery_id}")
        
        # Get discovery request to ensure it exists
        discovery_record = await self.repository.get_discovery_request(discovery_id)
        if not discovery_record:
            raise ToolDiscoveryError(f"Discovery request not found: {discovery_id}")
        
        # Delete the discovery request
        # In this implementation, we don't have a delete method on the repository
        # In a real implementation, we would add this method and call it here
        
        # For now, just update the status to "DELETED"
        await self.repository.update_discovery_request(
            discovery_id,
            {
                "status": "DELETED",
            }
        )
    
    # Tool evaluation operations
    
    async def evaluate_tool(
        self,
        tool_id: UUID,
        criteria: Dict[EvaluationCriteriaType, bool],
        context: Optional[Dict[str, Any]] = None,
    ) -> ComprehensiveEvaluationResult:
        """
        Evaluate a tool against specified criteria.
        
        Args:
            tool_id: Tool ID
            criteria: Evaluation criteria
            context: Optional evaluation context
            
        Returns:
            ComprehensiveEvaluationResult: Evaluation results
            
        Raises:
            ToolNotFoundError: If tool not found
            ToolEvaluationError: If evaluation fails
        """
        logger.info(f"Evaluating tool: {tool_id}")
        
        try:
            # Get the tool to ensure it exists
            tool = await self.registry.get_tool(tool_id)
            
            # Evaluate the tool
            evaluation_result = await self.evaluation_service.evaluate_tool(
                tool, criteria, context
            )
            
            # Store evaluation results
            evaluation_id = uuid.uuid4()
            evaluation_data = {
                "id": evaluation_id,
                "tool_id": tool_id,
                "evaluation_timestamp": datetime.utcnow(),
                "overall_score": evaluation_result.overall_score,
                "security_evaluation": evaluation_result.security.dict() if evaluation_result.security else None,
                "performance_evaluation": evaluation_result.performance.dict() if evaluation_result.performance else None,
                "compatibility_evaluation": evaluation_result.compatibility.dict() if evaluation_result.compatibility else None,
                "usability_score": evaluation_result.usability_score,
                "reliability_score": evaluation_result.reliability_score,
                "recommendation": evaluation_result.recommendation,
                "context": context,
            }
            
            evaluation_record = await self.repository.create_evaluation(evaluation_data)
            
            # Update tool with evaluation results
            await self.registry.update_evaluation(tool_id, {
                "overall_score": evaluation_result.overall_score,
                "security_score": evaluation_result.security.score if evaluation_result.security else None,
                "performance_score": evaluation_result.performance.score if evaluation_result.performance else None,
                "compatibility_score": evaluation_result.compatibility.score if evaluation_result.compatibility else None,
            })
            
            return evaluation_result
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error evaluating tool: {str(e)}")
            raise ToolEvaluationError(f"Error evaluating tool: {str(e)}", {"tool_id": str(tool_id)})
    
    async def get_tool_evaluations(
        self,
        tool_id: UUID,
        limit: int = 10,
    ) -> List[ToolEvaluationResult]:
        """
        Get evaluation history for a tool.
        
        Args:
            tool_id: Tool ID
            limit: Maximum number of evaluations
            
        Returns:
            List[ToolEvaluationResult]: List of evaluation results
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        logger.info(f"Getting evaluations for tool: {tool_id}")
        
        try:
            # Get the tool to ensure it exists
            await self.registry.get_tool(tool_id)
            
            # Get evaluations
            evaluations = await self.repository.get_tool_evaluations(tool_id, limit)
            
            # Convert DB models to API models
            return [
                ToolEvaluationResult(
                    id=e.id,
                    tool_id=e.tool_id,
                    timestamp=e.evaluation_timestamp,
                    overall_score=e.overall_score,
                    security_score=e.security_evaluation.get("score") if e.security_evaluation else None,
                    performance_score=e.performance_evaluation.get("score") if e.performance_evaluation else None,
                    compatibility_score=e.compatibility_evaluation.get("score") if e.compatibility_evaluation else None,
                    recommendation=e.recommendation,
                )
                for e in evaluations
            ]
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error getting tool evaluations: {str(e)}")
            raise
    
    async def get_evaluation(self, evaluation_id: UUID) -> ComprehensiveEvaluationResult:
        """
        Get a specific evaluation by ID.
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            ComprehensiveEvaluationResult: Evaluation result
            
        Raises:
            ToolEvaluationError: If evaluation not found
        """
        logger.info(f"Getting evaluation: {evaluation_id}")
        
        try:
            # Get evaluation record
            evaluation_record = await self.repository.get_evaluation(evaluation_id)
            if not evaluation_record:
                raise ToolEvaluationError(f"Evaluation not found: {evaluation_id}")
            
            # Convert DB model to API model
            result = ComprehensiveEvaluationResult(
                tool_id=evaluation_record.tool_id,
                evaluation_id=evaluation_record.id,
                evaluation_timestamp=evaluation_record.evaluation_timestamp,
                overall_score=evaluation_record.overall_score,
                security=None,
                performance=None,
                compatibility=None,
                usability_score=evaluation_record.usability_score,
                reliability_score=evaluation_record.reliability_score,
                recommendation=evaluation_record.recommendation,
                context=evaluation_record.context,
            )
            
            # Add detailed evaluation results if available
            if evaluation_record.security_evaluation:
                result.security = SecurityEvaluationResult(**evaluation_record.security_evaluation)
            
            if evaluation_record.performance_evaluation:
                result.performance = PerformanceEvaluationResult(**evaluation_record.performance_evaluation)
            
            if evaluation_record.compatibility_evaluation:
                result.compatibility = CompatibilityEvaluationResult(**evaluation_record.compatibility_evaluation)
            
            return result
        except Exception as e:
            if isinstance(e, ToolEvaluationError):
                raise
            logger.error(f"Error getting evaluation: {str(e)}")
            raise ToolEvaluationError(f"Error getting evaluation: {str(e)}")
    
    async def list_evaluations(
        self,
        tool_id: Optional[UUID] = None,
        evaluation_type: Optional[EvaluationCriteriaType] = None,
        min_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List evaluations with filtering and pagination.
        
        Args:
            tool_id: Optional tool ID filter
            evaluation_type: Optional evaluation type filter
            min_score: Optional minimum score filter
            page: Page number
            page_size: Page size
            
        Returns:
            PaginatedResponse: Paginated list of evaluations
        """
        logger.info(f"Listing evaluations (tool_id={tool_id}, type={evaluation_type})")
        
        try:
            # Get evaluations
            evaluations, total = await self.repository.list_evaluations(
                tool_id=tool_id,
                evaluation_type=evaluation_type.value if evaluation_type else None,
                min_score=min_score,
                page=page,
                page_size=page_size,
            )
            
            # Convert DB models to API models
            evaluation_items = [
                ToolEvaluationResult(
                    id=e.id,
                    tool_id=e.tool_id,
                    timestamp=e.evaluation_timestamp,
                    overall_score=e.overall_score,
                    security_score=e.security_evaluation.get("score") if e.security_evaluation else None,
                    performance_score=e.performance_evaluation.get("score") if e.performance_evaluation else None,
                    compatibility_score=e.compatibility_evaluation.get("score") if e.compatibility_evaluation else None,
                    recommendation=e.recommendation,
                )
                for e in evaluations
            ]
            
            # Calculate pages
            pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            return PaginatedResponse(
                items=evaluation_items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
            )
        except Exception as e:
            logger.error(f"Error listing evaluations: {str(e)}")
            raise
    
    async def batch_evaluate_tools(
        self,
        evaluation_requests: List[EvaluationRequest],
    ) -> BatchEvaluationResponse:
        """
        Evaluate multiple tools in a batch operation.
        
        Args:
            evaluation_requests: List of evaluation requests
            
        Returns:
            BatchEvaluationResponse: Batch evaluation results
        """
        logger.info(f"Batch evaluating {len(evaluation_requests)} tools")
        
        successful = []
        failed = []
        
        for request in evaluation_requests:
            try:
                # Evaluate the tool
                evaluation_result = await self.evaluate_tool(
                    request.tool_id,
                    request.criteria,
                    request.context,
                )
                
                # Convert to ToolEvaluationResult
                result = ToolEvaluationResult(
                    id=evaluation_result.evaluation_id,
                    tool_id=evaluation_result.tool_id,
                    timestamp=evaluation_result.evaluation_timestamp,
                    overall_score=evaluation_result.overall_score,
                    security_score=evaluation_result.security.score if evaluation_result.security else None,
                    performance_score=evaluation_result.performance.score if evaluation_result.performance else None,
                    compatibility_score=evaluation_result.compatibility.score if evaluation_result.compatibility else None,
                    recommendation=evaluation_result.recommendation,
                )
                
                successful.append(result)
            except Exception as e:
                logger.warning(f"Failed to evaluate tool {request.tool_id}: {str(e)}")
                failed.append({
                    "tool_id": str(request.tool_id),
                    "error": str(e),
                })
        
        return BatchEvaluationResponse(
            successful=successful,
            failed=failed,
        )
    
    # Tool integration operations
    
    async def integrate_tool(
        self,
        integration_request: ToolIntegrationRequest,
    ) -> ToolIntegrationResponse:
        """
        Integrate a tool with an agent.
        
        Args:
            integration_request: Integration request
            
        Returns:
            ToolIntegrationResponse: Integration details
            
        Raises:
            ToolNotFoundError: If tool not found
            SecurityViolationError: If integration violates security policies
            ToolValidationError: If integration configuration is invalid
        """
        logger.info(f"Integrating tool {integration_request.tool_id} with agent {integration_request.agent_id}")
        
        try:
            # Get the tool to ensure it exists
            tool = await self.registry.get_tool(integration_request.tool_id)
            
            # Check security constraints
            security_check = await self.security_scanner.check_integration_security(
                tool, integration_request.configuration, integration_request.permissions
            )
            
            if not security_check.approved:
                raise SecurityViolationError(
                    f"Integration denied due to security concerns: {security_check.reason}",
                    {"violation_type": security_check.violation_type}
                )
            
            # Register the integration
            integration_data = {
                "tool_id": integration_request.tool_id,
                "agent_id": integration_request.agent_id,
                "configuration": integration_request.configuration,
                "permissions": integration_request.permissions,
                "status": "ACTIVE",
                "integrated_at": datetime.utcnow(),
            }
            
            integration = await self.registry.register_integration(integration_data)
            
            # Create integration adapter
            adapter = await self.integration_service.create_adapter(
                tool, integration_request.configuration
            )
            
            # Setup any additional integration requirements
            await adapter.setup()
            
            # Return integration details
            return ToolIntegrationResponse(
                id=integration["id"],
                tool_id=integration["tool_id"],
                agent_id=integration["agent_id"],
                configuration=integration["configuration"],
                permissions=integration["permissions"],
                integrated_at=integration["integrated_at"],
                status=integration["status"],
                created_at=integration["created_at"],
                updated_at=integration["updated_at"],
            )
        except Exception as e:
            if isinstance(e, (ToolNotFoundError, SecurityViolationError, ToolValidationError)):
                raise
            logger.error(f"Error integrating tool: {str(e)}")
            raise ToolIntegrationError(f"Error integrating tool: {str(e)}")
    
    async def get_integration(
        self,
        agent_id: UUID,
        tool_id: UUID,
    ) -> ToolIntegrationResponse:
        """
        Get details of a specific tool integration.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            
        Returns:
            ToolIntegrationResponse: Integration details
            
        Raises:
            ToolNotFoundError: If integration not found
        """
        logger.info(f"Getting integration for tool {tool_id} with agent {agent_id}")
        
        try:
            # Get the integration
            integration = await self.repository.get_integration(tool_id, agent_id)
            if not integration:
                raise ToolNotFoundError(f"Integration not found for tool {tool_id} and agent {agent_id}")
            
            # Return integration details
            return ToolIntegrationResponse(
                id=integration.id,
                tool_id=integration.tool_id,
                agent_id=integration.agent_id,
                configuration=integration.configuration,
                permissions=integration.permissions,
                integrated_at=integration.integrated_at,
                status=integration.status,
                created_at=integration.created_at,
                updated_at=integration.updated_at,
            )
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error getting integration: {str(e)}")
            raise ToolIntegrationError(f"Error getting integration: {str(e)}")
    
    async def update_integration(
        self,
        agent_id: UUID,
        tool_id: UUID,
        update_data: ToolIntegrationUpdateRequest,
    ) -> ToolIntegrationResponse:
        """
        Update a tool integration.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            update_data: Integration data to update
            
        Returns:
            ToolIntegrationResponse: Updated integration details
            
        Raises:
            ToolNotFoundError: If integration not found
            ToolValidationError: If update data is invalid
        """
        logger.info(f"Updating integration for tool {tool_id} with agent {agent_id}")
        
        try:
            # Get the integration to ensure it exists
            integration = await self.repository.get_integration(tool_id, agent_id)
            if not integration:
                raise ToolNotFoundError(f"Integration not found for tool {tool_id} and agent {agent_id}")
            
            # Convert Pydantic model to dict, excluding None values
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            
            # Update the integration
            updated_integration = await self.repository.update_integration(
                tool_id, agent_id, update_dict
            )
            
            # Return updated integration details
            return ToolIntegrationResponse(
                id=updated_integration.id,
                tool_id=updated_integration.tool_id,
                agent_id=updated_integration.agent_id,
                configuration=updated_integration.configuration,
                permissions=updated_integration.permissions,
                integrated_at=updated_integration.integrated_at,
                status=updated_integration.status,
                created_at=updated_integration.created_at,
                updated_at=updated_integration.updated_at,
            )
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error updating integration: {str(e)}")
            raise ToolValidationError(f"Error updating integration: {str(e)}")
    
    async def remove_integration(
        self,
        agent_id: UUID,
        tool_id: UUID,
    ) -> None:
        """
        Remove a tool integration.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            
        Raises:
            ToolNotFoundError: If integration not found
        """
        logger.info(f"Removing integration for tool {tool_id} from agent {agent_id}")
        
        try:
            # Get the integration to ensure it exists
            integration = await self.repository.get_integration(tool_id, agent_id)
            if not integration:
                raise ToolNotFoundError(f"Integration not found for tool {tool_id} and agent {agent_id}")
            
            # Remove the integration
            deleted = await self.repository.delete_integration(tool_id, agent_id)
            if not deleted:
                raise ToolNotFoundError(f"Integration not found for tool {tool_id} and agent {agent_id}")
        except Exception as e:
            if isinstance(e, ToolNotFoundError):
                raise
            logger.error(f"Error removing integration: {str(e)}")
            raise ToolIntegrationError(f"Error removing integration: {str(e)}")
    
    async def list_agent_tools(
        self,
        agent_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List tools integrated with an agent.
        
        Args:
            agent_id: Agent ID
            status: Optional integration status filter
            page: Page number
            page_size: Page size
            
        Returns:
            PaginatedResponse: Paginated list of integrated tools
        """
        logger.info(f"Listing tools for agent: {agent_id}")
        
        try:
            # Get agent tool integrations
            integrations, total = await self.repository.list_agent_tools(
                agent_id=agent_id,
                status=status,
                page=page,
                page_size=page_size,
            )
            
            # Convert DB models to API models
            integration_items = [
                ToolIntegrationResponse(
                    id=i.id,
                    tool_id=i.tool_id,
                    agent_id=i.agent_id,
                    configuration=i.configuration,
                    permissions=i.permissions,
                    integrated_at=i.integrated_at,
                    status=i.status,
                    created_at=i.created_at,
                    updated_at=i.updated_at,
                )
                for i in integrations
            ]
            
            # Calculate pages
            pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            return PaginatedResponse(
                items=integration_items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
            )
        except Exception as e:
            logger.error(f"Error listing agent tools: {str(e)}")
            raise
    
    async def list_all_integrations(
        self,
        tool_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List all tool integrations with filtering and pagination.
        
        Args:
            tool_id: Optional tool ID filter
            agent_id: Optional agent ID filter
            status: Optional integration status filter
            page: Page number
            page_size: Page size
            
        Returns:
            PaginatedResponse: Paginated list of tool integrations
        """
        logger.info(f"Listing all integrations (tool_id={tool_id}, agent_id={agent_id}, status={status})")
        
        try:
            # Get all integrations
            integrations, total = await self.repository.list_all_integrations(
                tool_id=tool_id,
                agent_id=agent_id,
                status=status,
                page=page,
                page_size=page_size,
            )
            
            # Convert DB models to API models
            integration_items = [
                ToolIntegrationResponse(
                    id=i.id,
                    tool_id=i.tool_id,
                    agent_id=i.agent_id,
                    configuration=i.configuration,
                    permissions=i.permissions,
                    integrated_at=i.integrated_at,
                    status=i.status,
                    created_at=i.created_at,
                    updated_at=i.updated_at,
                )
                for i in integrations
            ]
            
            # Calculate pages
            pages = (total + page_size - 1) // page_size if page_size > 0 else 0
            
            return PaginatedResponse(
                items=integration_items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
            )
        except Exception as e:
            logger.error(f"Error listing integrations: {str(e)}")
            raise
    
    # Tool execution operations
    
    async def execute_tool(
        self,
        execution_request: ToolExecutionRequest,
    ) -> ToolExecutionResponse:
        """
        Execute a tool with provided parameters.
        
        Args:
            execution_request: Tool execution request
            
        Returns:
            ToolExecutionResponse: Execution response
            
        Raises:
            ToolNotFoundError: If tool or integration not found
            ToolValidationError: If execution parameters are invalid
            SecurityViolationError: If execution violates security policies
            ToolExecutionTimeoutError: If execution times out
            ToolExecutionError: If execution fails
        """
        logger.info(f"Executing tool {execution_request.tool_id} for agent {execution_request.agent_id}")
        
        try:
            # Get the tool
            tool = await self.registry.get_tool(execution_request.tool_id)
            
            # Get the integration
            integration = await self.repository.get_integration(
                execution_request.tool_id, execution_request.agent_id
            )
            if not integration:
                raise ToolNotFoundError(
                    f"Integration not found for tool {execution_request.tool_id} and agent {execution_request.agent_id}"
                )
            
            # Validate parameters against schema
            if tool.schema:
                validation_result = await self.integration_service.validate_parameters(
                    tool.schema, execution_request.parameters
                )
                if not validation_result.valid:
                    raise ToolValidationError(
                        f"Invalid parameters: {validation_result.errors}",
                        {"validation_errors": validation_result.errors}
                    )
            
            # Create execution record
            execution_id = uuid.uuid4()
            execution_data = {
                "id": execution_id,
                "tool_id": execution_request.tool_id,
                "agent_id": execution_request.agent_id,
                "parameters": execution_request.parameters,
                "execution_context": execution_request.execution_context,
                "mode": execution_request.mode,
                "callback_id": execution_request.callback_id,
                "started_at": datetime.utcnow(),
                "status": "RUNNING",
            }
            
            execution_record = await self.repository.create_execution(execution_data)
            
            # Update integration usage statistics
            await self.repository.update_integration_usage(
                execution_request.tool_id, execution_request.agent_id
            )
            
            # Get appropriate adapter for this tool
            adapter = await self.integration_service.get_adapter(
                tool, integration.configuration
            )
            
            # Execute the tool
            execution_start = datetime.utcnow()
            
            if execution_request.mode == ExecutionMode.SYNCHRONOUS:
                # Execute synchronously
                execution_result = await adapter.execute(
                    execution_request.parameters,
                    timeout=execution_request.timeout_seconds,
                    context=execution_request.execution_context,
                )
                
                # Calculate execution time
                execution_end = datetime.utcnow()
                execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
                
                # Update execution record
                await self.repository.update_execution(
                    execution_id,
                    {
                        "completed_at": execution_end,
                        "execution_time_ms": execution_time_ms,
                        "result": execution_result.result,
                        "error": execution_result.error,
                        "success": execution_result.success,
                        "status": "COMPLETED" if execution_result.success else "FAILED",
                    }
                )
                
                # Log execution details
                await self.repository.create_execution_log(
                    {
                        "execution_id": execution_id,
                        "timestamp": datetime.utcnow(),
                        "level": "INFO" if execution_result.success else "ERROR",
                        "message": f"Tool execution {'succeeded' if execution_result.success else 'failed'}",
                        "data": {
                            "execution_time_ms": execution_time_ms,
                            "result": execution_result.result,
                            "error": execution_result.error,
                        },
                    }
                )
                
                # Return execution response
                return ToolExecutionResponse(
                    execution_id=execution_id,
                    tool_id=execution_request.tool_id,
                    agent_id=execution_request.agent_id,
                    started_at=execution_start,
                    completed_at=execution_end,
                    execution_time_ms=execution_time_ms,
                    status="COMPLETED" if execution_result.success else "FAILED",
                    result=execution_result.result,
                    error=execution_result.error,
                    logs=None,  # Logs would be fetched separately
                )
            else:
                # For asynchronous execution, just start the execution and return
                # In a real implementation, this would involve a background task system
                
                # Start execution asynchronously
                # This is a placeholder - in a real system, you would use a task queue
                # or other background task mechanism
                # For now, just return a placeholder response
                
                return ToolExecutionResponse(
                    execution_id=execution_id,
                    tool_id=execution_request.tool_id,
                    agent_id=execution_request.agent_id,
                    started_at=execution_start,
                    completed_at=None,
                    execution_time_ms=None,
                    status="RUNNING",
                    result=None,
                    error=None,
                    logs=None,
                )
        except Exception as e:
            if isinstance(e, (ToolNotFoundError, ToolValidationError, SecurityViolationError, ToolExecutionTimeoutError)):
                raise
            logger.error(f"Error executing tool: {str(e)}")
            raise ToolExecutionError(f"Error executing tool: {str(e)}")
    
    async def get_execution_status(
        self,
        execution_id: UUID,
    ) -> ToolExecutionResponse:
        """
        Get status of a tool execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            ToolExecutionResponse: Execution status
            
        Raises:
            ToolExecutionError: If execution not found
        """
        logger.info(f"Getting execution status: {execution_id}")
        
        try:
            # Get execution record
            execution = await self.repository.get_execution(execution_id)
            if not execution:
                raise ToolExecutionError(f"Execution not found: {execution_id}")
            
            # Return execution status
            return ToolExecutionResponse(
                execution_id=execution.id,
                tool_id=execution.tool_id,
                agent_id=execution.agent_id,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                execution_time_ms=execution.execution_time_ms,
                status=execution.status,
                result=execution.result,
                error=execution.error,
                logs=None,  # Logs would be fetched separately
            )
        except Exception as e:
            if isinstance(e, ToolExecutionError):
                raise
            logger.error(f"Error getting execution status: {str(e)}")
            raise ToolExecutionError(f"Error getting execution status: {str(e)}")
