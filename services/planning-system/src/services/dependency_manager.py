"""
Dependency Manager component for the Planning System service.

This module implements the dependency management component, which handles
task dependencies, critical path analysis, and dependency validation.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID
from datetime import datetime

from shared.utils.src.messaging import EventBus

from ..models.api import (
    DependencyCreate,
    DependencyUpdate,
    DependencyResponse,
    PlanningTaskResponse,
    PaginatedResponse,
    DependencyType
)
from ..exceptions import (
    TaskNotFoundError,
    InvalidDependencyError
)
from .repository import PlanningRepository
from .base import BasePlannerComponent
from .validation import ValidationFactory

class DependencyManager(BasePlannerComponent):
    """
    Dependency management component.
    
    This component handles task dependencies, critical path analysis,
    and dependency validation for the planning system.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the dependency manager.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        super().__init__(repository, event_bus, "DependencyManager")
        self.validator = ValidationFactory.get_validator("dependency")
    
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
        await self._log_operation(
            "Creating", 
            "dependency", 
            entity_name=f"from {dependency_data.from_task_id} to {dependency_data.to_task_id}"
        )
        
        # Validate tasks exist
        from_task = await self.repository.get_task_by_id(dependency_data.from_task_id)
        if not from_task:
            await self._handle_not_found_error("task", dependency_data.from_task_id, TaskNotFoundError)
        
        to_task = await self.repository.get_task_by_id(dependency_data.to_task_id)
        if not to_task:
            await self._handle_not_found_error("task", dependency_data.to_task_id, TaskNotFoundError)
        
        # Validate tasks are in the same plan
        if from_task.plan_id != to_task.plan_id:
            raise InvalidDependencyError(
                message="Tasks must be in the same plan",
                details={
                    "from_task_id": str(dependency_data.from_task_id),
                    "from_task_plan_id": str(from_task.plan_id),
                    "to_task_id": str(dependency_data.to_task_id),
                    "to_task_plan_id": str(to_task.plan_id),
                }
            )
        
        # Validate dependency data
        context = {"dependency_manager": self}
        validation_errors = await self.validator.validate(dependency_data, context)
        if validation_errors:
            raise InvalidDependencyError(
                message="Invalid dependency data",
                validation_errors=validation_errors
            )
        
        # Check if dependency already exists
        existing = await self.repository.get_dependency(
            from_task_id=dependency_data.from_task_id,
            to_task_id=dependency_data.to_task_id
        )
        
        if existing:
            raise InvalidDependencyError(
                message="Dependency already exists",
                details={
                    "from_task_id": str(dependency_data.from_task_id),
                    "to_task_id": str(dependency_data.to_task_id),
                }
            )
        
        # Check for circular dependencies
        if await self._would_create_cycle(dependency_data.from_task_id, dependency_data.to_task_id):
            raise InvalidDependencyError(
                message="Circular dependency detected",
                validation_errors=["This dependency would create a circular reference"]
            )
        
        # Convert to dict for repository
        dependency_dict = dependency_data.model_dump()
        
        # Create dependency in repository
        dependency = await self.repository.create_dependency(dependency_dict)
        
        # Publish event
        await self._publish_event("dependency.created", dependency)
        
        # Convert to response model
        return await self._to_response_model(dependency)
    
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
        await self._log_operation(
            "Updating", 
            "dependency", 
            entity_name=f"from {from_task_id} to {to_task_id}"
        )
        
        # Get existing dependency
        dependency = await self.repository.get_dependency(
            from_task_id=from_task_id,
            to_task_id=to_task_id
        )
        
        if not dependency:
            raise InvalidDependencyError(
                message="Dependency not found",
                details={
                    "from_task_id": str(from_task_id),
                    "to_task_id": str(to_task_id),
                }
            )
        
        # Validate update data
        context = {
            "operation": "update",
            "existing_entity": dependency,
        }
        validation_errors = await self.validator.validate(dependency_data, context)
        if validation_errors:
            raise InvalidDependencyError(
                message="Invalid dependency update",
                validation_errors=validation_errors
            )
        
        # Convert to dict for repository
        update_dict = dependency_data.model_dump(exclude_unset=True)
        
        # Update dependency in repository
        dependency = await self.repository.update_dependency(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_data=update_dict
        )
        
        # Publish event
        await self._publish_event("dependency.updated", dependency)
        
        # Convert to response model
        return await self._to_response_model(dependency)
    
    async def delete_dependency(self, from_task_id: UUID, to_task_id: UUID) -> None:
        """
        Delete a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Raises:
            InvalidDependencyError: If dependency not found
        """
        await self._log_operation(
            "Deleting", 
            "dependency", 
            entity_name=f"from {from_task_id} to {to_task_id}"
        )
        
        # Get dependency data for event
        dependency = await self.repository.get_dependency(
            from_task_id=from_task_id,
            to_task_id=to_task_id
        )
        
        if not dependency:
            raise InvalidDependencyError(
                message="Dependency not found",
                details={
                    "from_task_id": str(from_task_id),
                    "to_task_id": str(to_task_id),
                }
            )
        
        # Delete dependency in repository
        success = await self.repository.delete_dependency(
            from_task_id=from_task_id,
            to_task_id=to_task_id
        )
        
        if not success:
            raise InvalidDependencyError(
                message="Failed to delete dependency",
                details={
                    "from_task_id": str(from_task_id),
                    "to_task_id": str(to_task_id),
                }
            )
        
        # Publish event
        await self._publish_event("dependency.deleted", dependency)
    
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
        await self._log_operation(
            "Listing", 
            f"{direction} dependencies", 
            entity_id=task_id
        )
        
        # Validate task exists
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            await self._handle_not_found_error("task", task_id, TaskNotFoundError)
        
        # Get dependencies from repository
        dependencies, total = await self.repository.list_dependencies(
            task_id=task_id,
            direction=direction,
            pagination={"page": page, "page_size": page_size}
        )
        
        # Convert to response models
        dependency_responses = [await self._to_response_model(dep) for dep in dependencies]
        
        # Build paginated response
        return PaginatedResponse(
            items=dependency_responses,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
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
        await self._log_operation("Calculating", "critical path", entity_id=plan_id)
        
        # Calculate critical path
        path_tasks = await self._calculate_critical_path(plan_id)
        
        # Load full task data
        task_responses = []
        for task in path_tasks:
            # Set critical path flag
            task.is_critical_path = True
            
            # Convert to response model (assuming this exists in repository or TacticalPlanner)
            # This is a placeholder - in a real implementation, we'd use the TacticalPlanner's to_response_model
            response = await self.repository.convert_task_to_response(task)
            task_responses.append(response)
        
        return task_responses
    
    async def update_dependent_tasks(self, task_id: UUID) -> None:
        """
        Update dependent tasks when a task is updated.
        
        Args:
            task_id: Updated task ID
        """
        await self._log_operation("Updating", "dependent tasks", entity_id=task_id)
        
        # Get task
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            return  # Task not found, nothing to update
        
        # Get dependent tasks
        dependent_tasks, _ = await self.repository.list_dependencies(
            task_id=task_id,
            direction="incoming",
            pagination=None  # Get all
        )
        
        # Process dependent tasks based on task status
        if task.status == "completed":
            # When a task is completed, check if dependent tasks can be set to ready
            for dependency in dependent_tasks:
                to_task = await self.repository.get_task_by_id(dependency.to_task_id)
                
                # Check if all predecessors are completed
                all_predecessors_completed = await self._are_all_predecessors_completed(to_task.id)
                
                if all_predecessors_completed and to_task.status == "planned":
                    # Update task status to ready
                    await self.repository.update_task(
                        task_id=to_task.id,
                        task_data={"status": "ready"}
                    )
                    
                    # Publish event
                    await self._publish_event(
                        "task.updated", 
                        to_task,
                        {"status_changed": True, "previous_status": "planned", "new_status": "ready"}
                    )
    
    async def is_task_on_critical_path(self, task_id: UUID) -> bool:
        """
        Check if a task is on the critical path.
        
        Args:
            task_id: Task ID
            
        Returns:
            bool: True if the task is on the critical path, False otherwise
        """
        # Get task
        task = await self.repository.get_task_by_id(task_id)
        if not task:
            return False
        
        # Get critical path for the plan
        critical_path_tasks = await self._calculate_critical_path(task.plan_id)
        
        # Check if task is in the critical path
        return any(path_task.id == task_id for path_task in critical_path_tasks)
    
    async def would_create_cycle(self, from_task_id: UUID, to_task_id: UUID) -> bool:
        """
        Check if adding a dependency would create a cycle.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Returns:
            bool: True if adding the dependency would create a cycle, False otherwise
        """
        return await self._would_create_cycle(from_task_id, to_task_id)
    
    # Helper methods
    
    async def _to_response_model(self, dependency) -> DependencyResponse:
        """
        Convert a dependency model to a response model.
        
        Args:
            dependency: Dependency model
            
        Returns:
            DependencyResponse: Dependency response model
        """
        # Get task names
        from_task = await self.repository.get_task_by_id(dependency.from_task_id)
        to_task = await self.repository.get_task_by_id(dependency.to_task_id)
        
        from_task_name = from_task.name if from_task else "Unknown Task"
        to_task_name = to_task.name if to_task else "Unknown Task"
        
        # Check if dependency is on critical path
        is_critical = False
        if from_task and to_task:
            # Get critical path for the plan
            critical_path_tasks = await self._calculate_critical_path(from_task.plan_id)
            critical_path_ids = [task.id for task in critical_path_tasks]
            
            # Check if both tasks are in the critical path and adjacent
            if (from_task.id in critical_path_ids and to_task.id in critical_path_ids):
                from_index = critical_path_ids.index(from_task.id)
                to_index = critical_path_ids.index(to_task.id)
                
                if from_index + 1 == to_index:
                    is_critical = True
        
        # Convert to response model
        return DependencyResponse(
            id=dependency.id,
            from_task_id=dependency.from_task_id,
            to_task_id=dependency.to_task_id,
            from_task_name=from_task_name,
            to_task_name=to_task_name,
            dependency_type=dependency.dependency_type,
            lag=dependency.lag,
            created_at=dependency.created_at,
            updated_at=dependency.updated_at,
            critical=is_critical,
        )
    
    async def _calculate_critical_path(self, plan_id: UUID) -> List[Any]:
        """
        Calculate the critical path for a plan.
        
        This implements a simplified version of the Critical Path Method (CPM).
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List[Any]: Tasks on the critical path
        """
        # Get all tasks for the plan
        tasks = await self.repository.get_tasks_by_plan(plan_id)
        if not tasks:
            return []
        
        # Build dependency graph
        graph = {}
        for task in tasks:
            graph[task.id] = {
                "task": task,
                "duration": task.estimated_duration,
                "predecessors": [],
                "successors": [],
                "earliest_start": 0,
                "earliest_finish": task.estimated_duration,
                "latest_start": 0,  # Will be calculated later
                "latest_finish": 0,  # Will be calculated later
                "slack": 0,  # Will be calculated later
            }
        
        # Add dependencies
        for task_id, node in graph.items():
            # Get outgoing dependencies (tasks that depend on this task)
            outgoing, _ = await self.repository.list_dependencies(
                task_id=task_id,
                direction="outgoing",
                pagination=None  # Get all
            )
            
            for dep in outgoing:
                if dep.to_task_id in graph:
                    node["successors"].append(dep.to_task_id)
                    graph[dep.to_task_id]["predecessors"].append(task_id)
        
        # Find start nodes (tasks with no predecessors)
        start_nodes = [task_id for task_id, node in graph.items() if not node["predecessors"]]
        
        # Forward pass - calculate earliest start and finish times
        # Starting with nodes that have no predecessors
        processed = set(start_nodes)
        to_process = start_nodes.copy()
        
        while to_process:
            task_id = to_process.pop(0)
            node = graph[task_id]
            
            # For each successor, calculate earliest start time
            for successor_id in node["successors"]:
                successor = graph[successor_id]
                
                # Earliest start time is the maximum of all predecessors' earliest finish times
                new_earliest_start = max(
                    successor["earliest_start"],
                    node["earliest_finish"]
                )
                
                # Update earliest start and finish times
                successor["earliest_start"] = new_earliest_start
                successor["earliest_finish"] = new_earliest_start + successor["duration"]
                
                # Add successor to processing queue if all its predecessors have been processed
                if (
                    successor_id not in processed and
                    all(pred in processed for pred in successor["predecessors"])
                ):
                    to_process.append(successor_id)
                    processed.add(successor_id)
        
        # Find end nodes (tasks with no successors)
        end_nodes = [task_id for task_id, node in graph.items() if not node["successors"]]
        
        # Find project completion time (maximum earliest finish of all tasks)
        project_completion = max(graph[task_id]["earliest_finish"] for task_id in end_nodes)
        
        # Backward pass - calculate latest start and finish times
        # Starting with the end nodes
        for task_id in graph:
            if task_id in end_nodes:
                # For end nodes, latest finish = project completion
                graph[task_id]["latest_finish"] = project_completion
            else:
                # For other nodes, initialize to a large value
                graph[task_id]["latest_finish"] = float("inf")
        
        # Process all tasks in reverse topological order
        processed = set()
        to_process = end_nodes.copy()
        
        while to_process:
            task_id = to_process.pop(0)
            node = graph[task_id]
            processed.add(task_id)
            
            # Calculate latest start time
            node["latest_start"] = node["latest_finish"] - node["duration"]
            
            # For each predecessor, calculate latest finish time
            for predecessor_id in node["predecessors"]:
                predecessor = graph[predecessor_id]
                
                # Latest finish time is the minimum of all successors' latest start times
                new_latest_finish = min(
                    predecessor["latest_finish"],
                    node["latest_start"]
                )
                
                # Update latest finish time
                predecessor["latest_finish"] = new_latest_finish
                
                # Add predecessor to processing queue if not already processed
                if predecessor_id not in processed:
                    to_process.append(predecessor_id)
        
        # Calculate slack and identify critical path
        critical_path_ids = []
        for task_id, node in graph.items():
            # Calculate slack
            node["slack"] = node["latest_start"] - node["earliest_start"]
            
            # Tasks with zero slack are on the critical path
            if node["slack"] == 0:
                critical_path_ids.append(task_id)
        
        # Sort critical path in correct order
        ordered_path = []
        current_ids = [task_id for task_id in critical_path_ids if not graph[task_id]["predecessors"] or all(pred not in critical_path_ids for pred in graph[task_id]["predecessors"])]
        
        while current_ids:
            task_id = current_ids.pop(0)
            ordered_path.append(graph[task_id]["task"])
            
            # Find successors on critical path
            for succ_id in graph[task_id]["successors"]:
                if succ_id in critical_path_ids and succ_id not in ordered_path:
                    # Add to current_ids if all predecessors have been processed
                    if all(pred not in critical_path_ids or graph[pred]["task"] in ordered_path for pred in graph[succ_id]["predecessors"]):
                        current_ids.append(succ_id)
        
        # Store schedule data for tasks
        for task_id, node in graph.items():
            await self.repository.update_task_schedule_data(
                task_id=task_id,
                schedule_data={
                    "earliest_start": datetime.utcnow(),  # Placeholder - would use actual dates
                    "earliest_finish": datetime.utcnow(),  # Placeholder
                    "latest_start": datetime.utcnow(),  # Placeholder
                    "latest_finish": datetime.utcnow(),  # Placeholder
                    "slack": node["slack"]
                }
            )
        
        return ordered_path
    
    async def _would_create_cycle(self, from_task_id: UUID, to_task_id: UUID) -> bool:
        """
        Check if adding a dependency would create a cycle.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Returns:
            bool: True if adding the dependency would create a cycle, False otherwise
        """
        # If to_task depends on from_task (directly or indirectly), adding a dependency
        # from from_task to to_task would create a cycle
        
        # Get all dependencies as a graph
        dependencies, _ = await self.repository.get_all_dependencies_for_plan_containing_task(
            task_id=from_task_id
        )
        
        # Build a graph representation
        graph = {}
        for dep in dependencies:
            if dep.from_task_id not in graph:
                graph[dep.from_task_id] = []
            graph[dep.from_task_id].append(dep.to_task_id)
        
        # Add the new dependency
        if from_task_id not in graph:
            graph[from_task_id] = []
        if to_task_id not in graph:
            graph[to_task_id] = []
        
        # DFS to check for cycles
        def has_path(start, end, visited=None):
            if visited is None:
                visited = set()
            
            if start == end:
                return True
            
            visited.add(start)
            
            for neighbor in graph.get(start, []):
                if neighbor not in visited:
                    if has_path(neighbor, end, visited):
                        return True
            
            return False
        
        # If there's a path from to_task to from_task, adding the new dependency
        # would create a cycle
        return has_path(to_task_id, from_task_id)
    
    async def _are_all_predecessors_completed(self, task_id: UUID) -> bool:
        """
        Check if all predecessors of a task are completed.
        
        Args:
            task_id: Task ID
            
        Returns:
            bool: True if all predecessors are completed, False otherwise
        """
        # Get incoming dependencies
        dependencies, _ = await self.repository.list_dependencies(
            task_id=task_id,
            direction="incoming",
            pagination=None  # Get all
        )
        
        if not dependencies:
            return True  # No dependencies means all prerequisites are met
        
        # Check if all predecessor tasks are completed
        for dep in dependencies:
            predecessor = await self.repository.get_task_by_id(dep.from_task_id)
            if not predecessor or predecessor.status != "completed":
                return False
        
        return True
