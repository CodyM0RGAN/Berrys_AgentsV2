"""
Exception Handling Example

This example demonstrates how to use the shared exception hierarchy and exception
handling middleware in a FastAPI service. It shows how to:

1. Raise and handle different types of exceptions
2. Use the exception handling middleware
3. Convert exceptions to standardized error responses
4. Propagate request IDs through error responses

This is a simplified example of a service that manages users.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Depends, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import shared utilities
from shared.utils.src.request_id import RequestIdMiddleware, get_request_id
from shared.utils.src.exception_middleware import ExceptionHandlingMiddleware
from shared.utils.src.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ServiceUnavailableError,
    InternalServerError,
    BadRequestError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="User Service")

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

# Add exception handling middleware
app.add_middleware(ExceptionHandlingMiddleware)

# Mock user database
USERS = {
    "user-123": {
        "id": "user-123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "USER"
    },
    "user-456": {
        "id": "user-456",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "role": "ADMIN"
    }
}

# Mock authentication
def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get the current user from the request.
    
    Args:
        request: The incoming request
        
    Returns:
        The current user
        
    Raises:
        AuthenticationError: If the user is not authenticated
    """
    # In a real implementation, this would check the Authorization header
    # For this example, we'll use a query parameter
    user_id = request.query_params.get("user_id")
    
    if not user_id:
        raise AuthenticationError(
            message="Authentication required",
            details={"reason": "No user ID provided"}
        )
    
    if user_id not in USERS:
        raise AuthenticationError(
            message="Invalid user ID",
            details={"reason": "User not found"}
        )
    
    return USERS[user_id]

# Mock authorization
def require_admin(user: Dict[str, Any]) -> None:
    """
    Require the user to be an admin.
    
    Args:
        user: The current user
        
    Raises:
        AuthorizationError: If the user is not an admin
    """
    if user.get("role") != "ADMIN":
        raise AuthorizationError(
            message="Admin access required",
            details={"reason": "User is not an admin"}
        )

# API endpoints
@app.get("/users")
async def list_users(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List users.
    
    Args:
        request: The incoming request
        current_user: The current user
        limit: Maximum number of users to return
        offset: Number of users to skip
        
    Returns:
        List of users
    """
    # Validate query parameters
    if limit < 1 or limit > 100:
        raise ValidationError(
            message="Invalid limit parameter",
            validation_errors={"limit": "Must be between 1 and 100"}
        )
    
    if offset < 0:
        raise ValidationError(
            message="Invalid offset parameter",
            validation_errors={"offset": "Must be a non-negative integer"}
        )
    
    # Get users
    users = list(USERS.values())[offset:offset+limit]
    
    return {
        "users": users,
        "total": len(USERS),
        "limit": limit,
        "offset": offset
    }

@app.get("/users/{user_id}")
async def get_user(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a user by ID.
    
    Args:
        request: The incoming request
        user_id: ID of the user to get
        current_user: The current user
        
    Returns:
        User data
    """
    # Check if the user exists
    if user_id not in USERS:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=user_id
        )
    
    # Return the user
    return USERS[user_id]

@app.post("/users")
async def create_user(
    request: Request,
    user: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new user.
    
    Args:
        request: The incoming request
        user: User data
        current_user: The current user
        
    Returns:
        Created user
    """
    # Require admin access
    require_admin(current_user)
    
    # Validate user data
    validation_errors = {}
    
    if not user.get("name"):
        validation_errors["name"] = "Name is required"
    
    if not user.get("email"):
        validation_errors["email"] = "Email is required"
    elif "@" not in user.get("email", ""):
        validation_errors["email"] = "Invalid email format"
    
    if validation_errors:
        raise ValidationError(
            message="Invalid user data",
            validation_errors=validation_errors
        )
    
    # Check for duplicate email
    for existing_user in USERS.values():
        if existing_user["email"] == user["email"]:
            raise ConflictError(
                message="Email already exists",
                details={"email": user["email"]}
            )
    
    # Create the user
    user_id = f"user-{uuid4()}"
    new_user = {
        "id": user_id,
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "USER")
    }
    
    # Add to database
    USERS[user_id] = new_user
    
    return new_user

@app.put("/users/{user_id}")
async def update_user(
    request: Request,
    user_id: str,
    user: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a user.
    
    Args:
        request: The incoming request
        user_id: ID of the user to update
        user: Updated user data
        current_user: The current user
        
    Returns:
        Updated user
    """
    # Check if the user exists
    if user_id not in USERS:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=user_id
        )
    
    # Check if the current user is the user being updated or an admin
    if current_user["id"] != user_id and current_user.get("role") != "ADMIN":
        raise AuthorizationError(
            message="Permission denied",
            details={"reason": "You can only update your own user or be an admin"}
        )
    
    # Validate user data
    validation_errors = {}
    
    if "name" in user and not user["name"]:
        validation_errors["name"] = "Name cannot be empty"
    
    if "email" in user:
        if not user["email"]:
            validation_errors["email"] = "Email cannot be empty"
        elif "@" not in user["email"]:
            validation_errors["email"] = "Invalid email format"
    
    if validation_errors:
        raise ValidationError(
            message="Invalid user data",
            validation_errors=validation_errors
        )
    
    # Check for duplicate email
    if "email" in user:
        for existing_id, existing_user in USERS.items():
            if existing_id != user_id and existing_user["email"] == user["email"]:
                raise ConflictError(
                    message="Email already exists",
                    details={"email": user["email"]}
                )
    
    # Update the user
    updated_user = USERS[user_id].copy()
    
    if "name" in user:
        updated_user["name"] = user["name"]
    
    if "email" in user:
        updated_user["email"] = user["email"]
    
    if "role" in user and current_user.get("role") == "ADMIN":
        updated_user["role"] = user["role"]
    
    # Save to database
    USERS[user_id] = updated_user
    
    return updated_user

@app.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a user.
    
    Args:
        request: The incoming request
        user_id: ID of the user to delete
        current_user: The current user
        
    Returns:
        Success message
    """
    # Require admin access
    require_admin(current_user)
    
    # Check if the user exists
    if user_id not in USERS:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=user_id
        )
    
    # Delete the user
    del USERS[user_id]
    
    return {"message": f"User {user_id} deleted"}

@app.get("/admin/users")
async def admin_list_users(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Admin endpoint to list all users.
    
    Args:
        request: The incoming request
        current_user: The current user
        
    Returns:
        List of all users
    """
    # Require admin access
    require_admin(current_user)
    
    # Return all users
    return {"users": list(USERS.values())}

@app.get("/error-examples")
async def error_examples(
    request: Request,
    error_type: str = Query(..., description="Type of error to demonstrate")
):
    """
    Demonstrate different types of errors.
    
    Args:
        request: The incoming request
        error_type: Type of error to demonstrate
        
    Returns:
        Error response
    """
    if error_type == "validation":
        raise ValidationError(
            message="Validation error example",
            validation_errors={
                "field1": "Field 1 is required",
                "field2": "Field 2 must be a positive integer"
            }
        )
    elif error_type == "not_found":
        raise ResourceNotFoundError(
            resource_type="Resource",
            resource_id="123"
        )
    elif error_type == "authentication":
        raise AuthenticationError(
            message="Authentication error example",
            details={"reason": "Invalid credentials"}
        )
    elif error_type == "authorization":
        raise AuthorizationError(
            message="Authorization error example",
            details={"reason": "Insufficient permissions"}
        )
    elif error_type == "conflict":
        raise ConflictError(
            message="Conflict error example",
            details={"field": "Value already exists"}
        )
    elif error_type == "service_unavailable":
        raise ServiceUnavailableError(
            message="Service unavailable error example",
            service_name="Example Service"
        )
    elif error_type == "internal_server":
        raise InternalServerError(
            message="Internal server error example",
            details={"reason": "Something went wrong"}
        )
    elif error_type == "bad_request":
        raise BadRequestError(
            message="Bad request error example",
            details={"reason": "Invalid request"}
        )
    elif error_type == "unhandled":
        # This will be caught by the exception handling middleware
        raise Exception("Unhandled exception example")
    else:
        raise ValidationError(
            message="Invalid error type",
            validation_errors={"error_type": f"Unknown error type: {error_type}"}
        )

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
