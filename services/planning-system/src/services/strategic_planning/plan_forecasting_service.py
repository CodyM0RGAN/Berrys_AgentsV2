"""
Plan Forecasting Service for Strategic Planning.

This module provides methods for forecasting strategic plans.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from ..repository import PlanningRepository
from .helper_service import HelperService

from ...models.api import (
    ForecastRequest,
    TimelineForecastResponse,
    BottleneckAnalysisResponse,
    TimelinePoint
)
from ...exceptions import (
    PlanNotFoundError,
    ForecastingError
)

from shared.utils.src.messaging import EventBus

logger = logging.getLogger(__name__)

class PlanForecastingService:
    """
    Plan forecasting service.
    
    This service provides methods for forecasting strategic plans.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        helper_service: HelperService,
        event_bus: EventBus,
    ):
        """
        Initialize the plan forecasting service.
        
        Args:
            repository: Planning repository
            helper_service: Helper service
            event_bus: Event bus
        """
        self.repository = repository
        self.helper_service = helper_service
        self.event_bus = event_bus
        logger.info("Plan Forecasting Service initialized")
    
    async def forecast_timeline(
        self,
        forecast_request: ForecastRequest
    ) -> TimelineForecastResponse:
        """
        Generate a timeline forecast for a strategic plan.
        
        Args:
            forecast_request: Forecast request
            
        Returns:
            TimelineForecastResponse: Timeline forecast
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If forecasting fails
        """
        logger.info(f"Forecasting timeline for plan: {forecast_request.plan_id}")
        
        # Get plan
        plan = await self.repository.get_plan_by_id(forecast_request.plan_id)
        if not plan:
            raise PlanNotFoundError(str(forecast_request.plan_id))
        
        # Get plan tasks, resources, and dependencies
        tasks = await self.repository.get_plan_tasks(plan.id)
        resources = await self.repository.get_plan_resources(plan.id)
        dependencies = await self.repository.get_plan_dependencies(plan.id)
        
        # Generate forecast
        try:
            forecast = await self._generate_timeline_forecast(
                plan,
                tasks,
                resources,
                dependencies,
                forecast_request
            )
        except Exception as e:
            logger.error(f"Forecasting failed: {str(e)}")
            raise ForecastingError(
                message=f"Forecasting failed: {str(e)}",
                details={"error": str(e)}
            )
        
        # Publish event
        await self.helper_service.publish_timeline_forecasted_event(plan, forecast, self.event_bus)
        
        # Return forecast
        return forecast
    
    async def analyze_bottlenecks(
        self,
        plan_id: UUID
    ) -> BottleneckAnalysisResponse:
        """
        Analyze bottlenecks in a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            BottleneckAnalysisResponse: Bottleneck analysis
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If analysis fails
        """
        logger.info(f"Analyzing bottlenecks for plan: {plan_id}")
        
        # Get plan
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        
        # Get plan tasks, resources, and dependencies
        tasks = await self.repository.get_plan_tasks(plan.id)
        resources = await self.repository.get_plan_resources(plan.id)
        dependencies = await self.repository.get_plan_dependencies(plan.id)
        
        # Analyze bottlenecks
        try:
            analysis = await self._analyze_plan_bottlenecks(
                plan,
                tasks,
                resources,
                dependencies
            )
        except Exception as e:
            logger.error(f"Bottleneck analysis failed: {str(e)}")
            raise ForecastingError(
                message=f"Bottleneck analysis failed: {str(e)}",
                details={"error": str(e)}
            )
        
        # Publish event
        await self.helper_service.publish_bottlenecks_analyzed_event(plan, analysis, self.event_bus)
        
        # Return analysis
        return analysis
    
    async def _generate_timeline_forecast(
        self,
        plan,
        tasks,
        resources,
        dependencies,
        forecast_request: ForecastRequest
    ) -> TimelineForecastResponse:
        """
        Generate timeline forecast.
        
        Args:
            plan: Plan model
            tasks: List of tasks
            resources: List of resources
            dependencies: List of dependencies
            forecast_request: Forecast request
            
        Returns:
            TimelineForecastResponse: Timeline forecast
        """
        # This is a placeholder for actual forecasting logic
        # In a real implementation, this would use forecasting algorithms
        
        # Set confidence interval
        confidence_interval = forecast_request.confidence_interval or 0.8
        
        # Calculate basic timeline points
        timeline_points = []
        
        # Determine start and end dates
        if tasks:
            start_date = min((task.start_date for task in tasks if task.start_date is not None), 
                            default=datetime.now())
            
            # Calculate a simple end date based on task durations and dependencies
            total_duration = sum(task.estimated_duration for task in tasks)
            avg_parallelism = max(1, min(len(tasks) / 5, len(resources) if resources else 1))
            estimated_days = total_duration / (8 * avg_parallelism)  # Assuming 8 hours per day
            
            end_date = start_date + timedelta(days=estimated_days)
            
            # Generate timeline points (one per week)
            current_date = start_date
            while current_date <= end_date:
                # Calculate progress percentage based on date
                total_days = (end_date - start_date).days
                elapsed_days = (current_date - start_date).days
                progress = min(100, (elapsed_days / total_days * 100) if total_days > 0 else 0)
                
                # Add some randomness to simulate uncertainty
                import random
                uncertainty = random.uniform(-5, 5) * (1 - confidence_interval)
                
                timeline_points.append(TimelinePoint(
                    date=current_date,
                    value=progress,
                    lower_bound=max(0, progress - uncertainty * 2),
                    upper_bound=min(100, progress + uncertainty * 2)
                ))
                
                # Move to next week
                current_date += timedelta(weeks=1)
            
            # Calculate expected completion and bounds
            expected_completion = end_date
            best_case_completion = end_date - timedelta(days=total_duration * 0.1 / 8)  # 10% faster
            worst_case_completion = end_date + timedelta(days=total_duration * 0.2 / 8)  # 20% slower
        else:
            # Default values if no tasks
            start_date = datetime.now()
            end_date = start_date + timedelta(weeks=12)
            expected_completion = end_date
            best_case_completion = end_date - timedelta(weeks=2)
            worst_case_completion = end_date + timedelta(weeks=4)
            
            # Generate some default timeline points
            for i in range(12):
                current_date = start_date + timedelta(weeks=i)
                progress = min(100, i * 8.33)  # Approximately 8.33% per week for 12 weeks
                
                timeline_points.append(TimelinePoint(
                    date=current_date,
                    value=progress,
                    lower_bound=max(0, progress - 5),
                    upper_bound=min(100, progress + 5)
                ))
        
        # Create forecast data
        forecast_data = {
            "plan_id": plan.id,
            "generated_at": datetime.now(),
            "confidence_interval": confidence_interval,
            "timeline": timeline_points,
            "expected_completion": expected_completion,
            "best_case_completion": best_case_completion,
            "worst_case_completion": worst_case_completion
        }
        
        # Create response
        return TimelineForecastResponse(
            data=forecast_data,
            message="Timeline forecast generated successfully",
            success=True
        )
    
    async def _analyze_plan_bottlenecks(
        self,
        plan,
        tasks,
        resources,
        dependencies
    ) -> BottleneckAnalysisResponse:
        """
        Analyze plan bottlenecks.
        
        Args:
            plan: Plan model
            tasks: List of tasks
            resources: List of resources
            dependencies: List of dependencies
            
        Returns:
            BottleneckAnalysisResponse: Bottleneck analysis
        """
        # This is a placeholder for actual bottleneck analysis logic
        # In a real implementation, this would use more sophisticated algorithms
        
        bottlenecks = []
        recommendations = []
        
        # Identify potential bottlenecks
        
        # 1. Check for overallocated resources
        resource_allocations = {}
        for resource in resources:
            resource_allocations[resource.id] = []
        
        for task in tasks:
            if task.assigned_to and task.assigned_to in resource_allocations:
                resource_allocations[task.assigned_to].append(task)
        
        for resource_id, allocated_tasks in resource_allocations.items():
            if len(allocated_tasks) > 3:  # Simple threshold for demonstration
                resource = next((r for r in resources if r.id == resource_id), None)
                if resource:
                    bottlenecks.append({
                        "type": "resource_overallocation",
                        "resource_id": str(resource_id),
                        "resource_name": resource.name,
                        "severity": "high",
                        "description": f"Resource {resource.name} is assigned to {len(allocated_tasks)} tasks",
                        "affected_tasks": [str(task.id) for task in allocated_tasks]
                    })
                    
                    recommendations.append({
                        "type": "resource_reallocation",
                        "description": f"Redistribute tasks from overallocated resource {resource.name}",
                        "details": {
                            "resource_id": str(resource_id),
                            "tasks_to_reassign": [str(task.id) for task in allocated_tasks[3:]]
                        }
                    })
        
        # 2. Check for critical path tasks with high duration
        critical_path_tasks = [task for task in tasks if getattr(task, 'is_critical_path', False)]
        for task in critical_path_tasks:
            if task.estimated_duration > 80:  # More than 2 weeks (80 hours)
                bottlenecks.append({
                    "type": "long_critical_task",
                    "task_id": str(task.id),
                    "task_name": task.name,
                    "severity": "medium",
                    "description": f"Critical path task {task.name} has a long duration ({task.estimated_duration} hours)",
                    "affected_tasks": [str(task.id)]
                })
                
                recommendations.append({
                    "type": "task_splitting",
                    "description": f"Split long critical path task {task.name} into smaller subtasks",
                    "details": {
                        "task_id": str(task.id),
                        "suggested_splits": 2
                    }
                })
        
        # 3. Check for tasks with many dependencies
        dependency_counts = {}
        for dependency in dependencies:
            to_task_id = dependency.to_task_id
            dependency_counts[to_task_id] = dependency_counts.get(to_task_id, 0) + 1
        
        for task_id, count in dependency_counts.items():
            if count > 3:  # Simple threshold for demonstration
                task = next((t for t in tasks if t.id == task_id), None)
                if task:
                    bottlenecks.append({
                        "type": "dependency_bottleneck",
                        "task_id": str(task_id),
                        "task_name": task.name,
                        "severity": "medium",
                        "description": f"Task {task.name} has {count} dependencies",
                        "affected_tasks": [str(task_id)]
                    })
                    
                    recommendations.append({
                        "type": "dependency_reduction",
                        "description": f"Reduce dependencies for task {task.name}",
                        "details": {
                            "task_id": str(task_id),
                            "current_dependencies": count
                        }
                    })
        
        # Create impact analysis
        impact_analysis = {
            "timeline_impact": {
                "delay_risk": "medium" if bottlenecks else "low",
                "estimated_delay": len(bottlenecks) * 3,  # Simple calculation: 3 days per bottleneck
                "affected_milestones": []
            },
            "resource_impact": {
                "overallocation_percentage": len([b for b in bottlenecks if b["type"] == "resource_overallocation"]) * 20,
                "affected_resources": [b["resource_id"] for b in bottlenecks if b["type"] == "resource_overallocation"]
            },
            "cost_impact": {
                "estimated_cost_increase": len(bottlenecks) * 5000,  # Simple calculation: $5000 per bottleneck
                "budget_risk": "high" if len(bottlenecks) > 3 else "medium" if bottlenecks else "low"
            }
        }
        
        # Create analysis data
        analysis_data = {
            "plan_id": plan.id,
            "generated_at": datetime.now(),
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "impact_analysis": impact_analysis
        }
        
        # Create response
        return BottleneckAnalysisResponse(
            data=analysis_data,
            message="Bottleneck analysis completed successfully",
            success=True
        )
