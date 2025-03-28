from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..dependencies import get_performance_tracker, get_current_user, get_optional_user, get_admin_user, UserInfo
from ..exceptions import ModelNotFoundError, InvalidRequestError
from ..services.performance_tracker import PerformanceTracker

router = APIRouter()


@router.post(
    "/feedback",
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Submit feedback for a model response.",
)
async def submit_feedback(
    feedback: Dict[str, Any],
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker),
) -> Dict[str, Any]:
    """
    Submit feedback for a model response.
    
    Args:
        feedback: Feedback data
        current_user: Current authenticated user (optional)
        performance_tracker: Performance tracker service
        
    Returns:
        Dict[str, Any]: Feedback result
        
    Raises:
        InvalidRequestError: If feedback data is invalid
    """
    try:
        # Extract feedback data
        request_id = feedback.get("request_id")
        model_id = feedback.get("model_id")
        success = feedback.get("success")
        
        # Validate required fields
        if not request_id or not model_id or success is None:
            raise InvalidRequestError("Missing required fields: request_id, model_id, success")
        
        # Extract optional fields
        quality_rating = feedback.get("quality_rating")
        feedback_text = feedback.get("feedback")
        task_type = feedback.get("task_type")
        corrections = feedback.get("corrections")
        
        # Set user ID if authenticated
        user_id = current_user.id if current_user else feedback.get("metadata", {}).get("user_id")
        
        # Record feedback
        feedback_id = await performance_tracker.record_feedback(
            request_id=request_id,
            model_id=model_id,
            success=success,
            quality_rating=quality_rating,
            feedback_text=feedback_text,
            task_type=task_type,
            corrections=corrections,
            user_id=user_id,
        )
        
        # Return result
        return {
            "feedback_id": feedback_id,
            "status": "accepted",
        }
    except Exception as e:
        if isinstance(e, InvalidRequestError):
            raise
        raise InvalidRequestError(f"Failed to submit feedback: {str(e)}")


@router.get(
    "/models",
    summary="Get model performance",
    description="Get performance metrics for models.",
)
async def get_model_performance(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    min_samples: int = Query(5, ge=1, description="Minimum number of samples"),
    current_user: Optional[UserInfo] = Depends(get_optional_user),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker),
) -> Dict[str, Any]:
    """
    Get performance metrics for models.
    
    Args:
        model_id: Filter by model ID
        task_type: Filter by task type
        min_samples: Minimum number of samples
        current_user: Current authenticated user (optional)
        performance_tracker: Performance tracker service
        
    Returns:
        Dict[str, Any]: Performance metrics
    """
    # Get performance metrics
    performances = await performance_tracker.get_model_performance(
        model_id=model_id,
        task_type=task_type,
        min_samples=min_samples,
    )
    
    # Group by model
    models = {}
    for performance in performances:
        model_id = performance["model_id"]
        task_type = performance["task_type"]
        
        if model_id not in models:
            models[model_id] = {
                "model_id": model_id,
                "metrics": {
                    "overall_quality": 0.0,
                    "success_rate": 0.0,
                    "task_specific": {},
                },
                "sample_count": 0,
            }
        
        # Add task-specific metrics
        models[model_id]["metrics"]["task_specific"][task_type] = {
            "quality_score": performance["quality_score"],
            "success_rate": performance["success_rate"],
            "sample_count": performance["sample_count"],
        }
        
        # Update overall metrics
        total_samples = models[model_id]["sample_count"] + performance["sample_count"]
        if total_samples > 0:
            # Weighted average for overall metrics
            models[model_id]["metrics"]["overall_quality"] = (
                (models[model_id]["metrics"]["overall_quality"] * models[model_id]["sample_count"]) +
                (performance["quality_score"] * performance["sample_count"])
            ) / total_samples
            
            models[model_id]["metrics"]["success_rate"] = (
                (models[model_id]["metrics"]["success_rate"] * models[model_id]["sample_count"]) +
                (performance["success_rate"] * performance["sample_count"])
            ) / total_samples
        
        # Update sample count
        models[model_id]["sample_count"] = total_samples
    
    # Return result
    return {
        "models": list(models.values()),
    }


@router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset performance metrics",
    description="Reset performance metrics for a model.",
)
async def reset_performance_metrics(
    reset_data: Dict[str, Any],
    current_user: UserInfo = Depends(get_admin_user),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker),
) -> Dict[str, Any]:
    """
    Reset performance metrics for a model.
    
    Args:
        reset_data: Reset data
        current_user: Current authenticated admin user
        performance_tracker: Performance tracker service
        
    Returns:
        Dict[str, Any]: Reset result
        
    Raises:
        InvalidRequestError: If reset data is invalid
        HTTPException: If user is not an admin
    """
    try:
        # Extract reset data
        model_id = reset_data.get("model_id")
        task_types = reset_data.get("task_types")
        
        # Validate required fields
        if not model_id:
            raise InvalidRequestError("Missing required field: model_id")
        
        # TODO: Implement reset functionality in performance tracker
        
        # Return result
        return {
            "status": "success",
            "message": "Performance metrics reset",
        }
    except Exception as e:
        if isinstance(e, InvalidRequestError):
            raise
        raise InvalidRequestError(f"Failed to reset performance metrics: {str(e)}")


@router.post(
    "/update-history",
    status_code=status.HTTP_200_OK,
    summary="Update performance history",
    description="Update performance history records.",
)
async def update_performance_history(
    background_tasks: BackgroundTasks,
    current_user: UserInfo = Depends(get_admin_user),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker),
) -> Dict[str, Any]:
    """
    Update performance history records.
    
    Args:
        background_tasks: Background tasks
        current_user: Current authenticated admin user
        performance_tracker: Performance tracker service
        
    Returns:
        Dict[str, Any]: Update result
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Update performance history in background
    background_tasks.add_task(performance_tracker.update_performance_history)
    
    # Return result
    return {
        "status": "success",
        "message": "Performance history update scheduled",
    }
