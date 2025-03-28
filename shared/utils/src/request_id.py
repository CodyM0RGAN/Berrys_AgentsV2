"""
Request ID middleware for consistent request tracking across services.

This module provides middleware for FastAPI and Flask applications to ensure
consistent request tracking across services. It generates a unique request ID
for each incoming request, propagates it through service calls, and includes
it in all log messages.
"""
import logging
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

# Set up logger
logger = logging.getLogger(__name__)

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# Header name for request ID
REQUEST_ID_HEADER = 'X-Request-ID'


def get_request_id(request: Optional[Request] = None) -> str:
    """
    Get the current request ID.
    
    Args:
        request: FastAPI request object (optional)
        
    Returns:
        Request ID
    """
    # If request is provided, try to get request ID from it
    if request and hasattr(request, 'state') and hasattr(request.state, 'request_id'):
        return request.state.request_id
    
    # Otherwise, get from context variable
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """
    Set the current request ID.
    
    Args:
        request_id: Request ID
    """
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """
    Generate a new request ID.
    
    Returns:
        Request ID
    """
    return str(uuid.uuid4())


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for request ID handling.
    
    This middleware:
    1. Extracts the request ID from the request headers if present
    2. Generates a new request ID if not present
    3. Sets the request ID in the request state
    4. Sets the request ID in the context variable
    5. Adds the request ID to the response headers
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize RequestIdMiddleware.
        
        Args:
            app: FastAPI application
        """
        super().__init__(app)
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware or endpoint
            
        Returns:
            FastAPI response
        """
        # Extract request ID from headers or generate a new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = generate_request_id()
            logger.debug(f"Generated new request ID: {request_id}")
        else:
            logger.debug(f"Using existing request ID: {request_id}")
        
        # Set request ID in request state
        request.state.request_id = request_id
        
        # Set request ID in context variable
        token = request_id_var.set(request_id)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers[REQUEST_ID_HEADER] = request_id
            
            return response
        finally:
            # Reset context variable
            request_id_var.reset(token)


class FlaskRequestIdMiddleware:
    """
    Flask middleware for request ID handling.
    
    This middleware:
    1. Extracts the request ID from the request headers if present
    2. Generates a new request ID if not present
    3. Sets the request ID in the Flask g object
    4. Sets the request ID in the context variable
    5. Adds the request ID to the response headers
    """
    
    def __init__(self, app):
        """
        Initialize FlaskRequestIdMiddleware.
        
        Args:
            app: Flask application
        """
        self.app = app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
    
    def before_request(self):
        """Process the request before the view function."""
        from flask import request, g
        
        # Extract request ID from headers or generate a new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = generate_request_id()
            logger.debug(f"Generated new request ID: {request_id}")
        else:
            logger.debug(f"Using existing request ID: {request_id}")
        
        # Set request ID in Flask g object
        g.request_id = request_id
        
        # Set request ID in context variable
        set_request_id(request_id)
    
    def after_request(self, response):
        """Process the response after the view function."""
        from flask import g
        
        # Add request ID to response headers
        if hasattr(g, 'request_id'):
            response.headers[REQUEST_ID_HEADER] = g.request_id
        
        return response


class RequestIdFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records.
    
    This filter adds the current request ID to log records, making it easier
    to trace requests across services.
    """
    
    def filter(self, record):
        """
        Add request ID to log record.
        
        Args:
            record: Log record
            
        Returns:
            True (always include the record)
        """
        record.request_id = get_request_id()
        return True


def setup_request_id_logging():
    """
    Set up logging to include request ID.
    
    This function adds a filter to the root logger that adds the current
    request ID to all log records.
    """
    root_logger = logging.getLogger()
    root_logger.addFilter(RequestIdFilter())


def add_request_id_middleware(app: Union[FastAPI, Any]) -> None:
    """
    Add request ID middleware to a FastAPI or Flask application.
    
    Args:
        app: FastAPI or Flask application
    """
    if isinstance(app, FastAPI):
        # FastAPI application
        app.add_middleware(RequestIdMiddleware)
        logger.info("Added RequestIdMiddleware to FastAPI application")
    else:
        # Assume Flask application
        FlaskRequestIdMiddleware(app)
        logger.info("Added FlaskRequestIdMiddleware to Flask application")
    
    # Set up logging
    setup_request_id_logging()
    logger.info("Set up request ID logging")


def get_request_id_header(request_id: Optional[str] = None) -> Dict[str, str]:
    """
    Get request ID header for outgoing requests.
    
    Args:
        request_id: Request ID (optional, defaults to current request ID)
        
    Returns:
        Dictionary with request ID header
    """
    if request_id is None:
        request_id = get_request_id()
    
    return {REQUEST_ID_HEADER: request_id}
