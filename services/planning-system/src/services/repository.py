"""
Planning System Repository implementation.

This module provides the data access layer for the Planning System service,
encapsulating database operations and queries.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union, cast
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from ..models.internal import (
    Base,
    StrategicPlanModel,
    PlanPhaseModel,
    PlanMilestoneModel,
    PlanningTaskModel,
    ResourceModel,
    ResourceAllocationModel,
    TimelineForecastModel,
    BottleneckAnalysisModel,
    OptimizationResultModel,
    PlanHistoryModel,
    task_dependencies
)

from ..models.api import (
    PlanStatus,
    TaskStatus,
    DependencyType
)

from ..exceptions import (
    PlanNotFoundError,
    TaskNotFoundError,
    InvalidDependencyError,
    ResourceNotFoundError,
    ResourceAllocationError
)

logger = logging.getLogger(__name__)

class PlanningRepository:
    """
    Repository for Planning System database operations.
    
    This class encapsulates database access for the Planning System service,
    providing methods for CRUD operations on planning entities.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            db: Database session
        """
        self.db = db
        logger.debug("Planning Repository initialized")
    
    # Plan operations
    
    async def create_plan(self, plan_data: Dict[str, Any]) -> StrategicPlanModel:
        """
        Create a new strategic plan.
        
        Args:
            plan_data: Plan data
            
        Returns:
            StrategicPlanModel: Created plan
        """
        logger.debug(f"Creating plan: {plan_data.get('name')}")
        
        # Create plan
        plan = StrategicPlanModel(**plan_data)
        self.db.add(plan)
        await self.db.flush()
        
        # Create plan history entry
        history_entry = PlanHistoryModel(
            plan_id=plan.id,
            timestamp=datetime.utcnow(),
            previous_state=None,
            new_state={
                "id": str(plan.id),
                "name": plan.name,
                "status": plan.status.value,
                "project_id": str(plan.project_id),
                "created_at": plan.created_at.isoformat(),
            },
            change_type="created",
            change_reason="Plan created"
        )
        self.db.add(history_entry)
        await self.db.flush()
        
        await self.db.refresh(plan)
        return plan
    
    async def get_plan_by_id(self, plan_id: UUID) -> Optional[StrategicPlanModel]:
        """
        Get a strategic plan by ID.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Optional[StrategicPlanModel]: Plan if found, None otherwise
        """
        logger.debug(f"Getting plan: {plan_id}")
        
        query = (
            select(StrategicPlanModel)
            .options(
                selectinload(StrategicPlanModel.phases),
                selectinload(StrategicPlanModel.milestones),
            )
            .where(StrategicPlanModel.id == plan_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_plans(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[StrategicPlanModel], int]:
        """
        List strategic plans with filtering and pagination.
        
        Args:
            filters: Filters to apply
            pagination: Pagination parameters
            
        Returns:
            Tuple[List[StrategicPlanModel], int]: List of plans and total count
        """
        logger.debug(f"Listing plans: {filters}")
        
        # Build query
        query = select(StrategicPlanModel)
        
        # Apply filters
        if "project_id" in filters and filters["project_id"]:
            query = query.where(StrategicPlanModel.project_id == filters["project_id"])
        
        if "status" in filters and filters["status"]:
            query = query.where(StrategicPlanModel.status == filters["status"])
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)
        offset = (page - 1) * page_size
        
        query = query.order_by(StrategicPlanModel.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        plans = result.scalars().all()
        
        return plans, total
    
    async def update_plan(
        self,
        plan_id: UUID,
        plan_data: Dict[str, Any]
    ) -> Optional[StrategicPlanModel]:
        """
        Update a strategic plan.
        
        Args:
            plan_id: Plan ID
            plan_data: Plan data to update
            
        Returns:
            Optional[StrategicPlanModel]: Updated plan if found, None otherwise
        """
        logger.debug(f"Updating plan: {plan_id}")
        
        # Get current plan
        plan = await self.get_plan_by_id(plan_id)
        if not plan:
            return None
        
        # Store previous state for history
        previous_state = {
            "id": str(plan.id),
            "name": plan.name,
            "status": plan.status.value,
            "description": plan.description,
            "constraints": plan.constraints,
            "objectives": plan.objectives,
            "updated_at": plan.updated_at.isoformat()
        }
        
        # Update plan
        for key, value in plan_data.items():
            if hasattr(plan, key) and value is not None:
                setattr(plan, key, value)
        
        # Set updated_at timestamp
        plan.updated_at = datetime.utcnow()
        
        # Create plan history entry
        new_state = {
            "id": str(plan.id),
            "name": plan.name,
            "status": plan.status.value,
            "description": plan.description,
            "constraints": plan.constraints,
            "objectives": plan.objectives,
            "updated_at": plan.updated_at.isoformat()
        }
        
        history_entry = PlanHistoryModel(
            plan_id=plan.id,
            timestamp=datetime.utcnow(),
            previous_state=previous_state,
            new_state=new_state,
            change_type="updated",
            change_reason="Plan updated"
        )
        self.db.add(history_entry)
        
        await self.db.flush()
        await self.db.refresh(plan)
        
        return plan
    
    async def delete_plan(self, plan_id: UUID) -> bool:
        """
        Delete a strategic plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        logger.debug(f"Deleting plan: {plan_id}")
        
        # Get plan to verify it exists
        plan = await self.get_plan_by_id(plan_id)
        if not plan:
            return False
        
        # Delete plan
        await self.db.execute(
            delete(StrategicPlanModel).where(StrategicPlanModel.id == plan_id)
        )
        
        return True
    
    async def get_plan_history(
        self,
        plan_id: UUID,
        limit: int = 10
    ) -> List[PlanHistoryModel]:
        """
        Get history of changes to a strategic plan.
        
        Args:
            plan_id: Plan ID
            limit: Maximum number of history entries
            
        Returns:
            List[PlanHistoryModel]: Plan history entries
        """
        logger.debug(f"Getting history for plan: {plan_id}")
        
        query = (
            select(PlanHistoryModel)
            .where(PlanHistoryModel.plan_id == plan_id)
            .order_by(PlanHistoryModel.timestamp.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # Task operations
    
    async def create_task(self, task_data: Dict[str, Any]) -> PlanningTaskModel:
        """
        Create a new planning task.
        
        Args:
            task_data: Task data
            
        Returns:
            PlanningTaskModel: Created task
        """
        logger.debug(f"Creating task: {task_data.get('name')}")
        
        # Create task
        task = PlanningTaskModel(**task_data)
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        
        return task
    
    async def get_task_by_id(self, task_id: UUID) -> Optional[PlanningTaskModel]:
        """
        Get a planning task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Optional[PlanningTaskModel]: Task if found, None otherwise
        """
        logger.debug(f"Getting task: {task_id}")
        
        query = (
            select(PlanningTaskModel)
            .options(
                selectinload(PlanningTaskModel.plan),
                selectinload(PlanningTaskModel.phase),
                selectinload(PlanningTaskModel.milestone),
                selectinload(PlanningTaskModel.dependencies),
                selectinload(PlanningTaskModel.dependent_tasks),
                selectinload(PlanningTaskModel.resource_allocations),
            )
            .where(PlanningTaskModel.id == task_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_tasks(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[PlanningTaskModel], int]:
        """
        List planning tasks with filtering and pagination.
        
        Args:
            filters: Filters to apply
            pagination: Pagination parameters
            
        Returns:
            Tuple[List[PlanningTaskModel], int]: List of tasks and total count
        """
        logger.debug(f"Listing tasks: {filters}")
        
        # Build query
        query = select(PlanningTaskModel)
        
        # Apply filters
        if "plan_id" in filters and filters["plan_id"]:
            query = query.where(PlanningTaskModel.plan_id == filters["plan_id"])
        
        if "phase_id" in filters and filters["phase_id"]:
            query = query.where(PlanningTaskModel.phase_id == filters["phase_id"])
        
        if "milestone_id" in filters and filters["milestone_id"]:
            query = query.where(PlanningTaskModel.milestone_id == filters["milestone_id"])
        
        if "status" in filters and filters["status"]:
            query = query.where(PlanningTaskModel.status == filters["status"])
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)
        offset = (page - 1) * page_size
        
        query = query.order_by(PlanningTaskModel.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return tasks, total
    
    async def update_task(
        self,
        task_id: UUID,
        task_data: Dict[str, Any]
    ) -> Optional[PlanningTaskModel]:
        """
        Update a planning task.
        
        Args:
            task_id: Task ID
            task_data: Task data to update
            
        Returns:
            Optional[PlanningTaskModel]: Updated task if found, None otherwise
        """
        logger.debug(f"Updating task: {task_id}")
        
        # Get current task
        task = await self.get_task_by_id(task_id)
        if not task:
            return None
        
        # Update task
        for key, value in task_data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        
        # Set updated_at timestamp
        task.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(task)
        
        return task
    
    async def delete_task(self, task_id: UUID) -> bool:
        """
        Delete a planning task.
        
        Args:
            task_id: Task ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        logger.debug(f"Deleting task: {task_id}")
        
        # Get task to verify it exists
        task = await self.get_task_by_id(task_id)
        if not task:
            return False
        
        # Delete task
        await self.db.execute(
            delete(PlanningTaskModel).where(PlanningTaskModel.id == task_id)
        )
        
        return True
    
    # Dependency operations
    
    async def create_dependency(
        self,
        from_task_id: UUID,
        to_task_id: UUID,
        dependency_type: DependencyType,
        lag: float
    ) -> Dict[str, Any]:
        """
        Create a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            dependency_type: Type of dependency
            lag: Lag time in hours
            
        Returns:
            Dict[str, Any]: Created dependency
            
        Raises:
            TaskNotFoundError: If task not found
            InvalidDependencyError: If dependency is invalid
        """
        logger.debug(f"Creating dependency from {from_task_id} to {to_task_id}")
        
        # Check tasks exist
        from_task = await self.get_task_by_id(from_task_id)
        if not from_task:
            raise TaskNotFoundError(str(from_task_id))
        
        to_task = await self.get_task_by_id(to_task_id)
        if not to_task:
            raise TaskNotFoundError(str(to_task_id))
        
        # Check for existing dependency
        query = (
            select(task_dependencies)
            .where(
                task_dependency.c.from_task_id == from_task_id,
                task_dependency.c.to_task_id == to_task_id
            )
        )
        result = await self.db.execute(query)
        if result.first():
            raise InvalidDependencyError(f"Dependency from {from_task_id} to {to_task_id} already exists")
        
        # Create dependency
        stmt = insert(task_dependencies).values(
            from_task_id=from_task_id,
            to_task_id=to_task_id,
            dependency_type=dependency_type.value,
            lag=lag,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await self.db.execute(stmt)
        
        # Return created dependency
        dependency = {
            "from_task_id": from_task_id,
            "to_task_id": to_task_id,
            "from_task_name": from_task.name,
            "to_task_name": to_task.name,
            "dependency_type": dependency_type,
            "lag": lag,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "critical": False,  # Default value
        }
        
        return dependency
    
    async def get_dependency(
        self,
        from_task_id: UUID,
        to_task_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Returns:
            Optional[Dict[str, Any]]: Dependency if found, None otherwise
        """
        logger.debug(f"Getting dependency from {from_task_id} to {to_task_id}")
        
        # Query dependency
        query = (
            select(
                task_dependency.c.from_task_id,
                task_dependency.c.to_task_id,
                task_dependency.c.dependency_type,
                task_dependency.c.lag,
                task_dependency.c.created_at,
                task_dependency.c.updated_at,
                PlanningTaskModel.name.label("from_task_name"),
                PlanningTaskModel.name.label("to_task_name"),
            )
            .select_from(
                task_dependencies
                .join(
                    PlanningTaskModel,
                    task_dependency.c.from_task_id == PlanningTaskModel.id
                )
                .join(
                    PlanningTaskModel,
                    task_dependency.c.to_task_id == PlanningTaskModel.id,
                    isouter=True
                )
            )
            .where(
                task_dependency.c.from_task_id == from_task_id,
                task_dependency.c.to_task_id == to_task_id
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        # Convert to dictionary
        dependency = {
            "from_task_id": row.from_task_id,
            "to_task_id": row.to_task_id,
            "from_task_name": row.from_task_name,
            "to_task_name": row.to_task_name,
            "dependency_type": DependencyType(row.dependency_type),
            "lag": row.lag,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "critical": False,  # Default value
        }
        
        return dependency
    
    async def update_dependency(
        self,
        from_task_id: UUID,
        to_task_id: UUID,
        dependency_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            dependency_data: Dependency data to update
            
        Returns:
            Optional[Dict[str, Any]]: Updated dependency if found, None otherwise
        """
        logger.debug(f"Updating dependency from {from_task_id} to {to_task_id}")
        
        # Check dependency exists
        dependency = await self.get_dependency(from_task_id, to_task_id)
        if not dependency:
            return None
        
        # Prepare update data
        update_data = {"updated_at": datetime.utcnow()}
        
        if "dependency_type" in dependency_data and dependency_data["dependency_type"] is not None:
            update_data["dependency_type"] = dependency_data["dependency_type"].value
        
        if "lag" in dependency_data and dependency_data["lag"] is not None:
            update_data["lag"] = dependency_data["lag"]
        
        # Update dependency
        stmt = (
            update(task_dependencies)
            .where(
                task_dependency.c.from_task_id == from_task_id,
                task_dependency.c.to_task_id == to_task_id
            )
            .values(**update_data)
        )
        await self.db.execute(stmt)
        
        # Return updated dependency
        updated_dependency = await self.get_dependency(from_task_id, to_task_id)
        return updated_dependency
    
    async def delete_dependency(self, from_task_id: UUID, to_task_id: UUID) -> bool:
        """
        Delete a task dependency.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        logger.debug(f"Deleting dependency from {from_task_id} to {to_task_id}")
        
        # Check dependency exists
        dependency = await self.get_dependency(from_task_id, to_task_id)
        if not dependency:
            return False
        
        # Delete dependency
        stmt = (
            delete(task_dependencies)
            .where(
                task_dependency.c.from_task_id == from_task_id,
                task_dependency.c.to_task_id == to_task_id
            )
        )
        await self.db.execute(stmt)
        
        return True
    
    # Forecasting operations
    
    async def create_forecast(
        self,
        forecast_data: Dict[str, Any]
    ) -> TimelineForecastModel:
        """
        Create a timeline forecast.
        
        Args:
            forecast_data: Forecast data
            
        Returns:
            TimelineForecastModel: Created forecast
        """
        logger.debug(f"Creating forecast for plan: {forecast_data.get('plan_id')}")
        
        # Create forecast
        forecast = TimelineForecastModel(**forecast_data)
        self.db.add(forecast)
        await self.db.flush()
        await self.db.refresh(forecast)
        
        return forecast
    
    async def get_latest_forecast(self, plan_id: UUID) -> Optional[TimelineForecastModel]:
        """
        Get the latest forecast for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Optional[TimelineForecastModel]: Latest forecast if found, None otherwise
        """
        logger.debug(f"Getting latest forecast for plan: {plan_id}")
        
        query = (
            select(TimelineForecastModel)
            .where(TimelineForecastModel.plan_id == plan_id)
            .order_by(TimelineForecastModel.generated_at.desc())
            .limit(1)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    # Bottleneck operations
    
    async def create_bottleneck_analysis(
        self,
        analysis_data: Dict[str, Any]
    ) -> BottleneckAnalysisModel:
        """
        Create a bottleneck analysis.
        
        Args:
            analysis_data: Analysis data
            
        Returns:
            BottleneckAnalysisModel: Created analysis
        """
        logger.debug(f"Creating bottleneck analysis for plan: {analysis_data.get('plan_id')}")
        
        # Create analysis
        analysis = BottleneckAnalysisModel(**analysis_data)
        self.db.add(analysis)
        await self.db.flush()
        await self.db.refresh(analysis)
        
        return analysis
    
    async def get_latest_bottleneck_analysis(self, plan_id: UUID) -> Optional[BottleneckAnalysisModel]:
        """
        Get the latest bottleneck analysis for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Optional[BottleneckAnalysisModel]: Latest analysis if found, None otherwise
        """
        logger.debug(f"Getting latest bottleneck analysis for plan: {plan_id}")
        
        query = (
            select(BottleneckAnalysisModel)
            .where(BottleneckAnalysisModel.plan_id == plan_id)
            .order_by(BottleneckAnalysisModel.generated_at.desc())
            .limit(1)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    # Resource operations
    
    async def create_resource(self, resource_data: Dict[str, Any]) -> ResourceModel:
        """
        Create a new resource.
        
        Args:
            resource_data: Resource data
            
        Returns:
            ResourceModel: Created resource
        """
        logger.debug(f"Creating resource: {resource_data.get('name')}")
        
        # Create resource
        resource = ResourceModel(**resource_data)
        self.db.add(resource)
        await self.db.flush()
        await self.db.refresh(resource)
        
        return resource
    
    async def get_resource_by_id(self, resource_id: UUID) -> Optional[ResourceModel]:
        """
        Get a resource by ID.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            Optional[ResourceModel]: Resource if found, None otherwise
        """
        logger.debug(f"Getting resource: {resource_id}")
        
        query = (
            select(ResourceModel)
            .where(ResourceModel.id == resource_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_resources(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[ResourceModel], int]:
        """
        List resources with filtering and pagination.
        
        Args:
            filters: Filters to apply
            pagination: Pagination parameters
            
        Returns:
            Tuple[List[ResourceModel], int]: List of resources and total count
        """
        logger.debug(f"Listing resources: {filters}")
        
        # Build query
        query = select(ResourceModel)
        
        # Apply filters
        if "resource_type" in filters and filters["resource_type"]:
            query = query.where(ResourceModel.resource_type == filters["resource_type"])
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)
        offset = (page - 1) * page_size
        
        query = query.order_by(ResourceModel.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        resources = result.scalars().all()
        
        return resources, total
    
    async def update_resource(
        self,
        resource_id: UUID,
        resource_data: Dict[str, Any]
    ) -> Optional[ResourceModel]:
        """
        Update a resource.
        
        Args:
            resource_id: Resource ID
            resource_data: Resource data to update
            
        Returns:
            Optional[ResourceModel]: Updated resource if found, None otherwise
        """
        logger.debug(f"Updating resource: {resource_id}")
        
        # Get current resource
        resource = await self.get_resource_by_id(resource_id)
        if not resource:
            return None
        
        # Update resource
        for key, value in resource_data.items():
            if hasattr(resource, key) and value is not None:
                setattr(resource, key, value)
        
        # Set updated_at timestamp
        resource.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(resource)
        
        return resource
    
    async def delete_resource(self, resource_id: UUID) -> bool:
        """
        Delete a resource.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        logger.debug(f"Deleting resource: {resource_id}")
        
        # Get resource to verify it exists
        resource = await self.get_resource_by_id(resource_id)
        if not resource:
            return False
        
        # Delete resource
        await self.db.execute(
            delete(ResourceModel).where(ResourceModel.id == resource_id)
        )
        
        return True
    
    async def get_resources_for_plan(
        self,
        plan_id: UUID,
        resource_type: Optional[str] = None
    ) -> List[ResourceModel]:
        """
        Get resources allocated to a plan.
        
        Args:
            plan_id: Plan ID
            resource_type: Optional resource type filter
            
        Returns:
            List[ResourceModel]: Resources allocated to the plan
        """
        logger.debug(f"Getting resources for plan: {plan_id}")
        
        # Get tasks for the plan
        tasks = await self.get_tasks_by_plan(plan_id)
        task_ids = [task.id for task in tasks]
        
        if not task_ids:
            return []
        
        # Get allocations for the tasks
        query = (
            select(ResourceAllocationModel)
            .where(ResourceAllocationModel.task_id.in_(task_ids))
        )
        
        result = await self.db.execute(query)
        allocations = result.scalars().all()
        
        if not allocations:
            return []
        
        # Get resources for the allocations
        resource_ids = [allocation.resource_id for allocation in allocations]
        
        query = (
            select(ResourceModel)
            .where(ResourceModel.id.in_(resource_ids))
        )
        
        if resource_type:
            query = query.where(ResourceModel.resource_type == resource_type)
        
        result = await self.db.execute(query)
        resources = result.scalars().all()
        
        return resources
    
    # Resource allocation operations
    
    async def create_resource_allocation(
        self,
        allocation_data: Dict[str, Any]
    ) -> ResourceAllocationModel:
        """
        Create a new resource allocation.
        
        Args:
            allocation_data: Allocation data
            
        Returns:
            ResourceAllocationModel: Created allocation
        """
        logger.debug(f"Creating resource allocation: {allocation_data}")
        
        # Create allocation
        allocation = ResourceAllocationModel(**allocation_data)
        self.db.add(allocation)
        await self.db.flush()
        await self.db.refresh(allocation)
        
        return allocation
    
    async def get_resource_allocation_by_id(
        self,
        allocation_id: UUID
    ) -> Optional[ResourceAllocationModel]:
        """
        Get a resource allocation by ID.
        
        Args:
            allocation_id: Allocation ID
            
        Returns:
            Optional[ResourceAllocationModel]: Allocation if found, None otherwise
        """
        logger.debug(f"Getting resource allocation: {allocation_id}")
        
        query = (
            select(ResourceAllocationModel)
            .where(ResourceAllocationModel.id == allocation_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_resource_allocations(
        self,
        filters: Dict[str, Any],
        pagination: Dict[str, int]
    ) -> Tuple[List[ResourceAllocationModel], int]:
        """
        List resource allocations with filtering and pagination.
        
        Args:
            filters: Filters to apply
            pagination: Pagination parameters
            
        Returns:
            Tuple[List[ResourceAllocationModel], int]: List of allocations and total count
        """
        logger.debug(f"Listing resource allocations: {filters}")
        
        # Build query
        query = select(ResourceAllocationModel)
        
        # Apply filters
        if "task_id" in filters and filters["task_id"]:
            query = query.where(ResourceAllocationModel.task_id == filters["task_id"])
        
        if "resource_id" in filters and filters["resource_id"]:
            query = query.where(ResourceAllocationModel.resource_id == filters["resource_id"])
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0
        
        # Apply pagination
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)
        offset = (page - 1) * page_size
        
        query = query.order_by(ResourceAllocationModel.created_at.desc())
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        allocations = result.scalars().all()
        
        return allocations, total
    
    async def update_resource_allocation(
        self,
        allocation_id: UUID,
        allocation_data: Dict[str, Any]
    ) -> Optional[ResourceAllocationModel]:
        """
        Update a resource allocation.
        
        Args:
            allocation_id: Allocation ID
            allocation_data: Allocation data to update
            
        Returns:
            Optional[ResourceAllocationModel]: Updated allocation if found, None otherwise
        """
        logger.debug(f"Updating resource allocation: {allocation_id}")
        
        # Get current allocation
        allocation = await self.get_resource_allocation_by_id(allocation_id)
        if not allocation:
            return None
        
        # Update allocation
        for key, value in allocation_data.items():
            if hasattr(allocation, key) and value is not None:
                setattr(allocation, key, value)
        
        # Set updated_at timestamp
        allocation.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(allocation)
        
        return allocation
    
    async def delete_resource_allocation(self, allocation_id: UUID) -> bool:
        """
        Delete a resource allocation.
        
        Args:
            allocation_id: Allocation ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        logger.debug(f"Deleting resource allocation: {allocation_id}")
        
        # Get allocation to verify it exists
        allocation = await self.get_resource_allocation_by_id(allocation_id)
        if not allocation:
            return False
        
        # Delete allocation
        await self.db.execute(
            delete(ResourceAllocationModel).where(ResourceAllocationModel.id == allocation_id)
        )
        
        return True
    
    async def get_resource_allocations_by_resource(
        self,
        resource_id: UUID
    ) -> List[ResourceAllocationModel]:
        """
        Get allocations for a resource.
        
        Args:
            resource_id: Resource ID
            
        Returns:
            List[ResourceAllocationModel]: Allocations for the resource
        """
        logger.debug(f"Getting allocations for resource: {resource_id}")
        
        query = (
            select(ResourceAllocationModel)
            .where(ResourceAllocationModel.resource_id == resource_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_resource_allocations_by_task(
        self,
        task_id: UUID
    ) -> List[ResourceAllocationModel]:
        """
        Get allocations for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List[ResourceAllocationModel]: Allocations for the task
        """
        logger.debug(f"Getting allocations for task: {task_id}")
        
        query = (
            select(ResourceAllocationModel)
            .where(ResourceAllocationModel.task_id == task_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_resource_allocations_for_plan(
        self,
        plan_id: UUID
    ) -> List[ResourceAllocationModel]:
        """
        Get allocations for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List[ResourceAllocationModel]: Allocations for the plan
        """
        logger.debug(f"Getting allocations for plan: {plan_id}")
        
        # Get tasks for the plan
        tasks = await self.get_tasks_by_plan(plan_id)
        task_ids = [task.id for task in tasks]
        
        if not task_ids:
            return []
        
        # Get allocations for the tasks
        query = (
            select(ResourceAllocationModel)
            .where(ResourceAllocationModel.task_id.in_(task_ids))
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_resource_allocations_for_resource(
        self,
        resource_id: UUID,
        plan_id: Optional[UUID] = None
    ) -> int:
        """
        Delete allocations for a resource.
        
        Args:
            resource_id: Resource ID
            plan_id: Optional plan ID to limit deletion to a specific plan
            
        Returns:
            int: Number of allocations deleted
        """
        logger.debug(f"Deleting allocations for resource: {resource_id}")
        
        if plan_id:
            # Get tasks for the plan
            tasks = await self.get_tasks_by_plan(plan_id)
            task_ids = [task.id for task in tasks]
            
            if not task_ids:
                return 0
            
            # Delete allocations for the resource and tasks
            stmt = (
                delete(ResourceAllocationModel)
                .where(
                    ResourceAllocationModel.resource_id == resource_id,
                    ResourceAllocationModel.task_id.in_(task_ids)
                )
            )
        else:
            # Delete all allocations for the resource
            stmt = (
                delete(ResourceAllocationModel)
                .where(ResourceAllocationModel.resource_id == resource_id)
            )
        
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def get_tasks_by_plan(self, plan_id: UUID) -> List[PlanningTaskModel]:
        """
        Get tasks for a plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List[PlanningTaskModel]: Tasks for the plan
        """
        logger.debug(f"Getting tasks for plan: {plan_id}")
        
        query = (
            select(PlanningTaskModel)
            .where(PlanningTaskModel.plan_id == plan_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    # Optimization operations
    
    async def create_optimization_result(
        self,
        result_data: Dict[str, Any]
    ) -> OptimizationResultModel:
        """
        Create an optimization result.
        
        Args:
            result_data: Result data
            
        Returns:
            OptimizationResultModel: Created result
        """
        logger.debug(f"Creating optimization result for plan: {result_data.get('plan_id')}")
        
        # Create result
        result = OptimizationResultModel(**result_data)
        self.db.add(result)
        await self.db.flush()
        await self.db.refresh(result)
        
        return result
    
    async def get_optimization_result(self, optimization_id: UUID) -> Optional[OptimizationResultModel]:
        """
        Get an optimization result by ID.
        
        Args:
            optimization_id: Optimization result ID
            
        Returns:
            Optional[OptimizationResultModel]: Result if found, None otherwise
        """
        logger.debug(f"Getting optimization result: {optimization_id}")
        
        query = (
            select(OptimizationResultModel)
            .where(OptimizationResultModel.id == optimization_id)
        )
        
        result = await self.db.execute(query)
        return result.scalars().first()
    
    # Utility methods for loading related entities
    
    async def load_plans_with_related(
        self,
        plans: List[StrategicPlanModel]
    ) -> List[StrategicPlanModel]:
        """
        Load related entities for plans.
        
        Args:
            plans: List of plans
            
        Returns:
            List[StrategicPlanModel]: Plans with related entities loaded
        """
        # Load phases and milestones
        for plan in plans:
            await self.db.refresh(
                plan,
                attributes=["phases", "milestones"],
            )
        
        return plans
