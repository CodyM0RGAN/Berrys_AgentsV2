"""
Error handling utilities for the Berrys_AgentsV2 project.

This module provides utilities for handling and logging errors.
"""

import logging
import os
import traceback
import functools
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Callable, Dict, Any, Type, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'errors_{datetime.now().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('error_handling')

class AppError(Exception):
    """Base class for application errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)

class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)

class DatabaseError(AppError):
    """Database error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)

class AuthenticationError(AppError):
    """Authentication error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)

class AuthorizationError(AppError):
    """Authorization error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)

def setup_error_handlers(app: FastAPI) -> None:
    """
    Set up error handlers for a FastAPI application.
    
    Args:
        app: FastAPI application
    """
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                'loc': error['loc'],
                'msg': error['msg'],
                'type': error['type']
            })
        
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                'detail': 'Validation error',
                'errors': errors
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """Handle SQLAlchemy errors."""
        error_message = str(exc)
        logger.error(f"Database error: {error_message}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'detail': 'Database error',
                'message': error_message
            }
        )
    
    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError):
        """Handle application errors."""
        logger.error(f"Application error: {exc.message}")
        logger.error(f"Details: {exc.details}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                'detail': exc.message,
                'details': exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle generic exceptions."""
        error_message = str(exc)
        logger.error(f"Unhandled exception: {error_message}")
        logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'detail': 'Internal server error',
                'message': error_message
            }
        )

def log_exceptions(func: Callable) -> Callable:
    """
    Decorator to log exceptions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    return wrapper

def handle_exceptions(error_map: Dict[Type[Exception], Callable[[Exception], AppError]]) -> Callable:
    """
    Decorator to handle exceptions.
    
    Args:
        error_map: Mapping from exception types to handler functions
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                for exc_type, handler in error_map.items():
                    if isinstance(e, exc_type):
                        app_error = handler(e)
                        logger.error(f"Handled exception in {func.__name__}: {app_error.message}")
                        logger.error(f"Details: {app_error.details}")
                        raise app_error
                
                # If no handler found, re-raise the exception
                logger.error(f"Unhandled exception in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        return wrapper
    
    return decorator
