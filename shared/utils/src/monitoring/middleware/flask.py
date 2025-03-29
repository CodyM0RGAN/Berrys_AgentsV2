"""
Flask middleware for the Berrys_AgentsV2 monitoring system.

This module provides middleware for integrating the monitoring system with
Flask applications, including request tracking, metrics collection, and
distributed tracing.

Usage:
    from flask import Flask
    from shared.utils.src.monitoring.middleware.flask import setup_monitoring

    app = Flask(__name__)
    
    # Setup all monitoring in one call
    setup_monitoring(app, service_name="web-dashboard")
"""

import time
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union, cast

from flask import Flask, Response, g, jsonify, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from shared.utils.src.monitoring.metrics import increment_counter, histogram
from shared.utils.src.monitoring.logging import get_logger, add_request_context
from shared.utils.src.monitoring.tracing import (
    tracer,
    extract_context_from_headers,
    inject_context_into_headers,
    SpanKind,
)
from shared.utils.src.monitoring.health import check_health


def _metrics_middleware():
    """Return metrics as JSON."""
    from shared.utils.src.monitoring.metrics import get_metrics
    return jsonify(get_metrics())


def _health_middleware():
    """Return health check as JSON."""
    health_info = check_health()
    status_code = 200 if health_info["status"] == "healthy" else 503
    return jsonify(health_info), status_code


def setup_monitoring(
    app: Flask,
    service_name: str,
    exclude_paths: Optional[List[str]] = None,
    log_request_body: bool = False,
    log_response_body: bool = False,
    enable_metrics: bool = True,
    enable_tracing: bool = True,
    enable_logging: bool = True,
) -> None:
    """
    Set up monitoring for a Flask application.
    
    Args:
        app: The Flask application
        service_name: The name of the service
        exclude_paths: Paths to exclude from monitoring
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        enable_metrics: Whether to enable metrics collection
        enable_tracing: Whether to enable distributed tracing
        enable_logging: Whether to enable structured logging
    """
    exclude_paths = exclude_paths or ["/metrics", "/health"]
    logger = get_logger(f"{service_name}.request")
    
    # Add middleware endpoints
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        "/metrics": _metrics_middleware,
        "/health": _health_middleware,
    })
    
    @app.before_request
    def before_request():
        """Set up request context and start timing."""
        # Skip excluded paths
        if request.path in exclude_paths:
            return
        
        # Store request start time
        g.start_time = time.time()
        
        # Generate a request ID if not provided
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Create request context for logging
        request_context = {
            "request_id": g.request_id,
            "service": service_name,
            "method": request.method,
            "path": request.path,
            "query": request.query_string.decode("utf-8"),
            "client": request.remote_addr,
            "user_agent": request.user_agent.string if request.user_agent else "",
        }
        
        # Store request context
        g.request_context = request_context
        
        # Configure request-specific logger
        if enable_logging:
            request_logger = add_request_context(logger, request_context)
            g.logger = request_logger
            
            # Log request start
            request_logger.info(f"Request started: {request.method} {request.path}")
            
            # Log request body if enabled
            if log_request_body and request.content_length:
                try:
                    request_logger.debug(f"Request body: {request.get_data(as_text=True)}")
                except Exception as e:
                    request_logger.warning(f"Failed to log request body: {str(e)}")
        
        # Start a trace span for this request
        if enable_tracing:
            # Extract trace context from headers
            trace_context = extract_context_from_headers(dict(request.headers))
            
            # Create a span for this request
            span = tracer.start_as_current_span(
                f"{request.method} {request.path}",
                kind=SpanKind.SERVER,
                attributes={
                    "service.name": service_name,
                    "http.method": request.method,
                    "http.url": request.url,
                    "http.path": request.path,
                    "http.host": request.host,
                    "http.user_agent": request.user_agent.string if request.user_agent else "",
                },
            )
            g.span = span
        
        # Increment request counter for metrics
        if enable_metrics:
            # Create tags for metrics
            tags = {
                "service": service_name,
                "method": request.method,
                "path": request.path,
            }
            
            # Store tags for later use
            g.metric_tags = tags
            
            # Increment request counter
            increment_counter("http_requests_total", tags)
    
    @app.after_request
    def after_request(response: Response) -> Response:
        """Process response and collect metrics."""
        # Skip excluded paths
        if request.path in exclude_paths:
            return response
        
        # Add request ID header
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        
        # Add trace context to response headers
        if enable_tracing and hasattr(g, "span"):
            response.headers = inject_context_into_headers(dict(response.headers))
            
            # Add response attributes to span
            g.span.set_attribute("http.status_code", str(response.status_code))
            
            # End the span
            g.span.__exit__(None, None, None)
        
        # Process metrics
        if enable_metrics and hasattr(g, "metric_tags") and hasattr(g, "start_time"):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Create tags with response status
            tags = dict(g.metric_tags)
            tags["status"] = str(response.status_code)
            
            # Record request duration
            histogram("http_request_duration_seconds", duration, tags)
            
            # Record response size if available
            if response.content_length:
                histogram("http_response_size_bytes", response.content_length, tags)
        
        # Process logging
        if enable_logging and hasattr(g, "logger") and hasattr(g, "start_time") and hasattr(g, "request_context"):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Update request context with response information
            request_context = dict(g.request_context)
            request_context["status_code"] = response.status_code
            request_context["duration"] = f"{duration:.3f}s"
            
            # Add response headers to request context if useful
            if response.content_length:
                request_context["content_length"] = response.content_length
            
            # Update logger with response context
            response_logger = add_request_context(logger, request_context)
            
            # Log response
            response_logger.info(
                f"Request completed: {request.method} {request.path} -> {response.status_code} in {duration:.3f}s"
            )
            
            # Log response body if enabled
            if log_response_body and response.content_length:
                try:
                    response_data = response.get_data(as_text=True)
                    response_logger.debug(f"Response body: {response_data}")
                except Exception as e:
                    response_logger.warning(f"Failed to log response body: {str(e)}")
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """Handle exceptions and cleanup."""
        # Skip excluded paths
        if request and request.path in exclude_paths:
            return
        
        # Handle exceptions in the request
        if exception is not None and enable_logging and hasattr(g, "logger") and hasattr(g, "start_time") and hasattr(g, "request_context"):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Update request context with error information
            request_context = dict(g.request_context)
            request_context["status_code"] = 500
            request_context["duration"] = f"{duration:.3f}s"
            request_context["error"] = str(exception)
            
            # Update logger with error context
            error_logger = add_request_context(logger, request_context)
            
            # Log error
            error_logger.error(
                f"Request failed: {request.method} {request.path} -> 500 in {duration:.3f}s: {str(exception)}",
                exc_info=True,
            )
        
        # End tracing span if it wasn't ended in after_request (e.g., due to an exception)
        if enable_tracing and hasattr(g, "span") and g.span._prev_current_span is not None:
            # This means the span is still active
            g.span.set_status("ERROR", str(exception) if exception else None)
            g.span.__exit__(type(exception), exception, None if exception is None else exception.__traceback__)


def instrument_function(
    name: Optional[str] = None,
    service_name: str = "unknown",
    capture_args: bool = False,
):
    """
    Decorator to instrument a function with metrics, logging, and tracing.
    
    Args:
        name: The name of the function (defaults to the function name)
        service_name: The name of the service
        capture_args: Whether to capture function arguments in tracing
        
    Returns:
        The decorated function
    """
    def decorator(func):
        func_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create span attributes
            attributes = {
                "service.name": service_name,
                "function.name": func_name,
            }
            
            # Add function arguments if requested
            if capture_args:
                for i, arg in enumerate(args):
                    if isinstance(arg, (str, int, float, bool)):
                        attributes[f"arg{i}"] = str(arg)
                
                for key, value in kwargs.items():
                    if isinstance(value, (str, int, float, bool)):
                        attributes[f"kwarg.{key}"] = str(value)
            
            # Start timing
            start_time = time.time()
            
            # Start a span for this function
            with tracer.start_as_current_span(
                func_name,
                kind=SpanKind.INTERNAL,
                attributes=attributes,
            ) as span:
                try:
                    # Call the function
                    result = func(*args, **kwargs)
                    
                    # Record success metrics
                    tags = {
                        "service": service_name,
                        "function": func_name,
                        "status": "success",
                    }
                    
                    duration = time.time() - start_time
                    increment_counter("function_calls_total", tags)
                    histogram("function_duration_seconds", duration, tags)
                    
                    return result
                except Exception as e:
                    # Record error metrics
                    tags = {
                        "service": service_name,
                        "function": func_name,
                        "status": "error",
                        "error_type": e.__class__.__name__,
                    }
                    
                    duration = time.time() - start_time
                    increment_counter("function_calls_total", tags)
                    histogram("function_duration_seconds", duration, tags)
                    
                    # Set span status to error
                    span.set_status("ERROR", str(e))
                    span.record_exception(e)
                    
                    # Re-raise the exception
                    raise
        
        return wrapper
    
    return decorator
