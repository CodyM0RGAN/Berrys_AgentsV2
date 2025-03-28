"""
Cross-Service Communication Example

This example demonstrates how to use the cross-service communication utilities
together in a service. It shows how to implement:

1. Request ID propagation
2. Standardized error handling
3. Retry mechanisms with exponential backoff
4. Circuit breaker pattern
5. Cache fallback for service unavailability

This is a simplified example of a service that fetches project data from another service.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import shared utilities
from shared.utils.src.request_id import (
    RequestIdMiddleware, 
    get_request_id, 
    propagate_request_id
)
from shared.utils.src.circuit_breaker import (
    CircuitBreaker, 
    CircuitBreakerOpenException,
    registry as circuit_breaker_registry
)
from shared.utils.src.retry import (
    retry_with_backoff, 
    RetryPolicy,
    MaxRetriesExceededError
)
from shared.utils.src.cache_fallback import (
    CacheFallback, 
    CacheStrategy
)
from shared.models.src.api.errors import (
    ErrorResponse,
    create_error_response,
    create_resource_not_found_response,
    create_service_unavailable_response
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Project Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIdMiddleware)

# Create circuit breakers
project_coordinator_cb = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30,
    name="project-coordinator"
)

# Create cache fallback
project_cache = CacheFallback(
    cache_key_prefix="project",
    ttl=3600,  # 1 hour
    strategy=CacheStrategy.STALE_WHILE_REVALIDATE
)

# Mock client for Project Coordinator service
class ProjectCoordinatorClient:
    """Mock client for Project Coordinator service."""
    
    BASE_URL = "http://project-coordinator:8000"
    
    async def get_project(self, project_id: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a project from the Project Coordinator service.
        
        Args:
            project_id: ID of the project to get
            request_id: Optional request ID for tracing
            
        Returns:
            Project data
            
        Raises:
            HTTPException: If the project is not found or the service is unavailable
        """
        # In a real implementation, this would make an HTTP request to the service
        # For this example, we'll simulate different responses
        
        # Simulate a 404 error for a specific project ID
        if project_id == "not-found":
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Simulate a 500 error for a specific project ID
        if project_id == "server-error":
            raise HTTPException(status_code=500, detail="Internal server error")
        
        # Simulate a timeout for a specific project ID
        if project_id == "timeout":
            await asyncio.sleep(5)  # Simulate a long-running request
            raise HTTPException(status_code=504, detail="Gateway timeout")
        
        # Return mock project data for other project IDs
        return {
            "id": project_id,
            "name": f"Project {project_id}",
            "description": f"Description for project {project_id}",
            "status": "ACTIVE",
            "owner_id": "user-123",
            "created_at": "2025-03-26T12:00:00Z",
            "updated_at": "2025-03-26T12:00:00Z"
        }

# Create client instance
project_coordinator_client = ProjectCoordinatorClient()

# Define service exceptions
class ServiceUnavailableError(Exception):
    """Exception raised when a service is unavailable."""
    pass

class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found."""
    pass

# Define service functions
async def get_project_from_coordinator(
    project_id: str, 
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a project from the Project Coordinator service with retry and circuit breaker.
    
    Args:
        project_id: ID of the project to get
        request_id: Optional request ID for tracing
        
    Returns:
        Project data
        
    Raises:
        ResourceNotFoundError: If the project is not found
        ServiceUnavailableError: If the service is unavailable
        CircuitBreakerOpenException: If the circuit breaker is open
    """
    # Define retry policy
    retry_policy = RetryPolicy(
        max_retries=3,
        base_delay=0.5,
        max_delay=5.0,
        retry_exceptions=[HTTPException],
        retry_on_result=lambda result: result.get("status") == "ERROR"
    )
    
    # Define the operation to execute with retry and circuit breaker
    async def operation():
        try:
            return await project_coordinator_client.get_project(
                project_id=project_id,
                request_id=request_id
            )
        except HTTPException as e:
            if e.status_code == 404:
                raise ResourceNotFoundError(f"Project {project_id} not found")
            elif e.status_code >= 500:
                raise ServiceUnavailableError(f"Project Coordinator service unavailable: {str(e)}")
            raise
    
    try:
        # Execute with retry and circuit breaker
        return await project_coordinator_cb.execute(
            lambda: retry_with_backoff(
                operation=operation,
                policy=retry_policy,
                request_id=request_id,
                operation_name=f"get_project_{project_id}"
            )
        )
    except MaxRetriesExceededError as e:
        logger.error(
            f"Max retries exceeded for project {project_id}",
            extra={"request_id": request_id, "attempts": e.attempts}
        )
        raise ServiceUnavailableError(f"Failed to get project after {e.attempts} attempts")
    except ResourceNotFoundError:
        # Re-raise resource not found errors
        raise
    except Exception as e:
        logger.error(
            f"Error getting project {project_id}: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise ServiceUnavailableError(f"Failed to get project: {str(e)}")

async def get_project_with_fallback(
    project_id: str, 
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a project with fallback to cache if the service is unavailable.
    
    Args:
        project_id: ID of the project to get
        request_id: Optional request ID for tracing
        
    Returns:
        Project data
        
    Raises:
        ResourceNotFoundError: If the project is not found and not in cache
        ServiceUnavailableError: If the service is unavailable and not in cache
    """
    cache_key = f"project:{project_id}"
    log_context = {"request_id": request_id, "project_id": project_id}
    
    try:
        # Try to get from cache or service
        project, from_cache = await project_cache.get_or_fetch(
            cache_key=cache_key,
            fetch_func=lambda: get_project_from_coordinator(project_id, request_id),
            request_id=request_id
        )
        
        if from_cache:
            logger.info(f"Retrieved project {project_id} from cache", extra=log_context)
        else:
            logger.info(f"Retrieved project {project_id} from service", extra=log_context)
            
        return project
    except ResourceNotFoundError:
        # Check if we have a cached version
        cached_project = await project_cache.get(cache_key)
        if cached_project:
            logger.warning(
                f"Project {project_id} not found in service but found in cache",
                extra=log_context
            )
            return cached_project
        
        # No cached version, re-raise the exception
        logger.error(f"Project {project_id} not found", extra=log_context)
        raise
    except (ServiceUnavailableError, CircuitBreakerOpenException) as e:
        # Service is unavailable, try to get from cache
        cached_project = await project_cache.get(cache_key)
        
        if cached_project:
            logger.warning(
                f"Service unavailable, using cached project {project_id}",
                extra=log_context
            )
            return cached_project
            
        # No cached data available
        logger.error(
            f"Service unavailable and no cached data for project {project_id}",
            extra=log_context
        )
        raise ServiceUnavailableError(f"Project service unavailable and no cached data available")

# Define API endpoints
@app.get("/projects/{project_id}")
async def get_project(project_id: str, request: Request):
    """
    Get a project by ID.
    
    Args:
        project_id: ID of the project to get
        request: FastAPI request object
        
    Returns:
        Project data
    """
    request_id = get_request_id(request)
    log_context = {"request_id": request_id, "project_id": project_id}
    
    try:
        # Get project with fallback
        project = await get_project_with_fallback(project_id, request_id)
        return project
    except ResourceNotFoundError:
        # Return 404 response
        error_response = create_resource_not_found_response(
            resource_type="Project",
            resource_id=project_id,
            request_id=request_id
        )
        return JSONResponse(status_code=404, content=error_response)
    except ServiceUnavailableError as e:
        # Return 503 response
        error_response = create_service_unavailable_response(
            service_name="Project Coordinator",
            message=str(e),
            request_id=request_id
        )
        return JSONResponse(status_code=503, content=error_response)
    except Exception as e:
        # Return 500 response
        logger.error(f"Unexpected error: {str(e)}", extra=log_context, exc_info=True)
        error_response = create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"error": str(e)},
            request_id=request_id
        )
        return JSONResponse(status_code=500, content=error_response)

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Add circuit breaker status endpoint
@app.get("/circuit-breakers")
async def circuit_breaker_status():
    """Get status of all circuit breakers."""
    return circuit_breaker_registry.get_all_metrics()

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
