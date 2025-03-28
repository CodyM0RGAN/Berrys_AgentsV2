"""
Progress Tracker for Project Coordinator service.

This module provides progress tracking functionality for projects with support
for different tracking strategies.
"""
import logging
from typing import List, Dict, Any, Optional, Protocol, Type
from uuid import UUID
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import statistics

from ...repositories.project import ProjectRepository
from ...exceptions import ProjectNotFoundError
from ...config import Settings


class AbstractProgressTracker(ABC):
    """
    Abstract base class for progress tracking strategies.
    
    This implements the Strategy Pattern, allowing different progress tracking
    algorithms to be used interchangeably.
    """
    
    @abstractmethod
    def calculate_progress(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate overall progress from progress records.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress percentage (0-100)
        """
        pass
    
    @abstractmethod
    def calculate_progress_rate(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate progress rate from progress records.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress rate (percentage points per day)
        """
        pass


class SimpleProgressTracker(AbstractProgressTracker):
    """
    Simple progress tracker that uses the latest progress record.
    """
    
    def calculate_progress(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate overall progress as the value from the latest record.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress percentage (0-100)
        """
        if not progress_records:
            return 0.0
        
        # Return the percentage from the latest record
        return progress_records[0]["percentage"]
    
    def calculate_progress_rate(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate progress rate as change per day over time.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress rate (percentage points per day)
        """
        if len(progress_records) < 2:
            return 0.0
        
        # Get first and last record
        latest = progress_records[0]
        earliest = progress_records[-1]
        
        # Calculate time difference in days
        time_diff = (latest["recorded_at"] - earliest["recorded_at"]).total_seconds() / (24 * 3600)
        
        # Avoid division by zero
        if time_diff == 0:
            return 0.0
        
        # Calculate rate
        progress_diff = latest["percentage"] - earliest["percentage"]
        rate = progress_diff / time_diff
        
        return rate


class WeightedProgressTracker(AbstractProgressTracker):
    """
    Weighted progress tracker that calculates progress based on weighted tasks.
    """
    
    def calculate_progress(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate overall progress using weighted metrics.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress percentage (0-100)
        """
        if not progress_records:
            return 0.0
        
        # Use the latest record
        latest = progress_records[0]
        
        # Check if metrics contain weights
        metrics = latest.get("metrics", {})
        if not metrics or "weighted_tasks" not in metrics:
            # Fall back to simple percentage
            return latest["percentage"]
        
        weighted_tasks = metrics["weighted_tasks"]
        total_weight = sum(task.get("weight", 1) for task in weighted_tasks)
        
        if total_weight == 0:
            return 0.0
        
        # Calculate weighted progress
        weighted_progress = sum(
            task.get("percentage", 0) * task.get("weight", 1) / total_weight
            for task in weighted_tasks
        )
        
        return min(weighted_progress, 100.0)
    
    def calculate_progress_rate(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate progress rate using weighted metrics.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress rate (percentage points per day)
        """
        # For rate calculation, use calculated progress values
        calculated_progress = [
            {
                "percentage": self.calculate_progress([record]),
                "recorded_at": record["recorded_at"]
            }
            for record in progress_records
        ]
        
        # Use SimpleProgressTracker for rate calculation
        simple_tracker = SimpleProgressTracker()
        return simple_tracker.calculate_progress_rate(calculated_progress)


class MilestoneBasedTracker(AbstractProgressTracker):
    """
    Milestone-based progress tracker that calculates progress based on milestones.
    """
    
    def calculate_progress(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate overall progress based on milestone completion.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress percentage (0-100)
        """
        if not progress_records:
            return 0.0
        
        # Use the latest record
        latest = progress_records[0]
        
        # Check if metrics contain milestones
        metrics = latest.get("metrics", {})
        if not metrics or "milestones" not in metrics:
            # Fall back to simple percentage
            return latest["percentage"]
        
        milestones = metrics["milestones"]
        total_milestones = len(milestones)
        
        if total_milestones == 0:
            return 0.0
        
        # Count completed milestones
        completed_milestones = sum(1 for m in milestones if m.get("completed", False))
        
        # Calculate progress
        milestone_progress = (completed_milestones / total_milestones) * 100.0
        
        return milestone_progress
    
    def calculate_progress_rate(self, progress_records: List[Dict[str, Any]]) -> float:
        """
        Calculate progress rate based on milestone completion rate.
        
        Args:
            progress_records: List of progress records
            
        Returns:
            Progress rate (percentage points per day)
        """
        # For rate calculation, use calculated progress values
        calculated_progress = [
            {
                "percentage": self.calculate_progress([record]),
                "recorded_at": record["recorded_at"]
            }
            for record in progress_records
        ]
        
        # Use SimpleProgressTracker for rate calculation
        simple_tracker = SimpleProgressTracker()
        return simple_tracker.calculate_progress_rate(calculated_progress)


class ProgressTracker:
    """
    Progress Tracker service.
    
    This service manages project progress tracking and analysis.
    
    Attributes:
        project_repo: Project repository
        settings: Application settings
        logger: Logger instance
        trackers: Dictionary of progress tracker strategies
    """
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        settings: Settings,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Progress Tracker.
        
        Args:
            project_repo: Project repository
            settings: Application settings
            logger: Logger instance (optional)
        """
        self.project_repo = project_repo
        self.settings = settings
        self.logger = logger or logging.getLogger("progress_tracker")
        
        # Register tracker strategies
        self.trackers = {
            "simple": SimpleProgressTracker(),
            "weighted": WeightedProgressTracker(),
            "milestone": MilestoneBasedTracker()
        }
        
        # Default tracker
        self.default_tracker_type = "simple"
    
    def record_progress(
        self, 
        project_id: UUID, 
        percentage: float,
        metrics: Optional[Dict[str, Any]] = None,
        milestone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record progress for a project.
        
        Args:
            project_id: Project ID
            percentage: Progress percentage (0-100)
            metrics: Additional metrics
            milestone: Optional milestone name
            
        Returns:
            Created progress record
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Recording progress for project {project_id}: {percentage}%")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Create progress record
        progress_record = self.project_repo.add_progress_record(
            project_id=project_id,
            percentage=percentage,
            metrics=metrics,
            milestone=milestone
        )
        
        return {
            "id": progress_record.id,
            "project_id": progress_record.project_id,
            "percentage": progress_record.percentage,
            "recorded_at": progress_record.recorded_at,
            "metrics": progress_record.metrics or {},
            "milestone": progress_record.milestone
        }
    
    def get_current_progress(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get current progress for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Current progress
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting current progress for project: {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get the latest progress record
        latest_progress = self.project_repo.get_latest_progress(project_id)
        
        if not latest_progress:
            return {
                "percentage": 0.0,
                "recorded_at": None,
                "metrics": {},
                "milestone": None
            }
        
        return {
            "id": latest_progress.id,
            "project_id": latest_progress.project_id,
            "percentage": latest_progress.percentage,
            "recorded_at": latest_progress.recorded_at,
            "metrics": latest_progress.metrics or {},
            "milestone": latest_progress.milestone
        }
    
    def get_progress_history(self, project_id: UUID, limit: int = 100) -> Dict[str, Any]:
        """
        Get progress history for a project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of records to return
            
        Returns:
            Progress history with analytics
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        self.logger.info(f"Getting progress history for project: {project_id}")
        
        # Ensure project exists
        self.project_repo.get_project_or_404(project_id)
        
        # Get progress history
        progress_records = self.project_repo.get_progress_history(project_id, limit)
        
        # Convert to response format
        progress_points = [
            {
                "id": record.id,
                "project_id": record.project_id,
                "percentage": record.percentage,
                "recorded_at": record.recorded_at,
                "metrics": record.metrics or {},
                "milestone": record.milestone
            }
            for record in progress_records
        ]
        
        # Calculate progress rate
        progress_rate = self._calculate_progress_rate(progress_points)
        
        # Determine best tracker
        tracker_type = self._determine_best_tracker(progress_points)
        tracker = self.trackers[tracker_type]
        
        # Calculate current progress
        current_progress = tracker.calculate_progress(progress_points) if progress_points else 0.0
        
        return {
            "progress_points": progress_points,
            "current_progress": current_progress,
            "average_progress_rate": progress_rate,
            "estimated_completion_days": self._estimate_completion_days(current_progress, progress_rate),
            "tracker_used": tracker_type
        }
    
    def _calculate_progress_rate(self, progress_points: List[Dict[str, Any]]) -> float:
        """
        Calculate average progress rate.
        
        Args:
            progress_points: List of progress records
            
        Returns:
            Progress rate (percentage points per day)
        """
        if len(progress_points) < 2:
            return 0.0
        
        # Determine best tracker
        tracker_type = self._determine_best_tracker(progress_points)
        tracker = self.trackers[tracker_type]
        
        # Calculate rate using the tracker
        return tracker.calculate_progress_rate(progress_points)
    
    def _estimate_completion_days(self, current_progress: float, progress_rate: float) -> Optional[float]:
        """
        Estimate days to completion.
        
        Args:
            current_progress: Current progress percentage
            progress_rate: Progress rate (percentage points per day)
            
        Returns:
            Estimated days to completion, or None if cannot be estimated
        """
        if progress_rate <= 0:
            return None
        
        remaining_progress = 100.0 - current_progress
        days = remaining_progress / progress_rate
        
        return max(days, 0.0)
    
    def _determine_best_tracker(self, progress_points: List[Dict[str, Any]]) -> str:
        """
        Determine the best progress tracker for the given data.
        
        Args:
            progress_points: List of progress records
            
        Returns:
            Tracker type name
        """
        if not progress_points:
            return self.default_tracker_type
        
        # Use latest record to check for specific metrics
        latest = progress_points[0]
        metrics = latest.get("metrics", {})
        
        # Check for weighted tasks
        if metrics and "weighted_tasks" in metrics:
            return "weighted"
        
        # Check for milestones
        if metrics and "milestones" in metrics:
            return "milestone"
        
        # Default to simple tracker
        return "simple"
