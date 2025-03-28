"""
Analytics Engine for Project Coordinator service.

This module provides functionality for generating project analytics and insights.
"""
import logging
from typing import List, Dict, Any, Optional, Type
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
import json
import statistics

from ...repositories.project import ProjectRepository
from ...exceptions import AnalyticsGenerationError, ProjectNotFoundError
from ...models.api import AnalyticsType
from ...config import Settings


class AnalyticsGenerator:
    """
    Base class for analytics generators.
    
    This implements a Template Method pattern, where subclasses provide specific
    analytics generation logic.
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings
    ):
        """
        Initialize the analytics generator.
        
        Args:
            project_repo: Project repository
            settings: Application settings
        """
        self.project_repo = project_repo
        self.settings = settings
    
    def generate(
        self, 
        project_id: UUID, 
        parameters: Optional[Dict[str, Any]] = None,
        time_range: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Generate analytics data.
        
        This is a template method that handles common logic and delegates
        specific analytics generation to subclasses.
        
        Args:
            project_id: Project ID
            parameters: Optional parameters for analytics generation
            time_range: Optional time range for analytics
            
        Returns:
            Generated analytics data
            
        Raises:
            ProjectNotFoundError: If project not found
            AnalyticsGenerationError: If analytics generation fails
        """
        # Ensure project exists
        project = self.project_repo.get_project_or_404(project_id)
        
        # Initialize default parameters and time range
        parameters = parameters or {}
        time_range = time_range or {}
        
        # Generate analytics
        try:
            analytics_data = self._generate_analytics(
                project_id=project_id,
                project=project,
                parameters=parameters,
                time_range=time_range
            )
            
            # Generate visualizations
            visualizations = self._generate_visualizations(analytics_data, parameters)
            
            return {
                "data": analytics_data,
                "visualizations": visualizations,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise AnalyticsGenerationError(
                message=f"Failed to generate analytics: {str(e)}",
                analytics_type=self.__class__.__name__
            )
    
    def _generate_analytics(
        self, 
        project_id: UUID, 
        project: Dict[str, Any],
        parameters: Dict[str, Any],
        time_range: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """
        Generate analytics data.
        
        This is implemented by subclasses to provide specific analytics generation logic.
        
        Args:
            project_id: Project ID
            project: Project data
            parameters: Parameters for analytics generation
            time_range: Time range for analytics
            
        Returns:
            Generated analytics data
        """
        raise NotImplementedError("Subclasses must implement _generate_analytics")
    
    def _generate_visualizations(
        self, 
        analytics_data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate visualizations for analytics data.
        
        This is implemented by subclasses to provide specific visualization generation logic.
        
        Args:
            analytics_data: Analytics data
            parameters: Parameters for visualization generation
            
        Returns:
            List of visualization configurations
        """
        return []  # Default implementation - no visualizations


class ProgressAnalyticsGenerator(AnalyticsGenerator):
    """Analytics generator for project progress."""
    
    def _generate_analytics(
        self, 
        project_id: UUID, 
        project: Dict[str, Any],
        parameters: Dict[str, Any],
        time_range: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """
        Generate progress analytics data.
        
        Args:
            project_id: Project ID
            project: Project data
            parameters: Parameters for analytics generation
            time_range: Time range for analytics
            
        Returns:
            Progress analytics data
        """
        # Get progress history
        progress_records = self.project_repo.get_progress_history(project_id)
        
        if not progress_records:
            return {
                "current_progress": 0.0,
                "progress_trend": "no_data",
                "milestone_completion": [],
                "estimated_completion": None
            }
        
        # Convert to list of dictionaries
        progress_points = [
            {
                "percentage": record.percentage,
                "recorded_at": record.recorded_at,
                "metrics": record.metrics or {},
                "milestone": record.milestone
            }
            for record in progress_records
        ]
        
        # Calculate trend
        trend = self._calculate_trend(progress_points)
        
        # Calculate milestone completions
        milestones = self._extract_milestones(progress_points)
        
        # Estimate completion
        completion_estimate = self._estimate_completion(progress_points, trend)
        
        return {
            "current_progress": progress_points[0]["percentage"],
            "progress_trend": trend,
            "milestone_completion": milestones,
            "estimated_completion": completion_estimate,
            "progress_points": progress_points[:10]  # Include last 10 points
        }
    
    def _calculate_trend(self, progress_points: List[Dict[str, Any]]) -> str:
        """
        Calculate progress trend.
        
        Args:
            progress_points: List of progress records
            
        Returns:
            Trend description
        """
        if len(progress_points) < 2:
            return "no_trend"
        
        # Get last few points to determine recent trend
        recent_points = progress_points[:min(5, len(progress_points))]
        
        # Calculate rates
        rates = []
        for i in range(len(recent_points) - 1):
            current = recent_points[i]
            next_point = recent_points[i + 1]
            
            time_diff = (current["recorded_at"] - next_point["recorded_at"]).total_seconds()
            if time_diff <= 0:
                continue
                
            progress_diff = current["percentage"] - next_point["percentage"]
            rate = progress_diff / (time_diff / (24 * 3600))  # points per day
            rates.append(rate)
        
        if not rates:
            return "no_trend"
        
        avg_rate = sum(rates) / len(rates)
        
        if avg_rate > 1.0:
            return "strong_progress"
        elif avg_rate > 0.5:
            return "moderate_progress"
        elif avg_rate > 0.1:
            return "slow_progress"
        elif avg_rate > -0.1:
            return "stalled"
        else:
            return "regressing"
    
    def _extract_milestones(self, progress_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract milestone completions from progress records.
        
        Args:
            progress_points: List of progress records
            
        Returns:
            List of milestone completions
        """
        milestones = []
        seen_milestones = set()
        
        for point in progress_points:
            if point.get("milestone") and point["milestone"] not in seen_milestones:
                milestones.append({
                    "name": point["milestone"],
                    "percentage": point["percentage"],
                    "completed_at": point["recorded_at"]
                })
                seen_milestones.add(point["milestone"])
        
        return milestones
    
    def _estimate_completion(
        self, 
        progress_points: List[Dict[str, Any]], 
        trend: str
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate project completion date.
        
        Args:
            progress_points: List of progress records
            trend: Progress trend
            
        Returns:
            Completion estimate information
        """
        if len(progress_points) < 2 or trend in ["no_trend", "stalled", "regressing"]:
            return None
        
        # Calculate average progress rate
        rates = []
        for i in range(len(progress_points) - 1):
            current = progress_points[i]
            next_point = progress_points[i + 1]
            
            time_diff = (current["recorded_at"] - next_point["recorded_at"]).total_seconds()
            if time_diff <= 0:
                continue
                
            progress_diff = current["percentage"] - next_point["percentage"]
            rate = progress_diff / (time_diff / (24 * 3600))  # points per day
            rates.append(rate)
        
        if not rates:
            return None
        
        avg_rate = sum(rates) / len(rates)
        
        if avg_rate <= 0:
            return None
        
        # Calculate days to completion
        current_progress = progress_points[0]["percentage"]
        remaining_progress = 100.0 - current_progress
        
        days_to_completion = remaining_progress / avg_rate
        estimated_completion = progress_points[0]["recorded_at"] + timedelta(days=days_to_completion)
        
        # Calculate confidence
        rate_variation = statistics.stdev(rates) if len(rates) > 1 else 0
        confidence = max(0.0, min(1.0, 1.0 - (rate_variation / max(abs(avg_rate), 0.01))))
        
        return {
            "estimated_date": estimated_completion,
            "days_remaining": days_to_completion,
            "confidence": confidence,
            "current_rate": avg_rate
        }
    
    def _generate_visualizations(
        self, 
        analytics_data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate visualizations for progress analytics.
        
        Args:
            analytics_data: Progress analytics data
            parameters: Parameters for visualization generation
            
        Returns:
            List of visualization configurations
        """
        if "progress_points" not in analytics_data or not analytics_data["progress_points"]:
            return []
        
        # Generate line chart configuration for progress over time
        progress_chart = {
            "type": "line_chart",
            "title": "Progress Over Time",
            "x_axis": {
                "label": "Date",
                "type": "datetime",
                "values": [point["recorded_at"].isoformat() for point in reversed(analytics_data["progress_points"])]
            },
            "y_axis": {
                "label": "Progress (%)",
                "min": 0,
                "max": 100,
                "values": [point["percentage"] for point in reversed(analytics_data["progress_points"])]
            },
            "series": [{
                "name": "Progress",
                "color": "#4285F4"
            }]
        }
        
        # Generate milestone chart if there are milestones
        milestones = analytics_data.get("milestone_completion", [])
        if milestones:
            milestone_chart = {
                "type": "milestone_chart",
                "title": "Milestone Completion",
                "milestones": [
                    {
                        "name": milestone["name"],
                        "percentage": milestone["percentage"],
                        "date": milestone["completed_at"].isoformat()
                    }
                    for milestone in milestones
                ]
            }
            return [progress_chart, milestone_chart]
        
        return [progress_chart]


class ResourceAnalyticsGenerator(AnalyticsGenerator):
    """Analytics generator for project resources."""
    
    def _generate_analytics(
        self, 
        project_id: UUID, 
        project: Dict[str, Any],
        parameters: Dict[str, Any],
        time_range: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """
        Generate resource analytics data.
        
        Args:
            project_id: Project ID
            project: Project data
            parameters: Parameters for analytics generation
            time_range: Time range for analytics
            
        Returns:
            Resource analytics data
        """
        # Get resources
        resources = self.project_repo.get_project_resources(project_id)
        
        if not resources:
            return {
                "resource_count": 0,
                "resource_allocation": {},
                "resource_utilization": 0.0
            }
        
        # Group resources by type
        resources_by_type = {}
        for resource in resources:
            resource_type = resource.resource_type
            if resource_type not in resources_by_type:
                resources_by_type[resource_type] = []
            
            resources_by_type[resource_type].append({
                "id": resource.id,
                "resource_id": resource.resource_id,
                "allocation": resource.allocation,
                "allocated_at": resource.allocated_at,
                "metadata": resource.metadata or {}
            })
        
        # Calculate utilization
        total_allocation = sum(
            resource.allocation
            for resource in resources
        )
        
        avg_allocation = total_allocation / len(resources) if resources else 0.0
        
        # Calculate allocation by time
        allocation_by_time = self._calculate_allocation_by_time(resources)
        
        return {
            "resource_count": len(resources),
            "resources_by_type": resources_by_type,
            "total_allocation": total_allocation,
            "average_allocation": avg_allocation,
            "allocation_by_time": allocation_by_time
        }
    
    def _calculate_allocation_by_time(
        self,
        resources: List[Any]
    ) -> Dict[str, float]:
        """
        Calculate resource allocation by time period.
        
        Args:
            resources: List of resource records
            
        Returns:
            Resource allocation by time period
        """
        # Group resources by week
        now = datetime.utcnow()
        allocation_by_week = {}
        
        for resource in resources:
            allocated_at = resource.allocated_at
            week_key = allocated_at.strftime("%Y-%U")  # ISO year and week number
            
            if week_key not in allocation_by_week:
                allocation_by_week[week_key] = 0.0
            
            allocation_by_week[week_key] += resource.allocation
        
        # Sort by week
        sorted_weeks = sorted(allocation_by_week.keys())
        
        return {
            "labels": sorted_weeks,
            "values": [allocation_by_week[week] for week in sorted_weeks]
        }
    
    def _generate_visualizations(
        self, 
        analytics_data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate visualizations for resource analytics.
        
        Args:
            analytics_data: Resource analytics data
            parameters: Parameters for visualization generation
            
        Returns:
            List of visualization configurations
        """
        if "resources_by_type" not in analytics_data or not analytics_data["resources_by_type"]:
            return []
        
        # Generate pie chart for resource allocation by type
        resource_types = list(analytics_data["resources_by_type"].keys())
        type_allocations = [
            sum(r["allocation"] for r in resources)
            for resources in analytics_data["resources_by_type"].values()
        ]
        
        pie_chart = {
            "type": "pie_chart",
            "title": "Resource Allocation by Type",
            "labels": resource_types,
            "values": type_allocations,
            "colors": ["#4285F4", "#34A853", "#FBBC05", "#EA4335", "#8F44AD", "#3498DB", "#1ABC9C"]
        }
        
        # Generate bar chart for allocation by time
        allocation_by_time = analytics_data.get("allocation_by_time", {})
        if "labels" in allocation_by_time and allocation_by_time["labels"]:
            bar_chart = {
                "type": "bar_chart",
                "title": "Resource Allocation by Week",
                "x_axis": {
                    "label": "Week",
                    "values": allocation_by_time["labels"]
                },
                "y_axis": {
                    "label": "Allocation",
                    "values": allocation_by_time["values"]
                },
                "color": "#4285F4"
            }
            return [pie_chart, bar_chart]
        
        return [pie_chart]


class PerformanceAnalyticsGenerator(AnalyticsGenerator):
    """Analytics generator for project performance."""
    
    def _generate_analytics(
        self, 
        project_id: UUID, 
        project: Dict[str, Any],
        parameters: Dict[str, Any],
        time_range: Dict[str, datetime]
    ) -> Dict[str, Any]:
        """
        Generate performance analytics data.
        
        Args:
            project_id: Project ID
            project: Project data
            parameters: Parameters for analytics generation
            time_range: Time range for analytics
            
        Returns:
            Performance analytics data
        """
        # Get progress history
        progress_records = self.project_repo.get_progress_history(project_id)
        
        # Get resources
        resources = self.project_repo.get_project_resources(project_id)
        
        # Calculate performance metrics
        efficiency = self._calculate_efficiency(progress_records, resources)
        quality_metrics = self._calculate_quality_metrics(project)
        
        return {
            "efficiency": efficiency,
            "quality_metrics": quality_metrics,
            "performance_score": (efficiency + quality_metrics["overall_quality"]) / 2
        }
    
    def _calculate_efficiency(
        self,
        progress_records: List[Any],
        resources: List[Any]
    ) -> float:
        """
        Calculate project efficiency.
        
        Args:
            progress_records: List of progress records
            resources: List of resource records
            
        Returns:
            Efficiency score (0-1)
        """
        if not progress_records or not resources:
            return 0.5  # Default value
        
        # Calculate progress rate
        if len(progress_records) >= 2:
            latest = progress_records[0]
            earliest = progress_records[-1]
            
            time_diff = (latest.recorded_at - earliest.recorded_at).total_seconds()
            if time_diff > 0:
                progress_diff = latest.percentage - earliest.percentage
                progress_rate = progress_diff / (time_diff / (24 * 3600))  # points per day
            else:
                progress_rate = 0.0
        else:
            progress_rate = 0.0
        
        # Calculate resource utilization
        total_allocation = sum(
            resource.allocation
            for resource in resources
        )
        
        # Calculate efficiency score
        if total_allocation > 0:
            # Higher progress rate with lower resource allocation is more efficient
            efficiency = progress_rate / total_allocation
            
            # Normalize to 0-1 range
            normalized_efficiency = min(1.0, max(0.0, efficiency / 0.5))
        else:
            normalized_efficiency = 0.5  # Default value
        
        return normalized_efficiency
    
    def _calculate_quality_metrics(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate project quality metrics.
        
        Args:
            project: Project data
            
        Returns:
            Quality metrics
        """
        # Extract quality metrics from project metadata
        metadata = project.metadata or {}
        quality_metadata = metadata.get("quality", {})
        
        # Default metrics
        metrics = {
            "code_quality": quality_metadata.get("code_quality", 0.7),
            "test_coverage": quality_metadata.get("test_coverage", 0.6),
            "documentation": quality_metadata.get("documentation", 0.5),
            "user_satisfaction": quality_metadata.get("user_satisfaction", 0.8)
        }
        
        # Calculate overall quality
        metrics["overall_quality"] = sum(metrics.values()) / len(metrics)
        
        return metrics
    
    def _generate_visualizations(
        self, 
        analytics_data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate visualizations for performance analytics.
        
        Args:
            analytics_data: Performance analytics data
            parameters: Parameters for visualization generation
            
        Returns:
            List of visualization configurations
        """
        if "quality_metrics" not in analytics_data:
            return []
        
        # Generate radar chart for quality metrics
        quality_metrics = analytics_data["quality_metrics"]
        radar_chart = {
            "type": "radar_chart",
            "title": "Project Quality Metrics",
            "axes": ["Code Quality", "Test Coverage", "Documentation", "User Satisfaction"],
            "values": [
                quality_metrics["code_quality"],
                quality_metrics["test_coverage"],
                quality_metrics["documentation"],
                quality_metrics["user_satisfaction"]
            ],
            "color": "#4285F4",
            "fill": True,
            "max_value": 1.0
        }
        
        # Generate gauge chart for overall performance
        gauge_chart = {
            "type": "gauge_chart",
            "title": "Overall Performance",
            "value": analytics_data["performance_score"],
            "min": 0.0,
            "max": 1.0,
            "thresholds": [
                {"value": 0.3, "color": "#EA4335"},  # Red
                {"value": 0.7, "color": "#FBBC05"},  # Yellow
                {"value": 1.0, "color": "#34A853"}   # Green
            ]
        }
        
        return [radar_chart, gauge_chart]


class AnalyticsEngine:
    """
    Analytics Engine service.
    
    This service manages analytics generation for projects.
    
    Attributes:
        project_repo: Project repository
        settings: Application settings
        logger: Logger instance
        generators: Dictionary of analytics generators by type
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Analytics Engine.
        
        Args:
            project_repo: Project repository
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.settings = settings
        self.logger = logger or logging.getLogger("analytics_engine")
        
        # Register analytics generators
        self.generators = {
            AnalyticsType.PROGRESS: ProgressAnalyticsGenerator(project_repo, settings),
            AnalyticsType.RESOURCES: ResourceAnalyticsGenerator(project_repo, settings),
            AnalyticsType.PERFORMANCE: PerformanceAnalyticsGenerator(project_repo, settings)
        }
    
    def generate_analytics(
        self, 
        project_id: UUID, 
        analytics_type: AnalyticsType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate analytics for a project.
        
        Args:
            project_id: Project ID
            analytics_type: Type of analytics to generate
            parameters: Optional parameters for analytics generation
            
        Returns:
            Generated analytics
            
        Raises:
            ProjectNotFoundError: If project not found
            AnalyticsGenerationError: If analytics generation fails
        """
        self.logger.info(f"Generating {analytics_type} analytics for project {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Check for cached analytics
        cached_analytics = self._get_cached_analytics(project_id, analytics_type)
        if cached_analytics:
            self.logger.info(f"Using cached {analytics_type} analytics for project {project_id}")
            return cached_analytics
        
        # Get appropriate generator
        if analytics_type not in self.generators:
            raise AnalyticsGenerationError(
                message=f"Analytics type {analytics_type} not supported",
                analytics_type=analytics_type.value
            )
        
        generator = self.generators[analytics_type]
        
        # Generate analytics
        analytics = generator.generate(
            project_id=project_id,
            parameters=parameters
        )
        
        # Cache analytics
        self._cache_analytics(project_id, analytics_type, analytics)
        
        return analytics
    
    def _get_cached_analytics(
        self, 
        project_id: UUID, 
        analytics_type: AnalyticsType
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analytics if available and not expired.
        
        Args:
            project_id: Project ID
            analytics_type: Type of analytics
            
        Returns:
            Cached analytics if available, None otherwise
        """
        # Get latest analytics from database
        analytics_record = self.project_repo.get_latest_analytics(
            project_id=project_id,
            analytics_type=analytics_type.value
        )
        
        if not analytics_record:
            return None
        
        # Check if expired
        if analytics_record.expiry and analytics_record.expiry < datetime.utcnow():
            return None
        
        return {
            "data": analytics_record.data,
            "visualizations": analytics_record.visualization_config,
            "generated_at": analytics_record.generated_at
        }
    
    def _cache_analytics(
        self, 
        project_id: UUID, 
        analytics_type: AnalyticsType,
        analytics: Dict[str, Any]
    ) -> None:
        """
        Cache analytics in database.
        
        Args:
            project_id: Project ID
            analytics_type: Type of analytics
            analytics: Analytics data
        """
        # Cache expiry time (1 hour)
        expiry = datetime.utcnow() + timedelta(hours=1)
        
        # Save to database
        self.project_repo.save_analytics(
            project_id=project_id,
            analytics_type=analytics_type.value,
            data=analytics["data"],
            visualization_config=analytics.get("visualizations"),
            expiry=expiry
        )
