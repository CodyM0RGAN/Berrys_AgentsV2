"""
Distributed tracing system for the Berrys_AgentsV2 platform.

This module provides functionality for distributed tracing across service boundaries
using OpenTelemetry. It allows tracking requests as they flow through the system,
measuring performance, and diagnosing issues.

Usage:
    from shared.utils.src.monitoring.tracing import trace, get_current_span

    # Trace a function
    @trace("process_request")
    def process_request(request_data):
        # Function implementation
        pass

    # Manually create and manage spans
    with tracer.start_as_current_span("operation_name") as span:
        span.set_attribute("key", "value")
        # Operation implementation
"""

import functools
import inspect
import logging
import os
import threading
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, cast, Union

# Configure basic logging
logger = logging.getLogger(__name__)

# Type definitions for function decorators
F = TypeVar('F', bound=Callable[..., Any])

# Thread-local storage for the current trace context
_trace_context = threading.local()


class SpanKind(Enum):
    """Types of spans in a trace."""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class Span:
    """
    Represents a span in a distributed trace.
    
    In a real implementation, this would be backed by OpenTelemetry or similar,
    but for now it's a simple placeholder that logs span events.
    """
    
    def __init__(
        self,
        name: str,
        parent_span: Optional["Span"] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a new span.
        
        Args:
            name: The name of the span
            parent_span: The parent span, if any
            kind: The kind of span
            attributes: Initial attributes for the span
        """
        self.name = name
        self.parent_span = parent_span
        self.kind = kind
        self.attributes: Dict[str, str] = attributes or {}
        self.events: list = []
        self.status: Optional[str] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.trace_id = getattr(parent_span, "trace_id", os.urandom(16).hex())
        self.span_id = os.urandom(8).hex()
        
        # Set the current span in thread-local storage
        self._prev_current_span = getattr(_trace_context, "current_span", None)
    
    def __enter__(self) -> "Span":
        """Start the span and return it."""
        _trace_context.current_span = self
        self.start_time = _current_time_micros()
        logger.debug(f"Started span: {self.name} (trace_id={self.trace_id}, span_id={self.span_id})")
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End the span and restore the previous current span."""
        self.end_time = _current_time_micros()
        
        if exc_type:
            self.set_status("ERROR", str(exc_val))
            self.record_exception(exc_val, exc_tb)
        else:
            self.set_status("OK")
        
        # Calculate duration in milliseconds
        duration = (self.end_time - self.start_time) / 1000 if self.start_time else 0
        
        logger.debug(
            f"Ended span: {self.name} (trace_id={self.trace_id}, span_id={self.span_id}, "
            f"duration={duration:.3f}ms, status={self.status})"
        )
        
        # Restore the previous current span
        if self._prev_current_span:
            _trace_context.current_span = self._prev_current_span
        else:
            delattr(_trace_context, "current_span")
    
    def set_attribute(self, key: str, value: str) -> None:
        """
        Set an attribute on the span.
        
        Args:
            key: The attribute key
            value: The attribute value
        """
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, str]] = None) -> None:
        """
        Add an event to the span.
        
        Args:
            name: The name of the event
            attributes: Attributes for the event
        """
        event = {
            "name": name,
            "timestamp": _current_time_micros(),
            "attributes": attributes or {}
        }
        self.events.append(event)
        logger.debug(f"Span event: {name} on {self.name} (trace_id={self.trace_id}, span_id={self.span_id})")
    
    def set_status(self, status: str, description: Optional[str] = None) -> None:
        """
        Set the status of the span.
        
        Args:
            status: The status code ("OK" or "ERROR")
            description: A description of the status
        """
        self.status = status
        if description:
            self.set_attribute("status.description", description)
    
    def record_exception(self, exception: Exception, traceback: Any = None) -> None:
        """
        Record an exception in the span.
        
        Args:
            exception: The exception to record
            traceback: The traceback, if available
        """
        attributes = {
            "exception.type": exception.__class__.__name__,
            "exception.message": str(exception)
        }
        if traceback:
            attributes["exception.traceback"] = str(traceback)
        
        self.add_event("exception", attributes)


class Tracer:
    """
    Tracer for creating and managing spans.
    
    In a real implementation, this would be backed by OpenTelemetry or similar,
    but for now it's a simple placeholder that creates Span objects.
    """
    
    def __init__(self, name: str):
        """
        Initialize a new tracer.
        
        Args:
            name: The name of the tracer
        """
        self.name = name
    
    def start_span(
        self,
        name: str,
        parent_span: Optional[Span] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Span:
        """
        Start a new span.
        
        Args:
            name: The name of the span
            parent_span: The parent span, if any
            kind: The kind of span
            attributes: Initial attributes for the span
            
        Returns:
            A new span
        """
        # If no parent span is provided, use the current span as the parent
        if parent_span is None:
            parent_span = get_current_span()
        
        return Span(name, parent_span, kind, attributes)
    
    def start_as_current_span(
        self,
        name: str,
        parent_span: Optional[Span] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Span:
        """
        Start a new span and set it as the current span.
        
        Args:
            name: The name of the span
            parent_span: The parent span, if any
            kind: The kind of span
            attributes: Initial attributes for the span
            
        Returns:
            A new span that is set as the current span
        """
        span = self.start_span(name, parent_span, kind, attributes)
        span.__enter__()
        return span


def _current_time_micros() -> float:
    """Get the current time in microseconds."""
    import time
    return time.time() * 1_000_000


# Create a global tracer
tracer = Tracer("berrys_agents")


def get_current_span() -> Optional[Span]:
    """
    Get the current span from the thread-local context.
    
    Returns:
        The current span, or None if there is no current span
    """
    return getattr(_trace_context, "current_span", None)


def trace(
    name: Optional[Union[str, Callable]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, str]] = None,
) -> Callable[[F], F]:
    """
    Decorator to trace a function.
    
    Usage:
        @trace
        def my_function():
            pass
            
        @trace("custom_name")
        def my_function():
            pass
            
        @trace("custom_name", kind=SpanKind.SERVER, attributes={"key": "value"})
        def my_function():
            pass
    
    Args:
        name: The name of the span (defaults to the function name)
        kind: The kind of span
        attributes: Initial attributes for the span
        
    Returns:
        A decorator function that traces the decorated function
    """
    # Handle case where decorator is used without parameters
    if callable(name):
        func = name
        name = func.__name__
        return trace(name)(func)
    
    def decorator(func: F) -> F:
        # Use the function name if no name is provided
        span_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Start a new span for this function
            with tracer.start_as_current_span(span_name, kind=kind, attributes=attributes) as span:
                # Add function arguments as span attributes if they are simple types
                if inspect.signature(func).parameters:
                    for i, arg in enumerate(args):
                        if isinstance(arg, (str, int, float, bool)):
                            span.set_attribute(f"arg{i}", str(arg))
                    
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            span.set_attribute(f"kwarg.{key}", str(value))
                
                # Call the function and capture the result
                return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def extract_context_from_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Extract trace context from HTTP headers.
    
    Args:
        headers: The HTTP headers
        
    Returns:
        A dictionary of trace context values
    """
    context = {}
    
    trace_id = headers.get("X-Trace-ID") or headers.get("traceparent", "").split("-")[1] if "traceparent" in headers else None
    
    if trace_id:
        context["trace_id"] = trace_id
    
    span_id = headers.get("X-Span-ID")
    if span_id:
        context["parent_span_id"] = span_id
    
    return context


def inject_context_into_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into HTTP headers.
    
    Args:
        headers: The HTTP headers to inject into
        
    Returns:
        The updated headers
    """
    current_span = get_current_span()
    if current_span:
        headers["X-Trace-ID"] = current_span.trace_id
        headers["X-Span-ID"] = current_span.span_id
    
    return headers


def create_trace_context(trace_id: Optional[str] = None, parent_span_id: Optional[str] = None) -> Dict[str, str]:
    """
    Create a new trace context or adopt an existing one.
    
    Args:
        trace_id: An existing trace ID to adopt, or None to create a new one
        parent_span_id: An existing parent span ID, or None
        
    Returns:
        A dictionary with trace context values
    """
    return {
        "trace_id": trace_id or os.urandom(16).hex(),
        "parent_span_id": parent_span_id
    }
