"""
Project Forecaster component for the Planning System service.

This module implements the forecasting component, which handles
timeline forecasts, bottleneck analysis, and project predictions.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from uuid import UUID
from datetime import datetime, timedelta

from shared.utils.src.messaging import EventBus

from ..models.api import (
    TimelinePoint,
    TimelineForecast,
    BottleneckAnalysis,
    PaginatedResponse
)
from ..exceptions import (
    PlanNotFoundError,
    ForecastingError
)
from .repository import PlanningRepository
from .dependency_manager import DependencyManager
from .base import BasePlannerComponent
from ..config import PlanningSystemConfig as Settings

class ProjectForecaster(BasePlannerComponent):
    """
    Project forecasting component.
    
    This component handles timeline forecasts, bottleneck analysis,
    and project predictions for the planning system.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
        dependency_manager: DependencyManager,
    ):
        """
        Initialize the project forecaster.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
            dependency_manager: Dependency manager component
        """
        super().__init__(repository, event_bus, "ProjectForecaster")
        self.dependency_manager = dependency_manager
    
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
        await self._log_operation("Creating", "forecast", entity_id=plan_id)
        
        # Set default confidence interval if not provided
        confidence_interval = confidence_interval or 0.95  # 95% confidence interval
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        try:
            # Get plan data
            tasks = await self.repository.get_tasks_by_plan(plan_id)
            dependencies = await self.repository.get_all_dependencies_for_plan(plan_id)
            
            # Generate timeline
            timeline_points = await self._generate_timeline(
                plan=plan,
                tasks=tasks,
                dependencies=dependencies,
                confidence_interval=confidence_interval,
                time_unit=time_unit
            )
            
            # Calculate completion dates
            completion_dates = await self._calculate_completion_dates(
                timeline_points=timeline_points,
                confidence_interval=confidence_interval
            )
            
            # Create forecast record
            forecast_data = {
                "plan_id": plan_id,
                "generated_at": datetime.utcnow(),
                "confidence_interval": confidence_interval,
                "timeline": [point.model_dump() for point in timeline_points],
                "expected_completion": completion_dates["expected"],
                "best_case_completion": completion_dates["best_case"],
                "worst_case_completion": completion_dates["worst_case"]
            }
            
            # Store forecast
            forecast = await self.repository.create_forecast(forecast_data)
            
            # Publish event
            await self._publish_event(
                "plan.forecast.created", 
                forecast,
                {"plan_id": str(plan_id)}
            )
            
            # Convert to response model
            forecast_response = TimelineForecast(
                plan_id=plan_id,
                generated_at=forecast.generated_at,
                confidence_interval=confidence_interval,
                timeline=timeline_points,
                expected_completion=forecast.expected_completion,
                best_case_completion=forecast.best_case_completion,
                worst_case_completion=forecast.worst_case_completion
            )
            
            return forecast_response
        except Exception as e:
            self.logger.error(f"Forecasting error: {str(e)}")
            raise ForecastingError(
                message=f"Failed to create forecast: {str(e)}",
                details={"plan_id": str(plan_id)}
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
        await self._log_operation("Getting", "latest forecast", entity_id=plan_id)
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get latest forecast
        forecast = await self.repository.get_latest_forecast(plan_id)
        
        if not forecast:
            raise ForecastingError(
                message="No forecast exists for this plan",
                details={"plan_id": str(plan_id)}
            )
        
        # Convert stored timeline to TimelinePoint objects
        timeline_points = []
        for point_data in forecast.timeline:
            timeline_points.append(TimelinePoint(
                date=point_data["date"],
                value=point_data["value"],
                lower_bound=point_data.get("lower_bound"),
                upper_bound=point_data.get("upper_bound")
            ))
        
        # Convert to response model
        forecast_response = TimelineForecast(
            plan_id=plan_id,
            generated_at=forecast.generated_at,
            confidence_interval=forecast.confidence_interval,
            timeline=timeline_points,
            expected_completion=forecast.expected_completion,
            best_case_completion=forecast.best_case_completion,
            worst_case_completion=forecast.worst_case_completion
        )
        
        return forecast_response
    
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
        await self._log_operation("Identifying", "bottlenecks", entity_id=plan_id)
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        try:
            # Get plan data
            tasks = await self.repository.get_tasks_by_plan(plan_id)
            dependencies = await self.repository.get_all_dependencies_for_plan(plan_id)
            resources = await self.repository.get_resources_for_plan(plan_id)
            allocations = await self.repository.get_resource_allocations_for_plan(plan_id)
            
            # Identify resource bottlenecks
            resource_bottlenecks = await self._identify_resource_bottlenecks(
                tasks=tasks,
                resources=resources,
                allocations=allocations
            )
            
            # Identify dependency bottlenecks
            dependency_bottlenecks = await self._identify_dependency_bottlenecks(
                tasks=tasks,
                dependencies=dependencies
            )
            
            # Identify skill bottlenecks
            skill_bottlenecks = await self._identify_skill_bottlenecks(
                tasks=tasks,
                resources=resources
            )
            
            # Combine bottlenecks
            all_bottlenecks = resource_bottlenecks + dependency_bottlenecks + skill_bottlenecks
            
            # Sort bottlenecks by severity
            all_bottlenecks.sort(key=lambda x: x.get("severity", 0), reverse=True)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(all_bottlenecks)
            
            # Analyze impact
            impact_analysis = await self._analyze_bottleneck_impact(
                bottlenecks=all_bottlenecks,
                tasks=tasks,
                plan=plan
            )
            
            # Create bottleneck analysis record
            bottleneck_data = {
                "plan_id": plan_id,
                "generated_at": datetime.utcnow(),
                "bottlenecks": all_bottlenecks,
                "recommendations": recommendations,
                "impact_analysis": impact_analysis
            }
            
            # Store analysis
            analysis = await self.repository.create_bottleneck_analysis(bottleneck_data)
            
            # Publish event
            await self._publish_event(
                "plan.bottlenecks.identified", 
                analysis,
                {"plan_id": str(plan_id)}
            )
            
            # Convert to response model
            analysis_response = BottleneckAnalysis(
                plan_id=plan_id,
                generated_at=analysis.generated_at,
                bottlenecks=analysis.bottlenecks,
                recommendations=analysis.recommendations,
                impact_analysis=analysis.impact_analysis
            )
            
            return analysis_response
        except Exception as e:
            self.logger.error(f"Bottleneck analysis error: {str(e)}")
            raise ForecastingError(
                message=f"Failed to identify bottlenecks: {str(e)}",
                details={"plan_id": str(plan_id)}
            )
    
    async def compare_forecasts(
        self,
        plan_id: UUID,
        forecast_id_1: UUID,
        forecast_id_2: UUID
    ) -> Dict[str, Any]:
        """
        Compare two forecasts for the same plan.
        
        Args:
            plan_id: Plan ID
            forecast_id_1: First forecast ID
            forecast_id_2: Second forecast ID
            
        Returns:
            Dict[str, Any]: Comparison results
            
        Raises:
            PlanNotFoundError: If plan not found
            ForecastingError: If forecast not found
        """
        await self._log_operation(
            "Comparing", 
            "forecasts", 
            entity_id=plan_id,
            entity_name=f"between {forecast_id_1} and {forecast_id_2}"
        )
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get forecasts
        forecast1 = await self.repository.get_forecast_by_id(forecast_id_1)
        if not forecast1 or forecast1.plan_id != plan_id:
            raise ForecastingError(
                message="Forecast 1 not found or not associated with this plan",
                details={
                    "plan_id": str(plan_id),
                    "forecast_id": str(forecast_id_1)
                }
            )
        
        forecast2 = await self.repository.get_forecast_by_id(forecast_id_2)
        if not forecast2 or forecast2.plan_id != plan_id:
            raise ForecastingError(
                message="Forecast 2 not found or not associated with this plan",
                details={
                    "plan_id": str(plan_id),
                    "forecast_id": str(forecast_id_2)
                }
            )
        
        # Compare dates
        completion_diff = (forecast2.expected_completion - forecast1.expected_completion).days
        best_case_diff = (forecast2.best_case_completion - forecast1.best_case_completion).days
        worst_case_diff = (forecast2.worst_case_completion - forecast1.worst_case_completion).days
        
        # Calculate trends
        if completion_diff > 0:
            trend = "delay"
        elif completion_diff < 0:
            trend = "acceleration"
        else:
            trend = "stable"
        
        # Create comparison result
        comparison = {
            "plan_id": str(plan_id),
            "forecast1": {
                "id": str(forecast1.id),
                "generated_at": forecast1.generated_at.isoformat(),
                "expected_completion": forecast1.expected_completion.isoformat(),
                "best_case_completion": forecast1.best_case_completion.isoformat(),
                "worst_case_completion": forecast1.worst_case_completion.isoformat()
            },
            "forecast2": {
                "id": str(forecast2.id),
                "generated_at": forecast2.generated_at.isoformat(),
                "expected_completion": forecast2.expected_completion.isoformat(),
                "best_case_completion": forecast2.best_case_completion.isoformat(),
                "worst_case_completion": forecast2.worst_case_completion.isoformat()
            },
            "comparison": {
                "expected_completion_difference_days": completion_diff,
                "best_case_difference_days": best_case_diff,
                "worst_case_difference_days": worst_case_diff,
                "trend": trend,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        return comparison
    
    async def get_milestone_forecasts(
        self,
        plan_id: UUID,
        milestone_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Get forecasts for plan milestones.
        
        Args:
            plan_id: Plan ID
            milestone_ids: Optional list of milestone IDs to filter
            
        Returns:
            Dict[str, Any]: Milestone forecasts
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        await self._log_operation("Getting", "milestone forecasts", entity_id=plan_id)
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get milestones
        milestones = await self.repository.get_milestones_by_plan(plan_id)
        
        if milestone_ids:
            milestones = [m for m in milestones if m.id in milestone_ids]
        
        if not milestones:
            return {
                "plan_id": str(plan_id),
                "generated_at": datetime.utcnow().isoformat(),
                "milestones": []
            }
        
        # Get tasks and dependencies
        tasks = await self.repository.get_tasks_by_plan(plan_id)
        dependencies = await self.repository.get_all_dependencies_for_plan(plan_id)
        
        # Generate forecasts for each milestone
        milestone_forecasts = []
        for milestone in milestones:
            # Get tasks associated with this milestone
            milestone_tasks = [t for t in tasks if t.milestone_id == milestone.id]
            
            # Calculate expected completion date using Monte Carlo simulation
            completion_date, confidence = await self._forecast_milestone_completion(
                milestone=milestone,
                tasks=milestone_tasks,
                dependencies=dependencies
            )
            
            # Create forecast data
            milestone_forecasts.append({
                "id": str(milestone.id),
                "name": milestone.name,
                "target_date": milestone.target_date.isoformat(),
                "forecast_date": completion_date.isoformat(),
                "confidence": confidence,
                "variance": abs((completion_date - milestone.target_date).days),
                "on_track": completion_date <= milestone.target_date
            })
        
        return {
            "plan_id": str(plan_id),
            "generated_at": datetime.utcnow().isoformat(),
            "milestones": milestone_forecasts
        }
    
    # Helper methods
    
    async def _generate_timeline(
        self,
        plan: Any,
        tasks: List[Any],
        dependencies: List[Any],
        confidence_interval: float,
        time_unit: str
    ) -> List[TimelinePoint]:
        """
        Generate timeline forecast points.
        
        Args:
            plan: Plan data
            tasks: Task data
            dependencies: Dependency data
            confidence_interval: Confidence interval (0.0-1.0)
            time_unit: Time unit (hour, day, week, month)
            
        Returns:
            List[TimelinePoint]: Timeline forecast points
        """
        # In a real implementation, this would use Monte Carlo simulation
        # or other forecasting techniques to generate timeline points
        # For this example, we'll create simplified data
        
        # Define time unit in days
        unit_days = {
            "hour": 1/24,
            "day": 1,
            "week": 7,
            "month": 30
        }.get(time_unit, 1)
        
        # Get critical path
        critical_path = await self.dependency_manager.get_critical_path(plan.id)
        
        # Calculate total duration based on critical path
        total_duration_days = sum(task.estimated_duration / 8 for task in critical_path)  # 8 hours per day
        
        # Create timeline points
        start_date = datetime.utcnow()
        points = []
        
        # Calculate number of points based on timeline and time unit
        num_points = int(total_duration_days / unit_days) + 1
        num_points = min(max(num_points, 10), 100)  # At least 10, at most 100 points
        
        # Calculate standard deviation for confidence bounds (simplified)
        # In a real implementation, this would be calculated from historical data
        std_dev = total_duration_days * 0.2  # 20% of total duration
        
        # Z-score for the confidence interval
        z = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }.get(confidence_interval, 1.96)
        
        # Generate points
        for i in range(num_points):
            point_date = start_date + timedelta(days=i * unit_days)
            
            # S-curve for progress (simplified)
            x = i / (num_points - 1) if num_points > 1 else 0
            # S-curve formula: y = 1 / (1 + e^(-10 * (x - 0.5)))
            progress = 1 / (1 + 2.71828 ** (-10 * (x - 0.5)))
            progress = min(max(progress, 0), 1) * 100  # 0-100%
            
            # Calculate confidence bounds
            time_factor = (i / (num_points - 1)) if num_points > 1 else 0
            current_std_dev = std_dev * time_factor  # Uncertainty increases over time
            lower_bound = max(progress - z * current_std_dev, 0)
            upper_bound = min(progress + z * current_std_dev, 100)
            
            points.append(TimelinePoint(
                date=point_date,
                value=progress,
                lower_bound=lower_bound,
                upper_bound=upper_bound
            ))
        
        return points
    
    async def _calculate_completion_dates(
        self,
        timeline_points: List[TimelinePoint],
        confidence_interval: float
    ) -> Dict[str, datetime]:
        """
        Calculate expected completion dates from timeline.
        
        Args:
            timeline_points: Timeline points
            confidence_interval: Confidence interval
            
        Returns:
            Dict[str, datetime]: Completion dates
        """
        # In a real implementation, this would calculate completion dates
        # based on the timeline points and confidence interval
        # For this example, we'll use the last point as the expected completion
        
        if not timeline_points:
            return {
                "expected": datetime.utcnow() + timedelta(days=30),
                "best_case": datetime.utcnow() + timedelta(days=25),
                "worst_case": datetime.utcnow() + timedelta(days=40)
            }
        
        # Last point is expected completion
        expected_completion = timeline_points[-1].date
        
        # Best case completion (using confidence bound)
        if timeline_points[-1].lower_bound is not None:
            # Find the point where lower bound reaches 100%
            for i, point in enumerate(timeline_points):
                if point.lower_bound and point.lower_bound >= 100:
                    best_case = point.date
                    break
            else:
                # If no point reaches 100%, use expected minus some margin
                best_case = expected_completion - timedelta(days=5)
        else:
            best_case = expected_completion - timedelta(days=5)
        
        # Worst case completion (using confidence bound)
        if timeline_points[-1].upper_bound is not None:
            # Estimate when upper bound would reach 100%
            last_point = timeline_points[-1]
            if last_point.upper_bound < 100:
                # Calculate how many more days needed to reach 100%
                days_per_percent = 1  # Simplified estimate
                remaining_percent = 100 - last_point.upper_bound
                additional_days = remaining_percent * days_per_percent
                worst_case = last_point.date + timedelta(days=additional_days)
            else:
                # Find the earliest point where upper bound reaches 100%
                for point in timeline_points:
                    if point.upper_bound and point.upper_bound >= 100:
                        worst_case = point.date
                        break
                else:
                    worst_case = expected_completion + timedelta(days=10)
        else:
            worst_case = expected_completion + timedelta(days=10)
        
        return {
            "expected": expected_completion,
            "best_case": best_case,
            "worst_case": worst_case
        }
    
    async def _identify_resource_bottlenecks(
        self,
        tasks: List[Any],
        resources: List[Any],
        allocations: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify resource-related bottlenecks.
        
        Args:
            tasks: Task data
            resources: Resource data
            allocations: Resource allocation data
            
        Returns:
            List[Dict[str, Any]]: Resource bottlenecks
        """
        bottlenecks = []
        
        # Check for overallocated resources
        resource_utilization = {}
        for resource in resources:
            resource_utilization[resource.id] = {
                "resource": resource,
                "total_hours": 0,
                "capacity": getattr(resource, "capacity_hours", 40),  # Default 40 hours per week
                "allocations": []
            }
        
        for allocation in allocations:
            if allocation.resource_id in resource_utilization:
                resource_utilization[allocation.resource_id]["total_hours"] += allocation.assigned_hours
                resource_utilization[allocation.resource_id]["allocations"].append(allocation)
        
        # Find overallocated resources
        for resource_id, data in resource_utilization.items():
            utilization_percent = (data["total_hours"] / data["capacity"]) * 100 if data["capacity"] > 0 else 0
            
            if utilization_percent > 100:
                resource = data["resource"]
                
                # Get tasks for this resource
                resource_tasks = []
                for allocation in data["allocations"]:
                    task = next((t for t in tasks if t.id == allocation.task_id), None)
                    if task:
                        resource_tasks.append({
                            "id": str(task.id),
                            "name": task.name,
                            "hours": allocation.assigned_hours
                        })
                
                # Sort tasks by assigned hours (descending)
                resource_tasks.sort(key=lambda x: x["hours"], reverse=True)
                
                bottlenecks.append({
                    "type": "resource_overallocation",
                    "severity": min((utilization_percent - 100) / 100, 1) * 10,  # 0-10 scale
                    "resource_id": str(resource_id),
                    "resource_name": getattr(resource, "name", f"Resource {resource_id}"),
                    "capacity_hours": data["capacity"],
                    "allocated_hours": data["total_hours"],
                    "utilization_percent": utilization_percent,
                    "tasks": resource_tasks[:5]  # Top 5 tasks
                })
        
        # Check for critical resource dependencies
        critical_resources = []
        for resource in resources:
            # Count tasks on critical path assigned to this resource
            critical_tasks = 0
            for allocation in allocations:
                if allocation.resource_id == resource.id:
                    task = next((t for t in tasks if t.id == allocation.task_id), None)
                    if task and getattr(task, "is_critical_path", False):
                        critical_tasks += 1
            
            if critical_tasks > 3:  # If responsible for multiple critical path tasks
                critical_resources.append({
                    "resource_id": str(resource.id),
                    "resource_name": getattr(resource, "name", f"Resource {resource.id}"),
                    "critical_task_count": critical_tasks
                })
        
        # Add critical resource bottlenecks
        for resource_data in critical_resources:
            bottlenecks.append({
                "type": "critical_resource_dependency",
                "severity": min(resource_data["critical_task_count"] / 5, 1) * 8,  # 0-8 scale
                "resource_id": resource_data["resource_id"],
                "resource_name": resource_data["resource_name"],
                "critical_task_count": resource_data["critical_task_count"],
                "risk": "High dependency on a single resource for critical path"
            })
        
        return bottlenecks
    
    async def _identify_dependency_bottlenecks(
        self,
        tasks: List[Any],
        dependencies: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify dependency-related bottlenecks.
        
        Args:
            tasks: Task data
            dependencies: Dependency data
            
        Returns:
            List[Dict[str, Any]]: Dependency bottlenecks
        """
        bottlenecks = []
        
        # Count dependencies per task
        task_dependencies = {}
        for task in tasks:
            task_dependencies[task.id] = {
                "task": task,
                "incoming": 0,
                "outgoing": 0,
                "predecessors": [],
                "successors": []
            }
        
        for dependency in dependencies:
            # Increment incoming count for to_task
            if dependency.to_task_id in task_dependencies:
                task_dependencies[dependency.to_task_id]["incoming"] += 1
                task_dependencies[dependency.to_task_id]["predecessors"].append(dependency.from_task_id)
            
            # Increment outgoing count for from_task
            if dependency.from_task_id in task_dependencies:
                task_dependencies[dependency.from_task_id]["outgoing"] += 1
                task_dependencies[dependency.from_task_id]["successors"].append(dependency.to_task_id)
        
        # Check for dependency bottlenecks
        for task_id, data in task_dependencies.items():
            task = data["task"]
            
            # High incoming dependencies
            if data["incoming"] > 3:
                # Get predecessor tasks
                predecessor_tasks = []
                for pred_id in data["predecessors"]:
                    pred_task = next((t for t in tasks if t.id == pred_id), None)
                    if pred_task:
                        predecessor_tasks.append({
                            "id": str(pred_task.id),
                            "name": pred_task.name
                        })
                
                bottlenecks.append({
                    "type": "high_incoming_dependencies",
                    "severity": min(data["incoming"] / 5, 1) * 7,  # 0-7 scale
                    "task_id": str(task_id),
                    "task_name": task.name,
                    "dependency_count": data["incoming"],
                    "predecessors": predecessor_tasks,
                    "risk": "Task depends on many predecessors, increasing risk of delays"
                })
            
            # High outgoing dependencies
            if data["outgoing"] > 3:
                # Get successor tasks
                successor_tasks = []
                for succ_id in data["successors"]:
                    succ_task = next((t for t in tasks if t.id == succ_id), None)
                    if succ_task:
                        successor_tasks.append({
                            "id": str(succ_task.id),
                            "name": succ_task.name
                        })
                
                bottlenecks.append({
                    "type": "high_outgoing_dependencies",
                    "severity": min(data["outgoing"] / 5, 1) * 8,  # 0-8 scale
                    "task_id": str(task_id),
                    "task_name": task.name,
                    "dependency_count": data["outgoing"],
                    "successors": successor_tasks,
                    "risk": "Many tasks depend on this one, making it a critical bottleneck"
                })
        
        # Look for long dependency chains
        chains = await self._find_dependency_chains(task_dependencies)
        
        for chain in chains:
            if len(chain) > 4:  # Arbitrarily consider chains of 5+ tasks as bottlenecks
                chain_tasks = []
                for task_id in chain:
                    task = next((t for t in tasks if t.id == task_id), None)
                    if task:
                        chain_tasks.append({
                            "id": str(task.id),
                            "name": task.name
                        })
                
                bottlenecks.append({
                    "type": "long_dependency_chain",
                    "severity": min((len(chain) - 3) / 5, 1) * 9,  # 0-9 scale
                    "chain_length": len(chain),
                    "tasks": chain_tasks,
                    "risk": "Long sequential dependency chain limits parallelization"
                })
        
        return bottlenecks
    
    async def _identify_skill_bottlenecks(
        self,
        tasks: List[Any],
        resources: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify skill-related bottlenecks.
        
        Args:
            tasks: Task data
            resources: Resource data
            
        Returns:
            List[Dict[str, Any]]: Skill bottlenecks
        """
        bottlenecks = []
        
        # Collect required skills across all tasks
        required_skills = {}
        for task in tasks:
            if not hasattr(task, "required_skills") or not task.required_skills:
                continue
            
            for skill, level in task.required_skills.items():
                if skill not in required_skills:
                    required_skills[skill] = {
                        "name": skill,
                        "tasks": [],
                        "resources": [],
                        "max_level_required": 0
                    }
                
                # Add task to skill
                required_skills[skill]["tasks"].append({
                    "id": str(task.id),
                    "name": task.name,
                    "level": level
                })
                
                # Update max level
                required_skills[skill]["max_level_required"] = max(
                    required_skills[skill]["max_level_required"],
                    level
                )
        
        # Check resource skills against requirements
        for skill, skill_data in required_skills.items():
            # Find resources with this skill
            skilled_resources = []
            for resource in resources:
                # Check if resource has skills attribute
                if not hasattr(resource, "skills") or not resource.skills:
                    continue
                
                if skill in resource.skills:
                    skilled_resources.append({
                        "id": str(resource.id),
                        "name": getattr(resource, "name", f"Resource {resource.id}"),
                        "level": resource.skills[skill]
                    })
            
            # Add to skill data
            skill_data["resources"] = skilled_resources
            
            # Check if we have enough skilled resources
            if len(skilled_resources) == 0:
                # No resources with this skill
                bottlenecks.append({
                    "type": "missing_skill",
                    "severity": 10,  # Critical - no resources
                    "skill": skill,
                    "tasks_count": len(skill_data["tasks"]),
                    "resources_count": 0,
                    "tasks": skill_data["tasks"],
                    "risk": f"No resources with required skill: {skill}"
                })
            elif len(skilled_resources) < 2:
                # Single resource with this skill
                bottlenecks.append({
                    "type": "limited_skill",
                    "severity": 7,  # High - single resource
                    "skill": skill,
                    "tasks_count": len(skill_data["tasks"]),
                    "resources_count": len(skilled_resources),
                    "tasks": skill_data["tasks"],
                    "resources": skilled_resources,
                    "risk": f"Only one resource with required skill: {skill}"
                })
            
            # Check if any resources have sufficient skill level
            max_resource_level = max(r["level"] for r in skilled_resources) if skilled_resources else 0
            if max_resource_level < skill_data["max_level_required"]:
                bottlenecks.append({
                    "type": "insufficient_skill_level",
                    "severity": 8,  # High - skill gap
                    "skill": skill,
                    "required_level": skill_data["max_level_required"],
                    "available_level": max_resource_level,
                    "tasks": [t for t in skill_data["tasks"] if t["level"] > max_resource_level],
                    "resources": skilled_resources,
                    "risk": f"No resources with sufficient {skill} skill level"
                })
        
        return bottlenecks
    
    async def _find_dependency_chains(
        self,
        task_dependencies: Dict[Any, Dict[str, Any]]
    ) -> List[List[Any]]:
        """
        Find dependency chains in the task network.
        
        Args:
            task_dependencies: Dictionary of task dependencies
            
        Returns:
            List[List[Any]]: List of dependency chains
        """
        chains = []
        
        # Find start nodes (no predecessors)
        start_nodes = [
            task_id for task_id, data in task_dependencies.items()
            if not data["predecessors"]
        ]
        
        # Find all paths from start nodes
        for start_node in start_nodes:
            # DFS to find all paths
            self._find_paths(
                task_id=start_node,
                task_dependencies=task_dependencies,
                current_path=[],
                all_paths=chains,
                visited=set()
            )
        
        # Sort chains by length (descending)
        chains.sort(key=len, reverse=True)
        
        return chains
    
    def _find_paths(
        self,
        task_id: Any,
        task_dependencies: Dict[Any, Dict[str, Any]],
        current_path: List[Any],
        all_paths: List[List[Any]],
        visited: Set[Any]
    ) -> None:
        """
        Recursive helper to find all paths in the dependency graph.
        
        Args:
            task_id: Current task ID
            task_dependencies: Dictionary of task dependencies
            current_path: Current path being explored
            all_paths: List to collect all paths
            visited: Set of visited nodes in current path
        """
        # Skip if node already visited (avoid cycles)
        if task_id in visited:
            return
        
        # Add node to path and visited set
        current_path.append(task_id)
        visited.add(task_id)
        
        # Get successors
        successors = task_dependencies[task_id]["successors"]
        
        if not successors:
            # End of path, save if path length > 1
            if len(current_path) > 1:
                all_paths.append(current_path.copy())
        else:
            # Continue DFS with each successor
            for succ_id in successors:
                self._find_paths(
                    task_id=succ_id,
                    task_dependencies=task_dependencies,
                    current_path=current_path,
                    all_paths=all_paths,
                    visited=visited.copy()
                )
        
        # Backtrack: remove node from path
        current_path.pop()
        visited.remove(task_id)
    
    async def _forecast_milestone_completion(
        self,
        milestone: Any,
        tasks: List[Any],
        dependencies: List[Any]
    ) -> Tuple[datetime, float]:
        """
        Forecast milestone completion date.
        
        Args:
            milestone: Milestone data
            tasks: Tasks associated with milestone
            dependencies: All dependencies
            
        Returns:
            Tuple[datetime, float]: Forecast completion date and confidence
        """
        # In a real implementation, this would use Monte Carlo simulation
        # For this example, we'll use a simplified approach
        
        if not tasks:
            return milestone.target_date, 1.0
        
        # Get expected duration for each task
        task_durations = [task.estimated_duration for task in tasks]
        
        # Simple approach: assume all tasks are sequential
        total_hours = sum(task_durations)
        total_days = total_hours / 8  # Assuming 8 hours per day
        
        # Apply a random factor to simulate uncertainty
        import random
        random.seed(42)  # For reproducibility
        uncertainty_factor = random.uniform(0.8, 1.2)
        
        # Calculate completion date
        start_date = datetime.utcnow()
        completion_date = start_date + timedelta(days=total_days * uncertainty_factor)
        
        # Calculate confidence based on how close to target date
        days_difference = abs((completion_date - milestone.target_date).days)
        if completion_date <= milestone.target_date:
            # On or ahead of schedule
            confidence = max(0.5, 1.0 - (days_difference / 30) * 0.5)  # Min 50%
        else:
            # Behind schedule
            confidence = max(0.1, 0.9 - (days_difference / 20) * 0.4)  # Min 10%
        
        return completion_date, confidence
    
    async def _generate_recommendations(
        self,
        bottlenecks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations to address bottlenecks.
        
        Args:
            bottlenecks: List of identified bottlenecks
            
        Returns:
            List[Dict[str, Any]]: List of recommendations
        """
        recommendations = []
        
        # Process each bottleneck
        for bottleneck in bottlenecks:
            bottleneck_type = bottleneck.get("type", "")
            
            if bottleneck_type == "resource_overallocation":
                # Recommend resource allocation changes
                recommendations.append({
                    "type": "resource_reallocation",
                    "priority": "high" if bottleneck.get("severity", 0) > 7 else "medium",
                    "bottleneck_id": id(bottleneck),  # Use object id as identifier
                    "description": f"Reduce allocation for {bottleneck.get('resource_name', 'resource')}",
                    "action_items": [
                        "Reduce allocation percentage or assigned hours",
                        "Redistribute tasks to other resources",
                        "Extend timeline for non-critical tasks"
                    ],
                    "affected_resources": [bottleneck.get("resource_id")]
                })
            
            elif bottleneck_type == "critical_resource_dependency":
                # Recommend reducing dependency on critical resources
                recommendations.append({
                    "type": "resource_risk_mitigation",
                    "priority": "high",
                    "bottleneck_id": id(bottleneck),
                    "description": f"Reduce dependency on {bottleneck.get('resource_name', 'resource')}",
                    "action_items": [
                        "Cross-train other resources to handle critical tasks",
                        "Split critical tasks across multiple resources",
                        "Create backups for critical resources"
                    ],
                    "affected_resources": [bottleneck.get("resource_id")]
                })
            
            elif bottleneck_type in ["high_incoming_dependencies", "high_outgoing_dependencies"]:
                # Recommend dependency structure changes
                task_id = bottleneck.get("task_id")
                task_name = bottleneck.get("task_name", "task")
                
                recommendations.append({
                    "type": "dependency_restructuring",
                    "priority": "medium",
                    "bottleneck_id": id(bottleneck),
                    "description": f"Restructure dependencies for {task_name}",
                    "action_items": [
                        f"Break {task_name} into smaller, more manageable tasks",
                        "Identify and remove unnecessary dependencies",
                        "Parallelize tasks where possible"
                    ],
                    "affected_tasks": [task_id]
                })
            
            elif bottleneck_type == "long_dependency_chain":
                # Recommend breaking up the dependency chain
                recommendations.append({
                    "type": "parallelize_work",
                    "priority": "medium",
                    "bottleneck_id": id(bottleneck),
                    "description": "Break up long dependency chain",
                    "action_items": [
                        "Identify tasks that can be executed in parallel",
                        "Restructure dependencies to increase parallelism",
                        "Consider alternative implementation approaches"
                    ],
                    "affected_tasks": [task["id"] for task in bottleneck.get("tasks", [])]
                })
            
            elif bottleneck_type in ["missing_skill", "limited_skill", "insufficient_skill_level"]:
                # Recommend addressing skill shortages
                skill = bottleneck.get("skill", "")
                
                recommendations.append({
                    "type": "skill_acquisition",
                    "priority": "high" if bottleneck_type == "missing_skill" else "medium",
                    "bottleneck_id": id(bottleneck),
                    "description": f"Address shortage of {skill} skill",
                    "action_items": [
                        f"Train existing resources on {skill}",
                        f"Hire contractors with {skill} expertise",
                        f"Reassess task requirements for {skill}"
                    ],
                    "affected_tasks": [task["id"] for task in bottleneck.get("tasks", [])]
                })
        
        # Remove duplicates and sort by priority
        unique_recommendations = {}
        for rec in recommendations:
            key = f"{rec['type']}_{rec['description']}"
            unique_recommendations[key] = rec
        
        # Sort by priority
        priority_map = {"high": 3, "medium": 2, "low": 1}
        sorted_recommendations = sorted(
            unique_recommendations.values(),
            key=lambda x: priority_map.get(x["priority"], 0),
            reverse=True
        )
        
        return sorted_recommendations
    
    async def _analyze_bottleneck_impact(
        self,
        bottlenecks: List[Dict[str, Any]],
        tasks: List[Any],
        plan: Any
    ) -> Dict[str, Any]:
        """
        Analyze the impact of bottlenecks on the plan.
        
        Args:
            bottlenecks: List of identified bottlenecks
            tasks: Task data
            plan: Plan data
            
        Returns:
            Dict[str, Any]: Impact analysis
        """
        # Count bottlenecks by type and severity
        bottleneck_types = {}
        severity_levels = {
            "critical": 0,  # Severity 8-10
            "high": 0,      # Severity 6-8
            "medium": 0,    # Severity 4-6
            "low": 0        # Severity 0-4
        }
        
        for bottleneck in bottlenecks:
            bottleneck_type = bottleneck.get("type", "unknown")
            severity = bottleneck.get("severity", 0)
            
            # Count by type
            if bottleneck_type not in bottleneck_types:
                bottleneck_types[bottleneck_type] = 0
            bottleneck_types[bottleneck_type] += 1
            
            # Count by severity
            if severity >= 8:
                severity_levels["critical"] += 1
            elif severity >= 6:
                severity_levels["high"] += 1
            elif severity >= 4:
                severity_levels["medium"] += 1
            else:
                severity_levels["low"] += 1
        
        # Calculate affected tasks
        affected_task_ids = set()
        for bottleneck in bottlenecks:
            # Add task IDs from various bottleneck types
            if "task_id" in bottleneck:
                affected_task_ids.add(bottleneck["task_id"])
            
            if "tasks" in bottleneck and isinstance(bottleneck["tasks"], list):
                for task in bottleneck["tasks"]:
                    if isinstance(task, dict) and "id" in task:
                        affected_task_ids.add(task["id"])
        
        affected_task_count = len(affected_task_ids)
        total_task_count = len(tasks)
        affected_percentage = (affected_task_count / total_task_count * 100) if total_task_count > 0 else 0
        
        # Calculate estimated impact on timeline
        estimated_delay_days = 0
        for bottleneck in bottlenecks:
            severity = bottleneck.get("severity", 0)
            bottleneck_type = bottleneck.get("type", "")
            
            # Estimate delay based on bottleneck type and severity
            if bottleneck_type == "resource_overallocation":
                estimated_delay_days += severity * 0.5  # 0.5 days per severity point
            elif bottleneck_type == "critical_resource_dependency":
                estimated_delay_days += severity * 0.7  # 0.7 days per severity point
            elif bottleneck_type in ["high_incoming_dependencies", "high_outgoing_dependencies"]:
                estimated_delay_days += severity * 0.3  # 0.3 days per severity point
            elif bottleneck_type == "long_dependency_chain":
                estimated_delay_days += severity * 0.6  # 0.6 days per severity point
            elif bottleneck_type in ["missing_skill", "limited_skill", "insufficient_skill_level"]:
                estimated_delay_days += severity * 0.8  # 0.8 days per severity point
        
        # Cap estimated delay
        estimated_delay_days = min(estimated_delay_days, 60)  # Cap at 60 days
        
        # Calculate risk score
        risk_score = min(
            (severity_levels["critical"] * 10 +
            severity_levels["high"] * 5 +
            severity_levels["medium"] * 2 +
            severity_levels["low"] * 1) / 10,
            10
        )
        
        # Determine risk level
        risk_level = "low"
        if risk_score >= 7:
            risk_level = "critical"
        elif risk_score >= 5:
            risk_level = "high"
        elif risk_score >= 3:
            risk_level = "medium"
        
        return {
            "summary": {
                "total_bottlenecks": len(bottlenecks),
                "bottleneck_types": bottleneck_types,
                "severity_counts": severity_levels,
                "affected_tasks": affected_task_count,
                "affected_percentage": affected_percentage,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "estimated_delay_days": estimated_delay_days
            },
            "delay_impact": {
                "estimated_delay_days": estimated_delay_days,
                "original_end_date": getattr(plan, "end_date", datetime.utcnow() + timedelta(days=30)).isoformat(),
                "projected_end_date": (getattr(plan, "end_date", datetime.utcnow() + timedelta(days=30)) + timedelta(days=estimated_delay_days)).isoformat()
            },
            "most_impacted_areas": [k for k, v in sorted(bottleneck_types.items(), key=lambda item: item[1], reverse=True)],
            "risk_assessment": {
                "score": risk_score,
                "level": risk_level,
                "factors": [b["type"] for b in bottlenecks if b.get("severity", 0) >= 7]
            }
        }
