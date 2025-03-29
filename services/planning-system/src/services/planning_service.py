"""
Planning Service facade for the Planning System service.

This module implements the main facade service that coordinates all planning components.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.src.messaging import EventBus, CommandBus

from ..config import PlanningSystemConfig as Settings
from ..models.api import (
    StrategicPlanCreate, 
    StrategicPlanUpdate, 
    StrategicPlanResponse,
    PlanningTaskCreate,
    PlanningTaskUpdate,
    PlanningTaskResponse,
    DependencyCreate,
    DependencyUpdate,
    DependencyResponse,
    PaginatedResponse,
    TimelineForecast,
    BottleneckAnalysis,
    OptimizationRequest,
    OptimizationResult,
    PlanStatus
)
from ..exceptions import (
    PlanNotFoundError,
    TaskNotFoundError,
    InvalidDependencyError,
    ResourceAllocationError,
    ForecastingError
)

# Import component classes
from .strategic_planner import StrategicPlanner
from .tactical_planner import TacticalPlanner
from .forecaster import ProjectForecaster
from .resource_optimizer import ResourceOptimizer
from .resource_service import ResourceService
from .dependency_manager import DependencyManager
from .base_service import BaseService

logger = logging.getLogger(__name__)

class PlanningService:
    """
    Facade service for the Planning System.
    
    This service coordinates interactions between specialized planning components
    and provides a unified API for the Planning System service.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        strategic_planner: StrategicPlanner,
        tactical_planner: TacticalPlanner,
        forecaster: ProjectForecaster,
        resource_optimizer: ResourceOptimizer,
        resource_service: ResourceService,
        dependency_manager: DependencyManager,
        event_bus: EventBus,
        command_bus: CommandBus,
        settings: Settings,
        task_template_service: Optional["TaskTemplateService"] = None,
        dependency_type_service: Optional["DependencyTypeService"] = None,
        what_if_analysis_service: Optional["WhatIfAnalysisService"] = None,
    ):
        """
        Initialize the planning service.
        
        Args:
            db: Database session
            strategic_planner: Strategic planner component
            tactical_planner: Tactical planner component
            forecaster: Project forecaster component
            resource_optimizer: Resource optimizer component
            resource_service: Resource service component
            dependency_manager: Dependency manager component
            event_bus: Event bus
            command_bus: Command bus
            settings: Application settings
            task_template_service: Optional task template service component
            dependency_type_service: Optional dependency type service component
            what_if_analysis_service: Optional what-if analysis service component
        """
        # Store components
        self.strategic_planner = strategic_planner
        self.tactical_planner = tactical_planner
        self.forecaster = forecaster
        self.resource_optimizer = resource_optimizer
        self.resource_service = resource_service
        self.dependency_manager = dependency_manager
        self.task_template_service = task_template_service
        self.dependency_type_service = dependency_type_service
        self.what_if_analysis_service = what_if_analysis_service
        
        # Store dependencies
        self.db = db
        self.event_bus = event_bus
        self.command_bus = command_bus
        self.settings = settings
        
        logger.info("Planning Service initialized")
    
    # Plan management methods
    
    async def create_plan(self, plan_data: StrategicPlanCreate) -> StrategicPlanResponse:
        """
        Create a new strategic plan.
        
        Args:
            plan_data: Plan data
            
        Returns:
            StrategicPlanResponse: Created plan
            
        Raises:
            Exception: If plan creation fails
        """
        logger.info(f"Creating plan {plan_data.name} for project {plan_data.project_id}")
        return await self.strategic_planner.create_plan(plan_data)
    
    async def get_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Get a strategic plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            StrategicPlanResponse: Plan data
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Getting plan {plan_id}")
        return await self.strategic_planner.get_plan(plan_id)
    
    async def list_plans(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[PlanStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List strategic plans with filtering and pagination.
        
        Args:
            project_id: Optional project ID filter
            status: Optional status filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of plans
        """
        logger.info(f"Listing plans (project_id={project_id}, status={status})")
        return await self.strategic_planner.list_plans(
            project_id=project_id,
            status=status,
            page=page,
            page_size=page_size
        )
    
    async def update_plan(
        self,
        plan_id: UUID,
        plan_data: StrategicPlanUpdate
    ) -> StrategicPlanResponse:
        """
        Update a strategic plan.
        
        Args:
            plan_id: Plan ID
            plan_data: Plan data to update
            
        Returns:
            StrategicPlanResponse: Updated plan
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Updating plan {plan_id}")
        return await self.strategic_planner.update_plan(plan_id, plan_data)
    
    async def delete_plan(self, plan_id: UUID) -> None:
        """
        Delete a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Deleting plan {plan_id}")
        await self.strategic_planner.delete_plan(plan_id)
    
    async def activate_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Activate a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            StrategicPlanResponse: Activated plan
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Activating plan {plan_id}")
        return await self.strategic_planner.activate_plan(plan_id)
    
    async def clone_plan(self, plan_id: UUID) -> StrategicPlanResponse:
        """
        Clone a strategic plan.
        
        Args:
            plan_id: Source plan ID
            
        Returns:
            StrategicPlanResponse: Cloned plan
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Cloning plan {plan_id}")
        return await self.strategic_planner.clone_plan(plan_id)
    
    async def get_plan_history(self, plan_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get history of changes to a strategic plan.
        
        Args:
            plan_id: Plan ID
            limit: Maximum number of history entries
            
        Returns:
            List[Dict[str, Any]]: Plan history entries
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Getting history for plan {plan_id}")
        return await self.strategic_planner.get_plan_history(plan_id, limit)
    
    # Task management methods
    
    async def create_task(self, task_data: PlanningTaskCreate) -> PlanningTaskResponse:
        """
        Create a new planning task.
        
        Args:
            task_data: Task data
            
        Returns:
            PlanningTaskResponse: Created task
            
        Raises:
            PlanNotFoundError: If plan not found
            Exception: If task creation fails
        """
        logger.info(f"Creating task {task_data.name} for plan {task_data.plan_id}")
        return await self.tactical_planner.create_task(task_data)
    
    async def get_task(self, task_id: UUID) -> PlanningTaskResponse:
        """
        Get a planning task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            PlanningTaskResponse: Task data
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Getting task {task_id}")
        return await self.tactical_planner.get_task(task_id)
    
    async def list_tasks(
        self,
        plan_id: UUID,
        phase_id: Optional[UUID] = None,
        milestone_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List planning tasks with filtering and pagination.
        
        Args:
            plan_id: Plan ID
            phase_id: Optional phase ID filter
            milestone_id: Optional milestone ID filter
            status: Optional status filter
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of tasks
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Listing tasks for plan {plan_id}")
        return await self.tactical_planner.list_tasks(
            plan_id=plan_id,
            phase_id=phase_id,
            milestone_id=milestone_id,
            status=status,
            page=page,
            page_size=page_size
        )
    
    async def update_task(
        self,
        task_id: UUID,
        task_data: PlanningTaskUpdate
    ) -> PlanningTaskResponse:
        """
        Update a planning task.
        
        Args:
            task_id: Task ID
            task_data: Task data to update
            
        Returns:
            PlanningTaskResponse: Updated task
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Updating task {task_id}")
        return await self.tactical_planner.update_task(task_id, task_data)
    
    async def delete_task(self, task_id: UUID) -> None:
        """
        Delete a planning task.
        
        Args:
            task_id: Task ID
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Deleting task {task_id}")
        await self.tactical_planner.delete_task(task_id)
    
    # Dependency management methods
    
    async def create_dependency(self, dependency_data: DependencyCreate) -> DependencyResponse:
        """
        Create a task dependency.
        
        Args:
            dependency_data: Dependency data
            
        Returns:
            DependencyResponse: Created dependency
            
        Raises:
            TaskNotFoundError: If task not found
            InvalidDependencyError: If dependency is invalid
        """
        logger.info(f"Creating dependency from {dependency_data.from_task_id} to {dependency_data.to_task_id}")
        return await self.dependency_manager.create_dependency(dependency_data)
    
    async def update_dependency(
        self,
        from_task_id: UUID,
        to_task_id: UUID,
        dependency_data: DependencyUpdate
    ) -> DependencyResponse:
        """
        Update a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            dependency_data: Dependency data to update
            
        Returns:
            DependencyResponse: Updated dependency
            
        Raises:
            InvalidDependencyError: If dependency not found or invalid
        """
        logger.info(f"Updating dependency from {from_task_id} to {to_task_id}")
        return await self.dependency_manager.update_dependency(from_task_id, to_task_id, dependency_data)
    
    async def delete_dependency(self, from_task_id: UUID, to_task_id: UUID) -> None:
        """
        Delete a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Raises:
            InvalidDependencyError: If dependency not found
        """
        logger.info(f"Deleting dependency from {from_task_id} to {to_task_id}")
        await self.dependency_manager.delete_dependency(from_task_id, to_task_id)
    
    async def list_dependencies(
        self,
        task_id: UUID,
        direction: str = "outgoing",
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse:
        """
        List task dependencies.
        
        Args:
            task_id: Task ID
            direction: "outgoing" for dependencies, "incoming" for dependent tasks
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of dependencies
            
        Raises:
            TaskNotFoundError: If task not found
        """
        logger.info(f"Listing {direction} dependencies for task {task_id}")
        return await self.dependency_manager.list_dependencies(
            task_id=task_id,
            direction=direction,
            page=page,
            page_size=page_size
        )
    
    async def get_critical_path(self, plan_id: UUID) -> List[PlanningTaskResponse]:
        """
        Get the critical path for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List[PlanningTaskResponse]: Tasks on the critical path
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Getting critical path for plan {plan_id}")
        return await self.dependency_manager.get_critical_path(plan_id)
    
    # Forecasting methods
    
    async def create_forecast(
        self,
        plan_id: UUID,
        confidence_interval: Optional[float] = None,
        include_historical: bool = False,
        time_unit: str = "day"
    ) -> TimelineForecast:
        """
        Create a timeline forecast for a plan.
        
        Args:
            plan_id: Plan ID
            confidence_interval: Optional confidence interval (0.0-1.0)
            include_historical: Whether to include historical data
            time_unit: Time unit for forecast (hour, day, week, month)
            
        Returns:
            TimelineForecast: Generated forecast
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If forecasting fails
        """
        logger.info(f"Creating forecast for plan {plan_id}")
        return await self.forecaster.create_forecast(
            plan_id=plan_id,
            confidence_interval=confidence_interval,
            include_historical=include_historical,
            time_unit=time_unit
        )
    
    async def get_latest_forecast(self, plan_id: UUID) -> TimelineForecast:
        """
        Get the latest forecast for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            TimelineForecast: Latest forecast
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If no forecast exists
        """
        logger.info(f"Getting latest forecast for plan {plan_id}")
        return await self.forecaster.get_latest_forecast(plan_id)
    
    async def identify_bottlenecks(self, plan_id: UUID) -> BottleneckAnalysis:
        """
        Identify bottlenecks in a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            BottleneckAnalysis: Bottleneck analysis
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        logger.info(f"Identifying bottlenecks for plan {plan_id}")
        return await self.forecaster.identify_bottlenecks(plan_id)
    
    # Resource optimization methods
    
    async def optimize_resources(
        self,
        request: OptimizationRequest
    ) -> OptimizationResult:
        """
        Optimize resource allocation for a plan.
        
        Args:
            request: Optimization request
            
        Returns:
            OptimizationResult: Optimization result
            
        Raises:
            PlanNotFoundError: If plan not found
            ResourceAllocationError: If optimization fails
        """
        logger.info(f"Optimizing resources for plan {request.plan_id}")
        return await self.resource_optimizer.optimize_resources(request)
    
    async def apply_optimization(
        self,
        plan_id: UUID,
        optimization_id: UUID
    ) -> StrategicPlanResponse:
        """
        Apply optimization result to a plan.
        
        Args:
            plan_id: Plan ID
            optimization_id: Optimization result ID
            
        Returns:
            StrategicPlanResponse: Updated plan
            
        Raises:
            PlanNotFoundError: If plan not found
            ResourceAllocationError: If applying optimization fails
        """
        logger.info(f"Applying optimization {optimization_id} to plan {plan_id}")
        return await self.resource_optimizer.apply_optimization(plan_id, optimization_id)
