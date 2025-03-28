"""
Logging functionality.

This module contains the LoggingMixin class that provides methods for logging requests.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from ...models.internal import RequestModel

logger = logging.getLogger(__name__)


class LoggingMixin:
    """
    Mixin for logging operations.
    
    This mixin provides methods for:
    - Logging requests
    - Tracking performance metrics
    """
    
    async def log_request(
        self,
        request_id: str,
        request_type: str,
        model_id: str,
        provider: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        latency_ms: Optional[float] = None,
        cost: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """
        Log a request to the database.
        
        Args:
            request_id: Request ID
            request_type: Request type
            model_id: Model ID
            provider: Provider name
            user_id: User ID
            project_id: Project ID
            task_id: Task ID
            request_data: Request data
            response_data: Response data
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total number of tokens
            latency_ms: Latency in milliseconds
            cost: Cost in USD
            success: Whether the request was successful
            error_message: Error message
            error_code: Error code
        """
        try:
            # Extract token counts from response data if not provided
            if response_data and "usage" in response_data and not prompt_tokens:
                usage = response_data["usage"]
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")
            
            # Calculate total tokens if not provided
            if prompt_tokens and completion_tokens and not total_tokens:
                total_tokens = prompt_tokens + completion_tokens
            
            # Create request model
            request_model = RequestModel(
                request_id=request_id,
                request_type=request_type,
                model_id=model_id,
                provider=provider,
                user_id=user_id,
                project_id=project_id,
                task_id=task_id,
                request_data=request_data,
                response_data=response_data,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                cost=cost,
                success=success,
                error_message=error_message,
                error_code=error_code,
                completed_at=datetime.utcnow(),
            )
            
            # Add to database
            self.db.add(request_model)
            await self.db.commit()
            
            # Publish event
            if success:
                await self.event_bus.publish_event(
                    "model.request.completed",
                    {
                        "request_id": request_id,
                        "model_id": model_id,
                        "provider": provider,
                        "tokens": total_tokens,
                        "latency_ms": latency_ms,
                        "cost": cost,
                    }
                )
            else:
                await self.event_bus.publish_event(
                    "model.request.failed",
                    {
                        "request_id": request_id,
                        "model_id": model_id,
                        "provider": provider,
                        "error": {
                            "message": error_message,
                            "code": error_code,
                        },
                    }
                )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error logging request: {str(e)}")
