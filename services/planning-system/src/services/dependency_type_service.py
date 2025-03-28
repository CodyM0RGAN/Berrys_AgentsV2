"""
Dependency Type Service for the Planning System.

This module implements the dependency type service, which manages dependency types
and provides functionality for dependency type validation and analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID
from datetime import datetime, timedelta

from shared.utils.src.messaging import EventBus

from ..models.api import (
    DependencyType,
    DependencyTypeInfo,
    PaginatedResponse
)
from ..exceptions import (
    InvalidDependencyError
)
from .repository import PlanningRepository
from .base import BasePlannerComponent

logger = logging.getLogger(__name__)

class DependencyTypeService(BasePlannerComponent):
    """
    Dependency Type Service.
    
    This service manages dependency types and provides functionality for
    dependency type validation and analysis.
    """
    
    def __init__(
        self,
        repository: PlanningRepository,
        event_bus: EventBus,
    ):
        """
        Initialize the dependency type service.
        
        Args:
            repository: Planning repository
            event_bus: Event bus
        """
        super().__init__(repository, event_bus, "DependencyTypeService")
        
        # Initialize dependency type definitions
        self.dependency_types = self._initialize_dependency_types()
    
    def _initialize_dependency_types(self) -> Dict[str, DependencyTypeInfo]:
        """
        Initialize dependency type definitions.
        
        Returns:
            Dict[str, DependencyTypeInfo]: Dependency type definitions
        """
        return {
            DependencyType.FINISH_TO_START: DependencyTypeInfo(
                type=DependencyType.FINISH_TO_START,
                description="Task B can start only after Task A finishes",
                scheduling_rule="B.start >= A.finish + lag",
                is_default=True,
                allows_negative_lag=False,
                visualization_style="solid_arrow"
            ),
            DependencyType.START_TO_START: DependencyTypeInfo(
                type=DependencyType.START_TO_START,
                description="Task B can start only after Task A starts",
                scheduling_rule="B.start >= A.start + lag",
                is_default=False,
                allows_negative_lag=True,
                visualization_style="dashed_arrow"
            ),
            DependencyType.FINISH_TO_FINISH: DependencyTypeInfo(
                type=DependencyType.FINISH_TO_FINISH,
                description="Task B can finish only after Task A finishes",
                scheduling_rule="B.finish >= A.finish + lag",
                is_default=False,
                allows_negative_lag=True,
                visualization_style="dotted_arrow"
            ),
            DependencyType.START_TO_FINISH: DependencyTypeInfo(
                type=DependencyType.START_TO_FINISH,
                description="Task B can finish only after Task A starts",
                scheduling_rule="B.finish >= A.start + lag",
                is_default=False,
                allows_negative_lag=True,
                visualization_style="dash_dot_arrow"
            ),
            DependencyType.BLOCKS: DependencyTypeInfo(
                type=DependencyType.BLOCKS,
                description="Task A blocks Task B (prevents execution)",
                scheduling_rule="If A.status == 'in_progress', B.status cannot be 'in_progress'",
                is_default=False,
                allows_negative_lag=False,
                visualization_style="red_arrow"
            ),
            DependencyType.RELATES_TO: DependencyTypeInfo(
                type=DependencyType.RELATES_TO,
                description="Task A is related to Task B (informational only)",
                scheduling_rule="No scheduling constraint",
                is_default=False,
                allows_negative_lag=False,
                visualization_style="dotted_line"
            )
        }
    
    async def get_dependency_types(self) -> List[DependencyTypeInfo]:
        """
        Get all dependency types.
        
        Returns:
            List[DependencyTypeInfo]: List of dependency types
        """
        await self._log_operation("Getting", "dependency types")
        
        return list(self.dependency_types.values())
    
    async def get_dependency_type_info(self, dependency_type: str) -> Optional[DependencyTypeInfo]:
        """
        Get information about a specific dependency type.
        
        Args:
            dependency_type: Dependency type
            
        Returns:
            Optional[DependencyTypeInfo]: Dependency type information or None if not found
        """
        await self._log_operation("Getting", "dependency type info", entity_name=dependency_type)
        
        return self.dependency_types.get(dependency_type)
    
    async def validate_dependency_type(
        self,
        dependency_type: str,
        from_task_id: UUID,
        to_task_id: UUID,
        lag: Optional[int] = None
    ) -> List[str]:
        """
        Validate a dependency type for a specific dependency.
        
        Args:
            dependency_type: Dependency type
            from_task_id: Source task ID
            to_task_id: Target task ID
            lag: Optional lag value
            
        Returns:
            List[str]: Validation errors, empty if valid
        """
        await self._log_operation(
            "Validating", 
            "dependency type", 
            entity_name=f"{dependency_type} from {from_task_id} to {to_task_id}"
        )
        
        validation_errors = []
        
        # Check if dependency type exists
        if dependency_type not in self.dependency_types:
            validation_errors.append(f"Invalid dependency type: {dependency_type}")
            return validation_errors
        
        type_info = self.dependency_types[dependency_type]
        
        # Validate lag if provided
        if lag is not None:
            if lag < 0 and not type_info.allows_negative_lag:
                validation_errors.append(f"Negative lag not allowed for dependency type: {dependency_type}")
        
        # Get tasks
        from_task = await self.repository.get_task_by_id(from_task_id)
        to_task = await self.repository.get_task_by_id(to_task_id)
        
        if not from_task or not to_task:
            # Task validation is handled elsewhere
            return validation_errors
        
        # Validate specific dependency types
        if dependency_type == DependencyType.BLOCKS:
            # Check if tasks are already in progress
            if from_task.status == "in_progress" and to_task.status == "in_progress":
                validation_errors.append("Cannot create BLOCKS dependency between tasks that are both in progress")
        
        return validation_errors
    
    async def calculate_task_dates(
        self,
        task_id: UUID,
        dependency_type: str,
        predecessor_id: UUID,
        lag: int = 0
    ) -> Dict[str, datetime]:
        """
        Calculate task dates based on dependency type and predecessor.
        
        Args:
            task_id: Task ID
            dependency_type: Dependency type
            predecessor_id: Predecessor task ID
            lag: Lag value in hours
            
        Returns:
            Dict[str, datetime]: Calculated dates (earliest_start, earliest_finish)
            
        Raises:
            InvalidDependencyError: If dependency type is invalid
        """
        await self._log_operation(
            "Calculating", 
            "task dates", 
            entity_name=f"for {task_id} based on {dependency_type} from {predecessor_id}"
        )
        
        # Check if dependency type exists
        if dependency_type not in self.dependency_types:
            raise InvalidDependencyError(
                message=f"Invalid dependency type: {dependency_type}",
                validation_errors=[f"Unknown dependency type: {dependency_type}"]
            )
        
        # Get tasks
        task = await self.repository.get_task_by_id(task_id)
        predecessor = await self.repository.get_task_by_id(predecessor_id)
        
        if not task or not predecessor:
            raise InvalidDependencyError(
                message="Task not found",
                validation_errors=["One or both tasks not found"]
            )
        
        # Get current schedule data
        task_schedule = await self.repository.get_task_schedule_data(task_id)
        predecessor_schedule = await self.repository.get_task_schedule_data(predecessor_id)
        
        # Default dates if no schedule data
        now = datetime.utcnow()
        pred_start = predecessor_schedule.get("earliest_start", now) if predecessor_schedule else now
        pred_finish = predecessor_schedule.get("earliest_finish", now + timedelta(hours=predecessor.estimated_duration)) if predecessor_schedule else now + timedelta(hours=predecessor.estimated_duration)
        
        # Calculate lag timedelta
        lag_delta = timedelta(hours=lag)
        
        # Calculate dates based on dependency type
        if dependency_type == DependencyType.FINISH_TO_START:
            earliest_start = pred_finish + lag_delta
            earliest_finish = earliest_start + timedelta(hours=task.estimated_duration)
        
        elif dependency_type == DependencyType.START_TO_START:
            earliest_start = pred_start + lag_delta
            earliest_finish = earliest_start + timedelta(hours=task.estimated_duration)
        
        elif dependency_type == DependencyType.FINISH_TO_FINISH:
            earliest_finish = pred_finish + lag_delta
            earliest_start = earliest_finish - timedelta(hours=task.estimated_duration)
        
        elif dependency_type == DependencyType.START_TO_FINISH:
            earliest_finish = pred_start + lag_delta
            earliest_start = earliest_finish - timedelta(hours=task.estimated_duration)
        
        else:
            # For other dependency types, don't change dates
            earliest_start = task_schedule.get("earliest_start", now) if task_schedule else now
            earliest_finish = task_schedule.get("earliest_finish", now + timedelta(hours=task.estimated_duration)) if task_schedule else now + timedelta(hours=task.estimated_duration)
        
        return {
            "earliest_start": earliest_start,
            "earliest_finish": earliest_finish
        }
    
    async def get_dependency_visualization_data(
        self,
        plan_id: UUID
    ) -> Dict[str, Any]:
        """
        Get visualization data for dependencies in a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        await self._log_operation("Getting", "dependency visualization data", entity_id=plan_id)
        
        # Get all dependencies for the plan
        dependencies = await self.repository.get_all_dependencies_for_plan(plan_id)
        
        # Get all tasks for the plan
        tasks = await self.repository.get_tasks_by_plan(plan_id)
        
        # Create nodes (tasks)
        nodes = []
        for task in tasks:
            nodes.append({
                "id": str(task.id),
                "name": task.name,
                "status": task.status,
                "duration": task.estimated_duration,
                "type": "task"
            })
        
        # Create edges (dependencies)
        edges = []
        for dependency in dependencies:
            # Get dependency type info
            type_info = self.dependency_types.get(dependency.dependency_type, None)
            style = type_info.visualization_style if type_info else "solid_arrow"
            
            edges.append({
                "id": str(dependency.id),
                "from": str(dependency.from_task_id),
                "to": str(dependency.to_task_id),
                "type": dependency.dependency_type,
                "lag": dependency.lag,
                "style": style
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    async def analyze_dependency_network(
        self,
        plan_id: UUID
    ) -> Dict[str, Any]:
        """
        Analyze the dependency network for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        await self._log_operation("Analyzing", "dependency network", entity_id=plan_id)
        
        # Get all dependencies for the plan
        dependencies = await self.repository.get_all_dependencies_for_plan(plan_id)
        
        # Get all tasks for the plan
        tasks = await self.repository.get_tasks_by_plan(plan_id)
        
        # Build adjacency list
        graph = {}
        for task in tasks:
            graph[task.id] = {
                "task": task,
                "outgoing": [],
                "incoming": []
            }
        
        for dependency in dependencies:
            if dependency.from_task_id in graph:
                graph[dependency.from_task_id]["outgoing"].append({
                    "to_task_id": dependency.to_task_id,
                    "type": dependency.dependency_type,
                    "lag": dependency.lag
                })
            
            if dependency.to_task_id in graph:
                graph[dependency.to_task_id]["incoming"].append({
                    "from_task_id": dependency.from_task_id,
                    "type": dependency.dependency_type,
                    "lag": dependency.lag
                })
        
        # Calculate metrics
        total_tasks = len(tasks)
        total_dependencies = len(dependencies)
        
        # Count dependency types
        dependency_type_counts = {}
        for dependency in dependencies:
            if dependency.dependency_type not in dependency_type_counts:
                dependency_type_counts[dependency.dependency_type] = 0
            dependency_type_counts[dependency.dependency_type] += 1
        
        # Find tasks with most dependencies
        tasks_with_most_outgoing = sorted(
            [(task_id, len(data["outgoing"])) for task_id, data in graph.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5
        
        tasks_with_most_incoming = sorted(
            [(task_id, len(data["incoming"])) for task_id, data in graph.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5
        
        # Format results
        top_outgoing = []
        for task_id, count in tasks_with_most_outgoing:
            if count > 0:
                task = graph[task_id]["task"]
                top_outgoing.append({
                    "id": str(task_id),
                    "name": task.name,
                    "dependency_count": count
                })
        
        top_incoming = []
        for task_id, count in tasks_with_most_incoming:
            if count > 0:
                task = graph[task_id]["task"]
                top_incoming.append({
                    "id": str(task_id),
                    "name": task.name,
                    "dependency_count": count
                })
        
        # Calculate network density
        max_possible_dependencies = total_tasks * (total_tasks - 1)
        network_density = total_dependencies / max_possible_dependencies if max_possible_dependencies > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "total_dependencies": total_dependencies,
            "dependency_type_distribution": dependency_type_counts,
            "tasks_with_most_outgoing_dependencies": top_outgoing,
            "tasks_with_most_incoming_dependencies": top_incoming,
            "network_density": network_density,
            "average_dependencies_per_task": total_dependencies / total_tasks if total_tasks > 0 else 0
        }
