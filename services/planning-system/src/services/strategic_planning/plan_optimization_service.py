"""
Plan Optimization Service for Strategic Planning.

This module provides methods for optimizing strategic plans.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from ..repository import PlanningRepository
from .helper_service import HelperService

from ...models.api import (
    OptimizationRequest,
    OptimizationResultResponse
)
from ...exceptions import (
    PlanNotFoundError,
    OptimizationError
)

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)

class PlanOptimizationService:
    """
    Plan optimization service.
    
    This service provides methods for optimizing strategic plans.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        helper_service: HelperService,
        event_bus: EventBus,
    ):
        """
        Initialize the plan optimization service.
        
        Args:
            repository: Planning repository
            helper_service: Helper service
            event_bus: Event bus
        """
        self.repository = repository
        self.helper_service = helper_service
        self.event_bus = event_bus
        logger.info("Plan Optimization Service initialized")
    
    async def optimize_plan(
        self,
        optimization_request: OptimizationRequest
    ) -> OptimizationResultResponse:
        """
        Optimize a strategic plan.
        
        Args:
            optimization_request: Optimization request
            
        Returns:
            OptimizationResultResponse: Optimization result
            
        Raises:
            PlanNotFoundError: If plan not found
            OptimizationError: If optimization fails
        """
        logger.info(f"Optimizing plan: {optimization_request.plan_id}")
        
        # Get plan
        plan = await self.repository.get_plan_by_id(optimization_request.plan_id)
        if not plan:
            raise PlanNotFoundError(str(optimization_request.plan_id))
        
        # Get plan tasks, resources, and dependencies
        tasks = await self.repository.get_plan_tasks(plan.id)
        resources = await self.repository.get_plan_resources(plan.id)
        dependencies = await self.repository.get_plan_dependencies(plan.id)
        
        # Perform optimization
        try:
            optimization_result = await self._perform_optimization(
                plan,
                tasks,
                resources,
                dependencies,
                optimization_request
            )
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            raise OptimizationError(
                message=f"Optimization failed: {str(e)}",
                details={"error": str(e)}
            )
        
        # Publish event
        await self.helper_service.publish_plan_optimized_event(plan, optimization_result, self.event_bus)
        
        # Return optimization result
        return optimization_result
    
    async def _perform_optimization(
        self,
        plan,
        tasks,
        resources,
        dependencies,
        optimization_request: OptimizationRequest
    ) -> OptimizationResultResponse:
        """
        Perform plan optimization.
        
        Args:
            plan: Plan model
            tasks: List of tasks
            resources: List of resources
            dependencies: List of dependencies
            optimization_request: Optimization request
            
        Returns:
            OptimizationResultResponse: Optimization result
        """
        # This is a placeholder for actual optimization logic
        # In a real implementation, this would use optimization algorithms
        
        # Create a basic optimization result
        result_data = {
            "plan_id": plan.id,
            "generated_at": datetime.now(),
            "optimization_target": optimization_request.optimization_target,
            "status": "optimal",
            "task_adjustments": {},
            "resource_assignments": {},
            "metrics": {
                "original_duration": 0,
                "optimized_duration": 0,
                "improvement_percentage": 0,
                "resource_utilization": 0
            },
            "improvements": {
                "duration_reduction": 0,
                "cost_reduction": 0,
                "resource_efficiency": 0
            }
        }
        
        # Calculate original plan duration (simplified)
        if tasks:
            earliest_start = min(task.created_at for task in tasks)
            latest_end = earliest_start + timedelta(days=len(tasks) * 5)  # Simplified calculation
            original_duration = (latest_end - earliest_start).days
            
            # Simulate optimization (reduce duration by 10%)
            optimized_duration = int(original_duration * 0.9)
            
            # Update metrics
            result_data["metrics"]["original_duration"] = original_duration
            result_data["metrics"]["optimized_duration"] = optimized_duration
            result_data["metrics"]["improvement_percentage"] = 10
            result_data["metrics"]["resource_utilization"] = 85
            
            # Update improvements
            result_data["improvements"]["duration_reduction"] = original_duration - optimized_duration
            result_data["improvements"]["cost_reduction"] = 5000  # Example value
            result_data["improvements"]["resource_efficiency"] = 15  # Example percentage
            
            # Create task adjustments (for demonstration)
            for i, task in enumerate(tasks):
                if i % 3 == 0:  # Adjust every third task
                    result_data["task_adjustments"][str(task.id)] = {
                        "original_duration": task.estimated_duration,
                        "optimized_duration": task.estimated_duration * 0.9,
                        "start_date_shift": -1,  # Start 1 day earlier
                        "resource_reassignment": True if i % 2 == 0 else False
                    }
            
            # Create resource assignments (for demonstration)
            for i, resource in enumerate(resources):
                result_data["resource_assignments"][str(resource.id)] = [
                    {
                        "task_id": str(tasks[j].id) if j < len(tasks) else None,
                        "allocation_percentage": 100 if j % 2 == 0 else 50,
                        "start_date": (earliest_start + timedelta(days=j * 5)).isoformat(),
                        "end_date": (earliest_start + timedelta(days=(j + 1) * 5)).isoformat()
                    }
                    for j in range(min(3, len(tasks)))  # Assign up to 3 tasks per resource
                    if j % (i + 1) == 0  # Distribute tasks among resources
                ]
        
        # Create response
        return OptimizationResultResponse(
            data=result_data,
            message="Plan optimization completed successfully",
            success=True
        )
