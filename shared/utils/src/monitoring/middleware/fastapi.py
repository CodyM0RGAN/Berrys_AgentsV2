"""
FastAPI middleware for the Berrys_AgentsV2 monitoring system.

This module provides middleware for integrating the monitoring system with
FastAPI applications, including request tracking, metrics collection, and
distributed tracing.

Usage:
    from fastapi import FastAPI
    from shared.utils.src.monitoring.middleware.fastapi import (
        setup_monitoring,
        MetricsMiddleware,
        TracingMiddleware,
        LoggingMiddleware,
    )

    app = FastAPI()
    
    # Setup all monitoring in one call
    setup_monitoring(app, service_name="api-gateway")
    
    # Or add middleware individually
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(LoggingMiddleware, service_name="api-gateway")
"""

import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Union, cast

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response as StarletteResponse

from shared.utils.src.monitoring.metrics import increment_counter, histogram
from shared.utils.src.monitoring.logging import get_logger, add_request_context
from shared.utils.src.monitoring.tracing import (
    tracer,
    extract_context_from_headers,
    inject_context_into_headers,
    SpanKind,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting metrics about requests and responses.
    """
    
    def __init__(
        self,
        app: FastAPI,
        service_name: str = "unknown",
        exclude_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            service_name: The name of the service
            exclude_paths: Paths to exclude from metrics collection
        """
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = exclude_paths or ["/metrics", "/health"]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        """
        Process the request and collect metrics.
        
        Args:
            request: The HTTP request
            call_next: The next middleware in the chain
            
        Returns:
            The HTTP response
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get the route path for metrics tagging
        route_path = request.url.path
        for route in request.app.routes:
            if route.path_regex.match(request.url.path):
                route_path = route.path
                break
        
        # Create tags for metrics
        tags = {
            "service": self.service_name,
            "method": request.method,
            "path": route_path,
        }
        
        # Start timing
        start_time = time.time()
        
        # Increment request counter
        increment_counter("http_requests_total", tags)
        
        # Process the request
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Create tags with response status
        tags["status"] = str(response.status_code)
        
        # Record request duration
        histogram("http_request_duration_seconds", duration, tags)
        
        # Record response size if available
        if hasattr(response, "headers") and "content-length" in response.headers:
            content_length = int(response.headers["content-length"])
            histogram("http_response_size_bytes", content_length, tags)
        
        return response


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for distributed tracing of requests.
    """
    
    def __init__(
        self,
        app: FastAPI,
        service_name: str = "unknown",
        exclude_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            service_name: The name of the service
            exclude_paths: Paths to exclude from tracing
        """
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = exclude_paths or ["/metrics", "/health"]
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        """
        Process the request and create a trace span.
        
        Args:
            request: The HTTP request
            call_next: The next middleware in the chain
            
        Returns:
            The HTTP response
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract trace context from headers
        trace_context = extract_context_from_headers(dict(request.headers))
        
        # Get the route path for tracing
        route_path = request.url.path
        for route in request.app.routes:
            if route.path_regex.match(request.url.path):
                route_path = route.path
                break
        
        # Create a span for this request
        with tracer.start_as_current_span(
            f"{request.method} {route_path}",
            kind=SpanKind.SERVER,
            attributes={
                "service.name": self.service_name,
                "http.method": request.method,
                "http.url": str(request.url),
                "http.path": route_path,
                "http.host": request.headers.get("host", ""),
                "http.user_agent": request.headers.get("user-agent", ""),
            },
        ) as span:
            # Add trace context to response headers
            response = await call_next(request)
            
            if hasattr(response, "headers"):
                # Modify headers directly instead of replacing the entire headers object
                for key, value in inject_context_into_headers(dict(response.headers)).items():
                    response.headers[key] = value
            
            # Add response attributes to span
            span.set_attribute("http.status_code", str(response.status_code))
            
            return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging of requests and responses.
    """
    
    def __init__(
        self,
        app: FastAPI,
        service_name: str = "unknown",
        exclude_paths: Optional[List[str]] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ):
        """
        Initialize the middleware.
        
        Args:
            app: The FastAPI application
            service_name: The name of the service
            exclude_paths: Paths to exclude from logging
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
        """
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = exclude_paths or ["/metrics", "/health"]
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.logger = get_logger(f"{service_name}.request")
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StarletteResponse:
        """
        Process the request and log information about it.
        
        Args:
            request: The HTTP request
            call_next: The next middleware in the chain
            
        Returns:
            The HTTP response
        """
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate a request ID if not provided
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Get client information
        client_host = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else "unknown"
        
        # Create request context for logging
        request_context = {
            "request_id": request_id,
            "service": self.service_name,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client": f"{client_host}:{client_port}",
            "user_agent": request.headers.get("user-agent", ""),
        }
        
        # Add request context to logger
        request_logger = add_request_context(self.logger, request_context)
        
        # Log request start
        request_logger.info(f"Request started: {request.method} {request.url.path}")
        
        # Log request body if enabled
        if self.log_request_body:
            try:
                body = await request.body()
                if body:
                    request_logger.debug(f"Request body: {body.decode('utf-8')}")
            except Exception as e:
                request_logger.warning(f"Failed to log request body: {str(e)}")
        
        # Start timing
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Update request context with response information
            request_context["status_code"] = response.status_code
            request_context["duration"] = f"{duration:.3f}s"
            
            # Add response headers to request context if useful
            if "content-length" in response.headers:
                request_context["content_length"] = response.headers["content-length"]
            
            # Add request ID to response headers
            if hasattr(response, "headers"):
                response.headers["X-Request-ID"] = request_id
            
            # Update logger with response context
            response_logger = add_request_context(self.logger, request_context)
            
            # Log response
            response_logger.info(
                f"Request completed: {request.method} {request.url.path} -> {response.status_code} in {duration:.3f}s"
            )
            
            # Log response body if enabled
            if self.log_response_body and hasattr(response, "body"):
                try:
                    response_logger.debug(f"Response body: {response.body.decode('utf-8')}")
                except Exception as e:
                    response_logger.warning(f"Failed to log response body: {str(e)}")
            
            return response
        except Exception as e:
            # Calculate request duration
            duration = time.time() - start_time
            
            # Update request context with error information
            request_context["status_code"] = 500
            request_context["duration"] = f"{duration:.3f}s"
            request_context["error"] = str(e)
            
            # Update logger with error context
            error_logger = add_request_context(self.logger, request_context)
            
            # Log error
            error_logger.error(
                f"Request failed: {request.method} {request.url.path} -> 500 in {duration:.3f}s: {str(e)}",
                exc_info=True,
            )
            
            raise


def setup_monitoring(
    app: FastAPI,
    service_name: str,
    exclude_paths: Optional[List[str]] = None,
    log_request_body: bool = False,
    log_response_body: bool = False,
    enable_metrics: bool = True,
    enable_tracing: bool = True,
    enable_logging: bool = True,
) -> None:
    """
    Set up all monitoring middleware for a FastAPI application.
    
    Args:
        app: The FastAPI application
        service_name: The name of the service
        exclude_paths: Paths to exclude from monitoring
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        enable_metrics: Whether to enable metrics collection
        enable_tracing: Whether to enable distributed tracing
        enable_logging: Whether to enable structured logging
    """
    exclude_paths = exclude_paths or ["/metrics", "/health"]
    
    # Add middleware in reverse order (last added = executed first)
    if enable_logging:
        app.add_middleware(
            LoggingMiddleware,
            service_name=service_name,
            exclude_paths=exclude_paths,
            log_request_body=log_request_body,
            log_response_body=log_response_body,
        )
    
    if enable_tracing:
        app.add_middleware(
            TracingMiddleware,
            service_name=service_name,
            exclude_paths=exclude_paths,
        )
    
    if enable_metrics:
        app.add_middleware(
            MetricsMiddleware,
            service_name=service_name,
            exclude_paths=exclude_paths,
        )
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for the API."""
        from shared.utils.src.monitoring.health import check_health
        
        health_info = await check_health()
        status_code = 200 if health_info["status"] == "healthy" else 503
        
        return JSONResponse(
            content=health_info,
            status_code=status_code,
        )
    
    # Add metrics endpoint
    if enable_metrics:
        @app.get("/metrics")
        async def metrics():
            """Metrics endpoint for the API."""
            from shared.utils.src.monitoring.metrics import get_metrics
            
            return JSONResponse(content=get_metrics())
