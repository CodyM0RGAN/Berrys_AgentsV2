import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Tuple

from shared.utils.src.messaging import EventBus

# Corrected import to use ModelOrchestrationConfig
from ..config import ModelOrchestrationConfig
from ..exceptions import ModelNotFoundError, InvalidRequestError
from ..models.performance import ModelPerformanceModel, ModelFeedbackModel, ModelPerformanceHistoryModel

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Service for tracking and evaluating model performance.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        settings: ModelOrchestrationConfig, # Updated type hint
    ):
        """
        Initialize the performance tracker.
        
        Args:
            db: Database session
            event_bus: Event bus
            settings: Application settings
        """
        self.db = db
        self.event_bus = event_bus
        self.settings = settings
    
    async def record_request_result(
        self,
        request_id: str,
        model_id: str,
        task_type: Optional[str],
        success: bool,
        quality_score: Optional[float] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record the result of a model request.
        
        Args:
            request_id: Request ID
            model_id: Model ID
            task_type: Type of task (e.g., 'code_generation', 'reasoning')
            success: Whether the request was successful
            quality_score: Estimated quality score (0.0-1.0)
            confidence: Model's confidence in the response (0.0-1.0)
            metadata: Additional metadata
        """
        try:
            # Skip if no task type (can't categorize)
            if not task_type:
                return
            
            # Get existing performance record or create new one
            query = select(ModelPerformanceModel).where(
                and_(
                    ModelPerformanceModel.model_id == model_id,
                    ModelPerformanceModel.task_type == task_type,
                )
            )
            result = await self.db.execute(query)
            performance = result.scalars().first()
            
            if not performance:
                # Create new performance record
                performance = ModelPerformanceModel(
                    model_id=model_id,
                    task_type=task_type,
                    quality_score=quality_score or 0.5,  # Default middle score
                    success_rate=1.0 if success else 0.0,
                    sample_count=1,
                    metrics={
                        "confidence_sum": confidence or 0.0,
                        "quality_sum": quality_score or 0.5,
                    },
                )
                self.db.add(performance)
            else:
                # Update existing performance record
                new_sample_count = performance.sample_count + 1
                
                # Update success rate
                current_success_count = performance.success_rate * performance.sample_count
                new_success_count = current_success_count + (1 if success else 0)
                new_success_rate = new_success_count / new_sample_count
                
                # Update quality score (if provided)
                if quality_score is not None:
                    current_quality_sum = performance.metrics.get("quality_sum", performance.quality_score * performance.sample_count)
                    new_quality_sum = current_quality_sum + quality_score
                    new_quality_score = new_quality_sum / new_sample_count
                    
                    # Update metrics
                    metrics = performance.metrics or {}
                    metrics["quality_sum"] = new_quality_sum
                    
                    performance.quality_score = new_quality_score
                    performance.metrics = metrics
                
                # Update confidence (if provided)
                if confidence is not None:
                    metrics = performance.metrics or {}
                    current_confidence_sum = metrics.get("confidence_sum", 0.0)
                    metrics["confidence_sum"] = current_confidence_sum + confidence
                    performance.metrics = metrics
                
                # Update success rate and sample count
                performance.success_rate = new_success_rate
                performance.sample_count = new_sample_count
            
            # Commit changes
            await self.db.commit()
            
            # Log success
            logger.info(f"Recorded performance for model {model_id} on task {task_type}: success={success}, quality={quality_score}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording performance: {str(e)}")
    
    async def record_feedback(
        self,
        request_id: str,
        model_id: str,
        success: bool,
        quality_rating: Optional[float] = None,
        feedback_text: Optional[str] = None,
        task_type: Optional[str] = None,
        corrections: Optional[Dict[str, str]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Record user feedback for a model response.
        
        Args:
            request_id: Request ID
            model_id: Model ID
            success: Whether the response was successful
            quality_rating: User-provided quality rating (0.0-1.0)
            feedback_text: Textual feedback
            task_type: Type of task
            corrections: Corrections to the response
            user_id: User ID
            
        Returns:
            str: Feedback ID
        """
        try:
            # Create feedback record
            feedback_id = str(uuid.uuid4())
            
            # Handle corrections safely
            has_corrections = bool(corrections)
            original_content = None
            corrected_content = None
            
            if corrections and isinstance(corrections, dict):
                original_content = corrections.get("original")
                corrected_content = corrections.get("corrected")
            
            feedback = ModelFeedbackModel(
                id=uuid.UUID(feedback_id),
                request_id=request_id,
                model_id=model_id,
                task_type=task_type,
                quality_rating=quality_rating,
                success=success,
                feedback_text=feedback_text,
                has_corrections=has_corrections,
                original_content=original_content,
                corrected_content=corrected_content,
                user_id=user_id,
            )
            
            self.db.add(feedback)
            
            # Update performance metrics if task type is provided
            if task_type:
                # Get existing performance record
                query = select(ModelPerformanceModel).where(
                    and_(
                        ModelPerformanceModel.model_id == model_id,
                        ModelPerformanceModel.task_type == task_type,
                    )
                )
                result = await self.db.execute(query)
                performance = result.scalars().first()
                
                if performance:
                    # Calculate new metrics
                    # We weight user feedback more heavily than automatic metrics
                    feedback_weight = 2.0  # User feedback counts as 2 samples
                    
                    # Update sample count
                    new_sample_count = performance.sample_count + feedback_weight
                    
                    # Update success rate
                    current_success_count = performance.success_rate * performance.sample_count
                    new_success_count = current_success_count + (feedback_weight if success else 0)
                    new_success_rate = new_success_count / new_sample_count
                    
                    # Update quality score (if provided)
                    if quality_rating is not None:
                        current_quality_sum = performance.metrics.get("quality_sum", performance.quality_score * performance.sample_count)
                        new_quality_sum = current_quality_sum + (quality_rating * feedback_weight)
                        new_quality_score = new_quality_sum / new_sample_count
                        
                        # Update metrics
                        metrics = performance.metrics or {}
                        metrics["quality_sum"] = new_quality_sum
                        
                        performance.quality_score = new_quality_score
                        performance.metrics = metrics
                    
                    # Update success rate and sample count
                    performance.success_rate = new_success_rate
                    performance.sample_count = new_sample_count
            
            # Commit changes
            await self.db.commit()
            
            # Publish event
            await self.event_bus.publish_event(
                "model.feedback.received",
                {
                    "feedback_id": feedback_id,
                    "request_id": request_id,
                    "model_id": model_id,
                    "task_type": task_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "feedback": {
                        "quality_rating": quality_rating,
                        "success": success,
                        "has_corrections": bool(corrections),
                    }
                }
            )
            
            # Log success
            logger.info(f"Recorded feedback for model {model_id} on request {request_id}: success={success}, quality={quality_rating}")
            
            return feedback_id
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording feedback: {str(e)}")
            raise InvalidRequestError(f"Failed to record feedback: {str(e)}")
    
    async def get_model_performance(
        self,
        model_id: Optional[str] = None,
        task_type: Optional[str] = None,
        min_samples: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for models.
        
        Args:
            model_id: Filter by model ID
            task_type: Filter by task type
            min_samples: Minimum number of samples required
            
        Returns:
            List[Dict[str, Any]]: List of performance metrics
        """
        try:
            # Build query
            query = select(ModelPerformanceModel)
            
            # Apply filters
            if model_id:
                query = query.where(ModelPerformanceModel.model_id == model_id)
            
            if task_type:
                query = query.where(ModelPerformanceModel.task_type == task_type)
            
            # Apply minimum samples filter
            query = query.where(ModelPerformanceModel.sample_count >= min_samples)
            
            # Execute query
            result = await self.db.execute(query)
            performances = result.scalars().all()
            
            # Convert to dictionaries
            return [performance.to_dict() for performance in performances]
            
        except Exception as e:
            logger.error(f"Error getting model performance: {str(e)}")
            return []
    
    async def get_best_model_for_task(
        self,
        task_type: str,
        min_quality_score: float = 0.0,
        min_success_rate: float = 0.0,
        min_samples: int = 5,
        model_ids: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Get the best model for a task based on performance metrics.
        
        Args:
            task_type: Task type
            min_quality_score: Minimum quality score
            min_success_rate: Minimum success rate
            min_samples: Minimum number of samples
            model_ids: List of model IDs to consider
            
        Returns:
            Optional[str]: Best model ID or None if no suitable model found
        """
        try:
            # Build query
            query = select(ModelPerformanceModel).where(
                and_(
                    ModelPerformanceModel.task_type == task_type,
                    ModelPerformanceModel.quality_score >= min_quality_score,
                    ModelPerformanceModel.success_rate >= min_success_rate,
                    ModelPerformanceModel.sample_count >= min_samples,
                )
            )
            
            # Filter by model IDs if provided
            if model_ids:
                query = query.where(ModelPerformanceModel.model_id.in_(model_ids))
            
            # Order by quality score and success rate
            query = query.order_by(
                desc(ModelPerformanceModel.quality_score),
                desc(ModelPerformanceModel.success_rate),
                desc(ModelPerformanceModel.sample_count),
            )
            
            # Execute query
            result = await self.db.execute(query)
            performance = result.scalars().first()
            
            # Return best model ID or None
            return performance.model_id if performance else None
            
        except Exception as e:
            logger.error(f"Error getting best model for task: {str(e)}")
            return None
    
    async def update_performance_history(self) -> None:
        """
        Update performance history records.
        This should be called periodically (e.g., daily) to maintain historical data.
        """
        try:
            # Get current date
            now = datetime.utcnow()
            
            # Calculate period boundaries
            day_start = datetime(now.year, now.month, now.day)
            week_start = day_start - timedelta(days=day_start.weekday())
            month_start = datetime(now.year, now.month, 1)
            
            # Get all performance records
            query = select(ModelPerformanceModel)
            result = await self.db.execute(query)
            performances = result.scalars().all()
            
            # Process each performance record
            for performance in performances:
                # Create or update daily record
                await self._create_or_update_history(
                    performance,
                    period_start=day_start,
                    period_end=day_start + timedelta(days=1),
                    period_type="day",
                )
                
                # Create or update weekly record
                await self._create_or_update_history(
                    performance,
                    period_start=week_start,
                    period_end=week_start + timedelta(days=7),
                    period_type="week",
                )
                
                # Create or update monthly record
                # Calculate next month more elegantly
                if month_start.month == 12:
                    next_month_start = datetime(month_start.year + 1, 1, 1)
                else:
                    next_month_start = datetime(month_start.year, month_start.month + 1, 1)
                
                await self._create_or_update_history(
                    performance,
                    period_start=month_start,
                    period_end=next_month_start,
                    period_type="month",
                )
            
            # Commit changes
            await self.db.commit()
            
            logger.info("Updated performance history records")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating performance history: {str(e)}")
    
    async def _create_or_update_history(
        self,
        performance: ModelPerformanceModel,
        period_start: datetime,
        period_end: datetime,
        period_type: str,
    ) -> None:
        """
        Create or update a performance history record.
        
        Args:
            performance: Performance record
            period_start: Period start date
            period_end: Period end date
            period_type: Period type ('day', 'week', 'month')
        """
        # Check if history record exists
        query = select(ModelPerformanceHistoryModel).where(
            and_(
                ModelPerformanceHistoryModel.model_id == performance.model_id,
                ModelPerformanceHistoryModel.task_type == performance.task_type,
                ModelPerformanceHistoryModel.period_start == period_start,
                ModelPerformanceHistoryModel.period_type == period_type,
            )
        )
        result = await self.db.execute(query)
        history = result.scalars().first()
        
        if history:
            # Update existing record
            history.quality_score = performance.quality_score
            history.success_rate = performance.success_rate
            history.sample_count = performance.sample_count
            history.metrics = performance.metrics
        else:
            # Create new record
            history = ModelPerformanceHistoryModel(
                model_id=performance.model_id,
                task_type=performance.task_type,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                quality_score=performance.quality_score,
                success_rate=performance.success_rate,
                sample_count=performance.sample_count,
                metrics=performance.metrics,
            )
            self.db.add(history)
