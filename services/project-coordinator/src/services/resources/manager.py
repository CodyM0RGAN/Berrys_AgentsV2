"""
Resource Manager for Project Coordinator service.

This module provides resource allocation and optimization functionality for projects.
"""
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime
import heapq

from ...repositories.project import ProjectRepository
from ...exceptions import ResourceAllocationError, ProjectNotFoundError
from ...models.api import OptimizationTarget, ResourceType
from ...config import Settings


class ResourceOptimizer:
    """
    Resource optimizer implementation using factory pattern for different optimization strategies.
    """
    
    @staticmethod
    def create_optimizer(target: OptimizationTarget):
        """
        Factory method to create the appropriate optimizer based on target.
        
        Args:
            target: Optimization target
            
        Returns:
            Optimizer function
        """
        if target == OptimizationTarget.TIME:
            return ResourceOptimizer.optimize_for_time
        elif target == OptimizationTarget.COST:
            return ResourceOptimizer.optimize_for_cost
        elif target == OptimizationTarget.QUALITY:
            return ResourceOptimizer.optimize_for_quality
        else:  # BALANCED
            return ResourceOptimizer.optimize_for_balance
    
    @staticmethod
    def optimize_for_time(
        resources: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Optimize resources prioritizing time efficiency.
        
        Args:
            resources: List of resources
            constraints: Optional constraints
            
        Returns:
            Tuple of (optimized resources, optimization score)
        """
        # For time optimization, prioritize higher resource allocation
        constraints = constraints or {}
        max_total_allocation = constraints.get("max_total_allocation", 10.0)  # Default to 10.0 (1000%)
        
        # Sort resources by their impact on time
        sorted_resources = sorted(
            resources,
            key=lambda r: ResourceOptimizer._get_time_impact(r),
            reverse=True  # Higher impact first
        )
        
        # Allocate more to high-impact resources while respecting constraints
        optimized = ResourceOptimizer._allocate_with_constraint(
            sorted_resources,
            max_total_allocation,
            lambda r: ResourceOptimizer._get_time_impact(r)
        )
        
        # Calculate optimization score (higher is better)
        score = sum(r["allocation"] * ResourceOptimizer._get_time_impact(r) for r in optimized) / len(optimized) if optimized else 0.0
        
        return optimized, score
    
    @staticmethod
    def optimize_for_cost(
        resources: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Optimize resources prioritizing cost efficiency.
        
        Args:
            resources: List of resources
            constraints: Optional constraints
            
        Returns:
            Tuple of (optimized resources, optimization score)
        """
        # For cost optimization, prioritize resources with lower cost
        constraints = constraints or {}
        min_total_allocation = constraints.get("min_total_allocation", 1.0)  # Minimum 100%
        
        # Sort resources by cost efficiency (lower cost first)
        sorted_resources = sorted(
            resources,
            key=lambda r: ResourceOptimizer._get_cost(r)
        )
        
        # Allocate more to low-cost resources while ensuring minimum allocation
        optimized = []
        total_allocation = 0.0
        
        for resource in sorted_resources:
            # Preserve original allocation if it's low-cost, otherwise minimize
            cost = ResourceOptimizer._get_cost(resource)
            is_low_cost = cost < 0.5  # Threshold for "low cost"
            
            if is_low_cost:
                # Allocate more to low-cost resources
                new_allocation = min(1.0, resource["allocation"] * 1.5)
            else:
                # Allocate less to high-cost resources, but ensure minimum
                new_allocation = max(0.1, resource["allocation"] * 0.7)
            
            total_allocation += new_allocation
            
            optimized.append({
                **resource,
                "allocation": new_allocation
            })
        
        # Ensure minimum allocation
        if total_allocation < min_total_allocation:
            scaling_factor = min_total_allocation / total_allocation
            for r in optimized:
                r["allocation"] = min(1.0, r["allocation"] * scaling_factor)
        
        # Calculate optimization score (inverse of weighted cost)
        total_cost = sum(r["allocation"] * ResourceOptimizer._get_cost(r) for r in optimized)
        score = 1.0 / (total_cost or 1.0)  # Avoid division by zero
        
        return optimized, score
    
    @staticmethod
    def optimize_for_quality(
        resources: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Optimize resources prioritizing quality.
        
        Args:
            resources: List of resources
            constraints: Optional constraints
            
        Returns:
            Tuple of (optimized resources, optimization score)
        """
        # For quality optimization, prioritize high-quality resources
        constraints = constraints or {}
        max_total_allocation = constraints.get("max_total_allocation", 10.0)
        
        # Sort resources by quality (higher quality first)
        sorted_resources = sorted(
            resources,
            key=lambda r: ResourceOptimizer._get_quality(r),
            reverse=True
        )
        
        # Allocate more to high-quality resources
        optimized = ResourceOptimizer._allocate_with_constraint(
            sorted_resources,
            max_total_allocation,
            lambda r: ResourceOptimizer._get_quality(r)
        )
        
        # Calculate optimization score (higher is better)
        score = sum(r["allocation"] * ResourceOptimizer._get_quality(r) for r in optimized) / len(optimized) if optimized else 0.0
        
        return optimized, score
    
    @staticmethod
    def optimize_for_balance(
        resources: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Optimize resources for a balanced approach.
        
        Args:
            resources: List of resources
            constraints: Optional constraints
            
        Returns:
            Tuple of (optimized resources, optimization score)
        """
        # For balanced optimization, consider time, cost, and quality
        constraints = constraints or {}
        max_total_allocation = constraints.get("max_total_allocation", 5.0)  # More conservative
        
        # Calculate a balanced score for each resource
        for resource in resources:
            quality = ResourceOptimizer._get_quality(resource)
            time_impact = ResourceOptimizer._get_time_impact(resource)
            cost = ResourceOptimizer._get_cost(resource)
            
            # Balance score: higher quality, higher time impact, lower cost
            balanced_score = (quality + time_impact) / (cost + 0.1)  # Avoid division by zero
            resource["balanced_score"] = balanced_score
        
        # Sort by balanced score
        sorted_resources = sorted(
            resources,
            key=lambda r: r["balanced_score"],
            reverse=True  # Higher score first
        )
        
        # Allocate resources based on balanced score
        optimized = ResourceOptimizer._allocate_with_constraint(
            sorted_resources,
            max_total_allocation,
            lambda r: r["balanced_score"]
        )
        
        # Remove temporary score field and calculate optimization score
        for resource in optimized:
            balanced_score = resource.pop("balanced_score", 0.0)
        
        # Calculate average allocation weighted by balanced score
        weighted_allocations = [r["allocation"] * r.get("balanced_score", 0.0) for r in sorted_resources]
        score = sum(weighted_allocations) / len(weighted_allocations) if weighted_allocations else 0.0
        
        return optimized, score
    
    @staticmethod
    def _allocate_with_constraint(
        sorted_resources: List[Dict[str, Any]],
        max_total_allocation: float,
        score_func
    ) -> List[Dict[str, Any]]:
        """
        Allocate resources based on a scoring function while respecting a maximum total allocation.
        
        Args:
            sorted_resources: List of resources sorted by priority
            max_total_allocation: Maximum total allocation allowed
            score_func: Function to calculate score for a resource
            
        Returns:
            List of optimized resources
        """
        total_allocation = 0.0
        optimized = []
        
        # First pass: allocate proportionally to scores
        total_score = sum(score_func(r) for r in sorted_resources) or 1.0  # Avoid division by zero
        
        for resource in sorted_resources:
            score = score_func(resource)
            proportion = score / total_score if total_score > 0 else 0.0
            
            # Allocate proportionally, but no more than 100% per resource
            new_allocation = min(1.0, max_total_allocation * proportion)
            
            optimized.append({
                **resource,
                "allocation": new_allocation
            })
            
            total_allocation += new_allocation
        
        # Second pass: if we're over budget, reduce allocations
        if total_allocation > max_total_allocation:
            scaling_factor = max_total_allocation / total_allocation
            for r in optimized:
                r["allocation"] *= scaling_factor
        
        return optimized
    
    @staticmethod
    def _get_quality(resource: Dict[str, Any]) -> float:
        """Get quality score for a resource."""
        metadata = resource.get("metadata", {})
        return metadata.get("quality_score", 0.5)
    
    @staticmethod
    def _get_time_impact(resource: Dict[str, Any]) -> float:
        """Get time impact score for a resource."""
        metadata = resource.get("metadata", {})
        return metadata.get("time_impact", 0.5)
    
    @staticmethod
    def _get_cost(resource: Dict[str, Any]) -> float:
        """Get cost score for a resource."""
        metadata = resource.get("metadata", {})
        return metadata.get("cost", 0.5)


class ResourceManager:
    """
    Resource Manager service.
    
    This service manages project resource allocation and optimization.
    
    Attributes:
        project_repo: Project repository
        settings: Application settings
        logger: Logger instance
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Resource Manager.
        
        Args:
            project_repo: Project repository
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.settings = settings
        self.logger = logger or logging.getLogger("resource_manager")
    
    def allocate_resource(
        self, 
        project_id: UUID, 
        resource_type: ResourceType,
        resource_id: str,
        allocation: float,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Allocate a resource to a project.
        
        Args:
            project_id: Project ID
            resource_type: Resource type
            resource_id: Resource ID
            allocation: Allocation percentage (0.0-1.0)
            start_date: Optional start date
            end_date: Optional end date
            metadata: Additional metadata
            
        Returns:
            Allocated resource
            
        Raises:
            ProjectNotFoundError: If project not found
            ResourceAllocationError: If resource allocation fails
        """
        self.logger.info(
            f"Allocating {resource_type} resource {resource_id} "
            f"to project {project_id} at {allocation * 100}%"
        )
        
        # Validate allocation
        if allocation < 0.0 or allocation > 1.0:
            raise ResourceAllocationError(
                message=f"Allocation must be between 0.0 and 1.0, got {allocation}",
                resource_type=resource_type.value
            )
        
        # Check if the resource is already allocated to other projects
        # This would require querying across all projects, which we'll simplify for now
        # In a real implementation, we would check for conflicts
        
        # Allocate resource
        resource = self.project_repo.allocate_resource(
            project_id=project_id,
            resource_type=resource_type.value,
            resource_id=resource_id,
            allocation=allocation,
            start_date=start_date,
            end_date=end_date,
            metadata=metadata
        )
        
        return {
            "id": resource.id,
            "project_id": resource.project_id,
            "resource_type": resource.resource_type,
            "resource_id": resource.resource_id,
            "allocation": resource.allocation,
            "allocated_at": resource.allocated_at,
            "released_at": resource.released_at,
            "start_date": resource.start_date,
            "end_date": resource.end_date,
            "metadata": resource.metadata or {}
        }
    
    def get_resources(
        self, 
        project_id: UUID,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resources allocated to a project.
        
        Args:
            project_id: Project ID
            resource_type: Optional filter by resource type
            
        Returns:
            List of allocated resources
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting resources for project: {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get resources
        resources = self.project_repo.get_project_resources(
            project_id=project_id,
            resource_type=resource_type
        )
        
        return [
            {
                "id": resource.id,
                "project_id": resource.project_id,
                "resource_type": resource.resource_type,
                "resource_id": resource.resource_id,
                "allocation": resource.allocation,
                "allocated_at": resource.allocated_at,
                "released_at": resource.released_at,
                "start_date": resource.start_date,
                "end_date": resource.end_date,
                "metadata": resource.metadata or {}
            }
            for resource in resources
        ]
    
    def release_resource(self, resource_id: UUID) -> Dict[str, Any]:
        """
        Release a resource allocation.
        
        Args:
            resource_id: Resource allocation ID
            
        Returns:
            Released resource
            
        Raises:
            ResourceAllocationError: If resource release fails
        """
        self.logger.info(f"Releasing resource: {resource_id}")
        
        # Release resource
        resource = self.project_repo.release_resource(resource_id)
        
        if not resource:
            raise ResourceAllocationError(
                message=f"Resource {resource_id} not found or already released"
            )
        
        return {
            "id": resource.id,
            "project_id": resource.project_id,
            "resource_type": resource.resource_type,
            "resource_id": resource.resource_id,
            "allocation": resource.allocation,
            "allocated_at": resource.allocated_at,
            "released_at": resource.released_at,
            "metadata": resource.metadata or {}
        }
    
    def optimize_resources(
        self, 
        project_id: UUID, 
        target: OptimizationTarget,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize resource allocation for a project.
        
        Args:
            project_id: Project ID
            target: Optimization target
            constraints: Optional constraints
            
        Returns:
            Optimization result
            
        Raises:
            ProjectNotFoundError: If project not found
            ResourceAllocationError: If resource optimization fails
        """
        self.logger.info(f"Optimizing resources for project {project_id} with target: {target}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get current resources
        current_resources = self.get_resources(project_id)
        
        if not current_resources:
            return {
                "optimized_resources": [],
                "optimization_score": 0.0,
                "metrics": {
                    "resource_count": 0,
                    "optimization_target": target.value,
                    "message": "No resources to optimize"
                }
            }
        
        # Create optimizer based on target
        optimizer = ResourceOptimizer.create_optimizer(target)
        
        # Optimize resources
        optimized_resources, optimization_score = optimizer(current_resources, constraints)
        
        # Apply optimizations to database
        for resource in optimized_resources:
            # Update allocation in database
            updated_resource = self.project_repo.update_resource_allocation(
                resource_id=resource["id"],
                allocation=resource["allocation"]
            )
        
        return {
            "optimized_resources": optimized_resources,
            "optimization_score": optimization_score,
            "metrics": {
                "resource_count": len(optimized_resources),
                "optimization_target": target.value,
                "average_allocation": sum(r["allocation"] for r in optimized_resources) / len(optimized_resources),
                "constraints": constraints or {}
            }
        }
