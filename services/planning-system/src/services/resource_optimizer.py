"""
Resource Optimizer component for the Planning System service.

This module implements the resource optimization component, which handles
resource allocation optimization and resource utilization analysis.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from uuid import UUID
from datetime import datetime, timedelta

from shared.utils.src.messaging import EventBus

from ..models.api import (
    OptimizationRequest,
    OptimizationResult,
    ResourceType,
    StrategicPlanResponse,
    PaginatedResponse
)
from ..exceptions import (
    PlanNotFoundError,
    ResourceAllocationError
)
from .repository import PlanningRepository
from .base import BasePlannerComponent

class ResourceOptimizer(BasePlannerComponent):
    """
    Resource optimization component.
    
    This component handles resource allocation optimization and
    resource utilization analysis for the planning system.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the resource optimizer.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        super().__init__(repository, event_bus, "ResourceOptimizer")
    
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
        await self._log_operation(
            "Optimizing", 
            "resources", 
            entity_id=request.plan_id
        )
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(request.plan_id)
        if not plan:
            await self._handle_not_found_error("plan", request.plan_id, PlanNotFoundError)
        
        # Load tasks, resources, and current allocations
        tasks = await self.repository.get_tasks_by_plan(request.plan_id)
        resources = await self.repository.get_resources_for_plan(request.plan_id)
        current_allocations = await self.repository.get_resource_allocations_for_plan(request.plan_id)
        
        try:
            # Run optimization algorithm
            optimization_result = await self._run_optimization_algorithm(
                plan=plan,
                tasks=tasks,
                resources=resources,
                current_allocations=current_allocations,
                optimization_target=request.optimization_target,
                constraints=request.constraints,
                preferences=request.preferences
            )
            
            # Create optimization record
            result_record = {
                "plan_id": request.plan_id,
                "generated_at": datetime.utcnow(),
                "optimization_target": request.optimization_target,
                "constraints": request.constraints,
                "preferences": request.preferences,
                "status": optimization_result["status"],
                "task_adjustments": optimization_result["task_adjustments"],
                "resource_assignments": optimization_result["resource_assignments"],
                "metrics": optimization_result["metrics"],
                "improvements": optimization_result["improvements"]
            }
            
            # Store optimization result
            stored_result = await self.repository.create_optimization_result(result_record)
            
            # Publish event
            await self._publish_event(
                "resources.optimization.completed", 
                stored_result,
                {"plan_id": str(request.plan_id)}
            )
            
            # Convert to response model
            return OptimizationResult(
                id=stored_result.id,
                plan_id=stored_result.plan_id,
                generated_at=stored_result.generated_at,
                optimization_target=stored_result.optimization_target,
                status=stored_result.status,
                task_adjustments=stored_result.task_adjustments,
                resource_assignments=stored_result.resource_assignments,
                metrics=stored_result.metrics,
                improvements=stored_result.improvements
            )
        except Exception as e:
            self.logger.error(f"Error optimizing resources: {str(e)}")
            raise ResourceAllocationError(
                message=f"Failed to optimize resources: {str(e)}",
                details={"plan_id": str(request.plan_id)}
            )
    
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
        await self._log_operation(
            "Applying", 
            "optimization", 
            entity_id=optimization_id,
            entity_name=f"to plan {plan_id}"
        )
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get optimization result
        optimization = await self.repository.get_optimization_result(optimization_id)
        if not optimization:
            raise ResourceAllocationError(
                message=f"Optimization result not found: {optimization_id}",
                details={"optimization_id": str(optimization_id)}
            )
        
        # Verify optimization is for the specified plan
        if optimization.plan_id != plan_id:
            raise ResourceAllocationError(
                message="Optimization result is for a different plan",
                details={
                    "optimization_id": str(optimization_id),
                    "optimization_plan_id": str(optimization.plan_id),
                    "specified_plan_id": str(plan_id)
                }
            )
        
        try:
            # Apply task adjustments
            for task_id_str, adjustments in optimization.task_adjustments.items():
                task_id = UUID(task_id_str)
                
                # Skip tasks that don't need adjustments
                if not adjustments:
                    continue
                
                # Update task
                await self.repository.update_task(task_id, adjustments)
            
            # Apply resource assignments
            for resource_id_str, assignments in optimization.resource_assignments.items():
                resource_id = UUID(resource_id_str)
                
                # Delete existing allocations
                await self.repository.delete_resource_allocations_for_resource(
                    resource_id=resource_id,
                    plan_id=plan_id
                )
                
                # Create new allocations
                for assignment in assignments:
                    allocation_data = {
                        "resource_id": resource_id,
                        "task_id": UUID(assignment["task_id"]),
                        "allocation_percentage": assignment["allocation_percentage"],
                        "assigned_hours": assignment["assigned_hours"],
                        "start_date": datetime.fromisoformat(assignment["start_date"]),
                        "end_date": datetime.fromisoformat(assignment["end_date"])
                    }
                    
                    await self.repository.create_resource_allocation(allocation_data)
            
            # Mark optimization as applied
            await self.repository.update_optimization_result(
                optimization_id=optimization_id,
                update_data={"applied": True, "applied_at": datetime.utcnow()}
            )
            
            # Publish event
            await self._publish_event(
                "resources.optimization.applied", 
                optimization,
                {
                    "plan_id": str(plan_id),
                    "applied_at": datetime.utcnow().isoformat()
                }
            )
            
            # Get updated plan
            updated_plan = await self.repository.get_plan_by_id(plan_id)
            
            # Convert to response model (would use StrategicPlanner's to_response_model in real impl)
            # This is a placeholder
            return await self.repository.convert_plan_to_response(updated_plan)
        except Exception as e:
            self.logger.error(f"Error applying optimization: {str(e)}")
            raise ResourceAllocationError(
                message=f"Failed to apply optimization: {str(e)}",
                details={
                    "plan_id": str(plan_id),
                    "optimization_id": str(optimization_id)
                }
            )
    
    async def get_optimization_history(
        self,
        plan_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedResponse:
        """
        Get optimization history for a plan.
        
        Args:
            plan_id: Plan ID
            page: Page number
            page_size: Items per page
            
        Returns:
            PaginatedResponse: Paginated list of optimization results
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        await self._log_operation(
            "Getting", 
            "optimization history", 
            entity_id=plan_id
        )
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get optimization history
        results, total = await self.repository.get_optimization_history(
            plan_id=plan_id,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        result_items = []
        for result in results:
            result_items.append(OptimizationResult(
                id=result.id,
                plan_id=result.plan_id,
                generated_at=result.generated_at,
                optimization_target=result.optimization_target,
                status=result.status,
                task_adjustments=result.task_adjustments,
                resource_assignments=result.resource_assignments,
                metrics=result.metrics,
                improvements=result.improvements,
                applied=getattr(result, "applied", False),
                applied_at=getattr(result, "applied_at", None)
            ))
        
        # Build paginated response
        return PaginatedResponse(
            items=result_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    
    async def get_resource_utilization(
        self,
        plan_id: UUID,
        resource_type: Optional[ResourceType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get resource utilization for a plan.
        
        Args:
            plan_id: Plan ID
            resource_type: Optional resource type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict[str, Any]: Resource utilization data
            
        Raises:
            PlanNotFoundError: If plan not found
        """
        await self._log_operation(
            "Analyzing", 
            "resource utilization", 
            entity_id=plan_id
        )
        
        # Validate plan exists
        plan = await self.repository.get_plan_by_id(plan_id)
        if not plan:
            await self._handle_not_found_error("plan", plan_id, PlanNotFoundError)
        
        # Get resources and allocations
        resources = await self.repository.get_resources_for_plan(
            plan_id=plan_id,
            resource_type=resource_type
        )
        
        allocations = await self.repository.get_resource_allocations_for_plan(
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate utilization
        utilization = await self._calculate_resource_utilization(
            resources=resources,
            allocations=allocations,
            start_date=start_date or self._get_plan_start_date(plan),
            end_date=end_date or self._get_plan_end_date(plan)
        )
        
        return utilization
    
    # Helper methods
    
    async def _run_optimization_algorithm(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        current_allocations: List[Any],
        optimization_target: str,
        constraints: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run optimization algorithm for resource allocation.
        
        Args:
            plan: Plan data
            tasks: List of tasks
            resources: List of resources
            current_allocations: Current resource allocations
            optimization_target: Optimization target
            constraints: Optimization constraints
            preferences: Optional optimization preferences
            
        Returns:
            Dict[str, Any]: Optimization result
        """
        self.logger.info(f"Running {optimization_target} optimization for plan {plan.id}")
        
        # In a real implementation, this would use more sophisticated algorithms
        # based on the optimization target (duration, cost, resource utilization)
        # For this example, we'll implement a simplified version
        
        # Store original metrics for comparison
        original_metrics = await self._calculate_plan_metrics(
            plan=plan,
            tasks=tasks,
            resources=resources,
            allocations=current_allocations
        )
        
        # Initialize result data
        task_adjustments = {}
        resource_assignments = {}
        
        # Apply different optimization strategies based on target
        if optimization_target == "duration":
            # Duration optimization focuses on critical path and parallel execution
            optimization_data = await self._optimize_for_duration(
                plan=plan,
                tasks=tasks,
                resources=resources,
                current_allocations=current_allocations,
                constraints=constraints,
                preferences=preferences
            )
        elif optimization_target == "cost":
            # Cost optimization focuses on using cheaper resources when possible
            optimization_data = await self._optimize_for_cost(
                plan=plan,
                tasks=tasks,
                resources=resources,
                current_allocations=current_allocations,
                constraints=constraints,
                preferences=preferences
            )
        elif optimization_target == "resource_utilization":
            # Resource utilization optimization focuses on balancing workload
            optimization_data = await self._optimize_for_resource_utilization(
                plan=plan,
                tasks=tasks,
                resources=resources,
                current_allocations=current_allocations,
                constraints=constraints,
                preferences=preferences
            )
        else:
            raise ValueError(f"Unsupported optimization target: {optimization_target}")
        
        # Extract optimization results
        task_adjustments = optimization_data["task_adjustments"]
        resource_assignments = optimization_data["resource_assignments"]
        status = optimization_data["status"]
        
        # Calculate new metrics
        # In a real implementation, we would apply the changes temporarily
        # to calculate new metrics, but for this example we'll use placeholder values
        new_metrics = {
            "duration": original_metrics["duration"] * 0.9,  # 10% improvement
            "cost": original_metrics["cost"] * 0.95,  # 5% improvement
            "resource_utilization": min(original_metrics["resource_utilization"] * 1.15, 1.0),  # 15% improvement
            "overallocated_resources": max(original_metrics["overallocated_resources"] - 2, 0),  # Reduction by 2
        }
        
        # Calculate improvements
        improvements = {
            "duration_reduction": original_metrics["duration"] - new_metrics["duration"],
            "cost_reduction": original_metrics["cost"] - new_metrics["cost"],
            "utilization_improvement": new_metrics["resource_utilization"] - original_metrics["resource_utilization"],
            "overallocation_reduction": original_metrics["overallocated_resources"] - new_metrics["overallocated_resources"],
            "percent_improvements": {
                "duration": ((original_metrics["duration"] - new_metrics["duration"]) / original_metrics["duration"]) * 100 if original_metrics["duration"] > 0 else 0,
                "cost": ((original_metrics["cost"] - new_metrics["cost"]) / original_metrics["cost"]) * 100 if original_metrics["cost"] > 0 else 0,
                "resource_utilization": ((new_metrics["resource_utilization"] - original_metrics["resource_utilization"]) / original_metrics["resource_utilization"]) * 100 if original_metrics["resource_utilization"] > 0 else 0,
            }
        }
        
        return {
            "status": status,
            "task_adjustments": task_adjustments,
            "resource_assignments": resource_assignments,
            "metrics": new_metrics,
            "improvements": improvements
        }
    
    async def _optimize_for_duration(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        current_allocations: List[Any],
        constraints: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize resource allocation for minimal duration.
        
        Args:
            plan: Plan data
            tasks: List of tasks
            resources: List of resources
            current_allocations: Current resource allocations
            constraints: Optimization constraints
            preferences: Optional optimization preferences
            
        Returns:
            Dict[str, Any]: Optimization data
        """
        # In a real implementation, this would use critical path analysis
        # and resource leveling algorithms to minimize project duration
        # For this example, we'll create placeholder data
        
        task_adjustments = {}
        resource_assignments = {}
        
        # Identify critical path tasks (simplified example)
        critical_path_tasks = []
        for task in tasks:
            # Simplified check - in reality, would use proper CPM
            if task.priority == "critical" or task.priority == "high":
                critical_path_tasks.append(task)
        
        # Prioritize resource allocation for critical path tasks
        for task in critical_path_tasks:
            # Allocate best resources to critical path tasks
            task_adjustments[str(task.id)] = {}
            resource_assignments[str(task.id)] = []
            
            # Find suitable resources
            suitable_resources = [
                r for r in resources
                if (
                    not task.required_skills or
                    all(skill in r.skills and r.skills[skill] >= proficiency 
                        for skill, proficiency in task.required_skills.items())
                )
            ]
            
            # Sort resources by performance rating (if available)
            if suitable_resources:
                suitable_resources.sort(
                    key=lambda r: getattr(r, "performance_rating", 0),
                    reverse=True
                )
                
                # Allocate top-performing resource
                best_resource = suitable_resources[0]
                
                # Calculate dates (simplified)
                start_date = datetime.utcnow()  # In reality, would calculate based on dependencies
                end_date = start_date + timedelta(hours=task.estimated_duration)
                
                # Create assignment
                if str(best_resource.id) not in resource_assignments:
                    resource_assignments[str(best_resource.id)] = []
                
                resource_assignments[str(best_resource.id)].append({
                    "task_id": str(task.id),
                    "allocation_percentage": 100,
                    "assigned_hours": task.estimated_effort,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                })
                
                # Adjust task duration if resource is high-performing
                if getattr(best_resource, "performance_rating", 0) > 0.8:
                    # Reduce duration by performance factor
                    new_duration = task.estimated_duration * 0.8
                    task_adjustments[str(task.id)]["estimated_duration"] = new_duration
        
        return {
            "status": "optimal",
            "task_adjustments": task_adjustments,
            "resource_assignments": resource_assignments
        }
    
    async def _optimize_for_cost(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        current_allocations: List[Any],
        constraints: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize resource allocation for minimal cost.
        
        Args:
            plan: Plan data
            tasks: List of tasks
            resources: List of resources
            current_allocations: Current resource allocations
            constraints: Optimization constraints
            preferences: Optional optimization preferences
            
        Returns:
            Dict[str, Any]: Optimization data
        """
        # In a real implementation, this would use cost-based algorithms
        # to find the most cost-effective resource assignments
        # For this example, we'll create placeholder data
        
        task_adjustments = {}
        resource_assignments = {}
        
        # Add cost attribute to resources if not present
        for resource in resources:
            if not hasattr(resource, "cost_per_hour"):
                # Default value for resources without cost data
                resource.cost_per_hour = 50
        
        # Sort resources by cost
        resources.sort(key=lambda r: getattr(r, "cost_per_hour", 50))
        
        # Allocate resources to tasks based on cost
        for task in tasks:
            task_adjustments[str(task.id)] = {}
            
            # Find suitable resources
            suitable_resources = [
                r for r in resources
                if (
                    not task.required_skills or
                    all(skill in r.skills and r.skills[skill] >= proficiency 
                        for skill, proficiency in task.required_skills.items())
                )
            ]
            
            if suitable_resources:
                # Use the cheapest suitable resource
                cheapest_resource = suitable_resources[0]
                
                # Calculate dates (simplified)
                start_date = datetime.utcnow()  # In reality, would calculate based on dependencies
                end_date = start_date + timedelta(hours=task.estimated_duration)
                
                # Create assignment
                if str(cheapest_resource.id) not in resource_assignments:
                    resource_assignments[str(cheapest_resource.id)] = []
                
                resource_assignments[str(cheapest_resource.id)].append({
                    "task_id": str(task.id),
                    "allocation_percentage": 100,
                    "assigned_hours": task.estimated_effort,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                })
                
                # For non-critical tasks, can we extend duration to reduce cost?
                if task.priority in ["low", "medium"]:
                    # Increase duration but reduce effort (assuming less intensive work)
                    new_duration = task.estimated_duration * 1.2
                    new_effort = task.estimated_effort * 0.9
                    
                    task_adjustments[str(task.id)].update({
                        "estimated_duration": new_duration,
                        "estimated_effort": new_effort
                    })
        
        return {
            "status": "optimal",
            "task_adjustments": task_adjustments,
            "resource_assignments": resource_assignments
        }
    
    async def _optimize_for_resource_utilization(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        current_allocations: List[Any],
        constraints: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize resource allocation for balanced utilization.
        
        Args:
            plan: Plan data
            tasks: List of tasks
            resources: List of resources
            current_allocations: Current resource allocations
            constraints: Optimization constraints
            preferences: Optional optimization preferences
            
        Returns:
            Dict[str, Any]: Optimization data
        """
        # In a real implementation, this would use resource leveling algorithms
        # to balance resource utilization across the plan
        # For this example, we'll create placeholder data
        
        task_adjustments = {}
        resource_assignments = {}
        
        # Calculate current utilization per resource
        resource_utilization = {}
        for resource in resources:
            resource_utilization[str(resource.id)] = 0
        
        for allocation in current_allocations:
            if str(allocation.resource_id) in resource_utilization:
                resource_utilization[str(allocation.resource_id)] += allocation.assigned_hours
        
        # Sort resources by utilization (least utilized first)
        sorted_resources = sorted(
            resources,
            key=lambda r: resource_utilization.get(str(r.id), 0)
        )
        
        # Allocate tasks to balance utilization
        for task in tasks:
            # Find suitable resources
            suitable_resources = [
                r for r in sorted_resources
                if (
                    not task.required_skills or
                    all(skill in r.skills and r.skills[skill] >= proficiency 
                        for skill, proficiency in task.required_skills.items())
                )
            ]
            
            if suitable_resources:
                # Use the least utilized suitable resource
                selected_resource = suitable_resources[0]
                
                # Calculate dates (simplified)
                start_date = datetime.utcnow()  # In reality, would calculate based on dependencies
                end_date = start_date + timedelta(hours=task.estimated_duration)
                
                # Create assignment
                if str(selected_resource.id) not in resource_assignments:
                    resource_assignments[str(selected_resource.id)] = []
                
                resource_assignments[str(selected_resource.id)].append({
                    "task_id": str(task.id),
                    "allocation_percentage": 100,
                    "assigned_hours": task.estimated_effort,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                })
                
                # Update utilization for next iteration
                resource_utilization[str(selected_resource.id)] += task.estimated_effort
                
                # Re-sort resources for next task
                sorted_resources = sorted(
                    sorted_resources,
                    key=lambda r: resource_utilization.get(str(r.id), 0)
                )
        
        return {
            "status": "optimal",
            "task_adjustments": task_adjustments,
            "resource_assignments": resource_assignments
        }
    
    async def _calculate_plan_metrics(
        self,
        plan: Any,
        tasks: List[Any],
        resources: List[Any],
        allocations: List[Any]
    ) -> Dict[str, Any]:
        """
        Calculate key metrics for a plan.
        
        Args:
            plan: Plan data
            tasks: List of tasks
            resources: List of resources
            allocations: Resource allocations
            
        Returns:
            Dict[str, Any]: Plan metrics
        """
        # In a real implementation, this would calculate actual metrics
        # based on the plan data
        # For this example, we'll create placeholder values
        
        # Calculate durations based on dependencies (simplified)
        # In reality, this would use critical path analysis
        if tasks:
            # Simple calculation - longest task duration
            duration = max(task.estimated_duration for task in tasks)
        else:
            duration = 0
        
        # Calculate cost based on resource costs and allocations (simplified)
        cost = 0
        for allocation in allocations:
            resource = next((r for r in resources if r.id == allocation.resource_id), None)
            if resource:
                cost_per_hour = getattr(resource, "cost_per_hour", 50)  # Default cost
                cost += allocation.assigned_hours * cost_per_hour
        
        # Calculate resource utilization (simplified)
        # In reality, this would account for resource capacity and time periods
        total_assigned_hours = sum(allocation.assigned_hours for allocation in allocations)
        total_capacity_hours = sum(getattr(resource, "capacity_hours", 40) for resource in resources)
        
        resource_utilization = total_assigned_hours / total_capacity_hours if total_capacity_hours > 0 else 0
        
        # Count overallocated resources (simplified)
        resource_allocation_hours = {}
        for allocation in allocations:
            if allocation.resource_id not in resource_allocation_hours:
                resource_allocation_hours[allocation.resource_id] = 0
            resource_allocation_hours[allocation.resource_id] += allocation.assigned_hours
        
        overallocated_resources = 0
        for resource in resources:
            capacity_hours = getattr(resource, "capacity_hours", 40)
            if resource.id in resource_allocation_hours and resource_allocation_hours[resource.id] > capacity_hours:
                overallocated_resources += 1
        
        return {
            "duration": duration,
            "cost": cost,
            "resource_utilization": resource_utilization,
            "overallocated_resources": overallocated_resources
        }
    
    async def _calculate_resource_utilization(
        self,
        resources: List[Any],
        allocations: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate resource utilization for a time period.
        
        Args:
            resources: List of resources
            allocations: Resource allocations
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dict[str, Any]: Resource utilization data
        """
        # In a real implementation, this would calculate detailed utilization
        # across the specified time period
        # For this example, we'll create simplified data
        
        # Calculate total capacity and allocation per resource
        resource_data = {}
        for resource in resources:
            resource_id = str(resource.id)
            resource_data[resource_id] = {
                "id": resource_id,
                "name": getattr(resource, "name", f"Resource {resource_id}"),
                "type": getattr(resource, "type", "human"),
                "capacity_hours": getattr(resource, "capacity_hours", 40),
                "allocated_hours": 0,
                "utilization_percentage": 0,
                "overallocated": False,
                "allocations": []
            }
        
        # Add allocation data
        for allocation in allocations:
            resource_id = str(allocation.resource_id)
            
            # Skip if resource not in our list
            if resource_id not in resource_data:
                continue
            
            # Skip if allocation outside date range
            if allocation.start_date > end_date or allocation.end_date < start_date:
                continue
            
            # Calculate overlap with date range
            overlap_start = max(allocation.start_date, start_date)
            overlap_end = min(allocation.end_date, end_date)
            
            # Calculate hours within range
            total_hours = (allocation.end_date - allocation.start_date).total_seconds() / 3600
            overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600
            
            if total_hours > 0:
                ratio = overlap_hours / total_hours
                hours_in_range = allocation.assigned_hours * ratio
            else:
                hours_in_range = 0
            
            # Update resource data
            resource_data[resource_id]["allocated_hours"] += hours_in_range
            resource_data[resource_id]["allocations"].append({
                "task_id": str(allocation.task_id),
                "hours": hours_in_range,
                "start_date": overlap_start.isoformat(),
                "end_date": overlap_end.isoformat()
            })
        
        # Calculate utilization percentages and check for overallocation
        for resource_id, data in resource_data.items():
            capacity = data["capacity_hours"]
            if capacity > 0:
                data["utilization_percentage"] = (data["allocated_hours"] / capacity) * 100
                data["overallocated"] = data["allocated_hours"] > capacity
            else:
                data["utilization_percentage"] = 0
                data["overallocated"] = False
        
        # Create summary data
        total_capacity = sum(data["capacity_hours"] for data in resource_data.values())
        total_allocated = sum(data["allocated_hours"] for data in resource_data.values())
        overall_utilization = (total_allocated / total_capacity) * 100 if total_capacity > 0 else 0
        overallocated_count = sum(1 for data in resource_data.values() if data["overallocated"])
        
        return {
            "resources": list(resource_data.values()),
            "summary": {
                "total_resources": len(resources),
                "total_capacity_hours": total_capacity,
                "total_allocated_hours": total_allocated,
                "overall_utilization": overall_utilization,
                "overallocated_resources": overallocated_count,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            }
        }
    
    def _get_plan_start_date(self, plan: Any) -> datetime:
        """
        Get the start date for a plan.
        
        Args:
            plan: Plan data
            
        Returns:
            datetime: Plan start date
        """
        # In a real implementation, this would get the actual start date
        # For this example, we'll use the current date
        return datetime.utcnow()
    
    def _get_plan_end_date(self, plan: Any) -> datetime:
        """
        Get the end date for a plan.
        
        Args:
            plan: Plan data
            
        Returns:
            datetime: Plan end date
        """
        # In a real implementation, this would get the actual end date
        # For this example, we'll use the current date + 30 days
        return datetime.utcnow() + timedelta(days=30)
