"""
Request Mediator implementation.

This module implements the Mediator pattern for handling different types of
requests through registered handlers. It allows for loose coupling between
request senders and handlers.
"""
from typing import Dict, Any, Optional, List, Callable, Awaitable, TypeVar, Generic
import logging
import asyncio
from datetime import datetime

from ....exceptions import UnknownRequestTypeError
from ....models.api import ServiceInfo
from ..discovery.service import ServiceDiscovery

# Type definitions
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')
HandlerFunc = Callable[[TRequest], Awaitable[TResponse]]


class RequestMediator:
    """
    Request Mediator implementation.
    
    This class implements the Mediator pattern to decouple request senders
    from request handlers. It maintains a registry of handler functions for
    different request types and routes requests to the appropriate handler.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the request mediator.
        
        Args:
            service_discovery: Service discovery instance for finding services
            logger: Logger instance (optional)
        """
        self.service_discovery = service_discovery
        self.logger = logger or logging.getLogger("request_mediator")
        self.handlers: Dict[str, HandlerFunc] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    def register_handler(self, request_type: str, handler: HandlerFunc) -> None:
        """
        Register a handler for a specific request type.
        
        Args:
            request_type: Type of request (e.g., "workflow.agent_task_execution")
            handler: Async function that handles the request
        """
        self.logger.info(f"Registering handler for request type: {request_type}")
        self.handlers[request_type] = handler
        self.locks[request_type] = asyncio.Lock()
    
    def unregister_handler(self, request_type: str) -> bool:
        """
        Unregister a handler for a specific request type.
        
        Args:
            request_type: Type of request to unregister
            
        Returns:
            True if the handler was unregistered, False if not found
        """
        if request_type in self.handlers:
            self.logger.info(f"Unregistering handler for request type: {request_type}")
            del self.handlers[request_type]
            if request_type in self.locks:
                del self.locks[request_type]
            return True
        return False
    
    async def send(self, request_type: str, request: TRequest) -> TResponse:
        """
        Send a request to the appropriate handler.
        
        Args:
            request_type: Type of request
            request: Request data
            
        Returns:
            Response from the handler
            
        Raises:
            UnknownRequestTypeError: If no handler is registered for the request type
        """
        start_time = datetime.now()
        
        # Check if there's a handler for this request type
        if request_type not in self.handlers:
            self.logger.error(f"No handler registered for request type: {request_type}")
            raise UnknownRequestTypeError(f"Unknown request type: {request_type}")
        
        # Get the handler
        handler = self.handlers[request_type]
        lock = self.locks.get(request_type)
        
        try:
            # Process the request (with optional locking)
            self.logger.debug(f"Processing request type: {request_type}")
            
            if lock:
                async with lock:
                    response = await handler(request)
            else:
                response = await handler(request)
            
            # Calculate and log processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"Request {request_type} processed in {processing_time:.2f}ms")
            
            return response
            
        except UnknownRequestTypeError:
            raise
        except Exception as ex:
            self.logger.exception(f"Error processing request type: {request_type}")
            raise
    
    async def broadcast(self, event_type: str, event: Any) -> Dict[str, Any]:
        """
        Broadcast an event to all handlers with matching prefix.
        
        This is useful for notifying multiple handlers about an event.
        Handlers are identified by a prefix match on the event type.
        
        Args:
            event_type: Type of event (e.g., "event.service_registered")
            event: Event data
            
        Returns:
            Dictionary of handler names and their responses or errors
        """
        results = {}
        prefix = event_type.split('.')[0] + '.'
        matching_handlers = {name: handler for name, handler in self.handlers.items() if name.startswith(prefix)}
        
        if not matching_handlers:
            self.logger.warning(f"No handlers found for event type prefix: {prefix}")
            return results
        
        # Process in parallel
        tasks = []
        for name, handler in matching_handlers.items():
            self.logger.debug(f"Broadcasting event {event_type} to handler: {name}")
            task = asyncio.create_task(self._safe_call_handler(name, handler, event))
            tasks.append((name, task))
        
        # Collect results
        for name, task in tasks:
            try:
                result = await task
                results[name] = {"success": True, "result": result}
            except Exception as e:
                self.logger.error(f"Error in handler {name} processing event {event_type}: {str(e)}")
                results[name] = {"success": False, "error": str(e)}
        
        return results
    
    async def _safe_call_handler(self, name: str, handler: HandlerFunc, event: Any) -> Any:
        """Safely call a handler and return its result or raise an exception."""
        try:
            return await handler(event)
        except Exception as e:
            self.logger.error(f"Handler {name} raised an exception: {str(e)}")
            raise
