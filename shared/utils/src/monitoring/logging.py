"""
Logging configuration and utilities for Berrys_AgentsV2 platform.

This module provides standardized logging configuration and utilities for the
Berrys_AgentsV2 production environment. It implements structured JSON logging
with consistent formatting and context enrichment.
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler, SysLogHandler
from typing import Any, Dict, List, Optional, Type, Union, cast

# Define log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

class LogLevel(Enum):
    """Enum for log levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

# Define default logger name
DEFAULT_LOGGER_NAME = "berrys_agents"

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(
        self,
        service_name: str = "unknown",
        environment: str = "production",
        include_timestamp: bool = True
    ):
        """
        Initialize JSON formatter.
        
        Args:
            service_name: Name of the service
            environment: Deployment environment
            include_timestamp: Whether to include timestamp in log records
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON-formatted log record
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z" if self.include_timestamp else None,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "service": self.service_name,
            "environment": self.environment,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Add extra context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add any exception info
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": record.exc_text or logging.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            for key, value in record.extra.items():
                if key not in log_data:
                    log_data[key] = value
        
        return json.dumps(log_data)


class RequestContextFilter(logging.Filter):
    """Filter that adds request context to log records."""
    
    def __init__(self, request_id: Optional[str] = None):
        """
        Initialize request context filter.
        
        Args:
            request_id: Request ID to add to log records
        """
        super().__init__()
        self.request_id = request_id or str(uuid.uuid4())
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request context to log record.
        
        Args:
            record: Log record to filter
            
        Returns:
            bool: Always True (filter always passes)
        """
        record.request_id = self.request_id
        return True


class LoggerManager:
    """Manages loggers for the application."""
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    _default_config: Dict[str, Any] = {
        "level": INFO,
        "json_format": True,
        "service_name": DEFAULT_LOGGER_NAME,
        "environment": "production",
        "log_to_console": True,
        "log_to_file": False,
        "log_file_path": "logs/app.log",
        "log_file_max_size": 10 * 1024 * 1024,  # 10 MB
        "log_file_backup_count": 5,
        "log_to_syslog": False,
        "syslog_address": "/dev/log",
        "syslog_facility": SysLogHandler.LOG_USER
    }
    
    def __new__(cls):
        """Singleton pattern to ensure only one logger manager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize request context
            cls._instance._request_context = RequestContextFilter()
        return cls._instance
    
    def configure(self, **config) -> None:
        """
        Configure logging globally.
        
        Args:
            **config: Configuration options
        """
        # Merge config with defaults
        self._config = {**self._default_config, **config}
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self._config["level"])
        
        # Remove existing handlers to avoid duplicates
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        
        # Create handlers based on config
        handlers = []
        
        # Console handler
        if self._config["log_to_console"]:
            console_handler = logging.StreamHandler(sys.stdout)
            handlers.append(console_handler)
        
        # File handler
        if self._config["log_to_file"]:
            file_handler = RotatingFileHandler(
                self._config["log_file_path"],
                maxBytes=self._config["log_file_max_size"],
                backupCount=self._config["log_file_backup_count"]
            )
            handlers.append(file_handler)
        
        # Syslog handler
        if self._config["log_to_syslog"]:
            try:
                syslog_handler = SysLogHandler(
                    address=self._config["syslog_address"],
                    facility=self._config["syslog_facility"]
                )
                handlers.append(syslog_handler)
            except (FileNotFoundError, ConnectionRefusedError) as e:
                print(f"Failed to connect to syslog: {e}")
        
        # Configure handlers
        for handler in handlers:
            # Create formatter
            if self._config["json_format"]:
                formatter = JsonFormatter(
                    service_name=self._config["service_name"],
                    environment=self._config["environment"]
                )
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            handler.setFormatter(formatter)
            handler.addFilter(self._request_context)
            root_logger.addHandler(handler)
        
        self._configured = True
        
        # Log configuration
        root_logger.info(
            f"Logging configured",
            extra={
                "service": self._config["service_name"],
                "environment": self._config["environment"],
                "level": logging.getLevelName(self._config["level"])
            }
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        if not self._configured:
            self.configure()
        
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        
        return self._loggers[name]
    
    def set_request_id(self, request_id: str) -> None:
        """
        Set request ID for the current context.
        
        Args:
            request_id: Request ID
        """
        self._request_context.request_id = request_id


# Global logger manager instance
_logger_manager = LoggerManager()

# Convenience functions for global logger manager

def configure_logging(**config) -> None:
    """
    Configure logging globally.
    
    Args:
        **config: Configuration options
    """
    _logger_manager.configure(**config)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return _logger_manager.get_logger(name)

def set_request_id(request_id: str) -> None:
    """
    Set request ID for the current context.
    
    Args:
        request_id: Request ID
    """
    _logger_manager.set_request_id(request_id)


def add_request_context(logger: logging.Logger, context: Dict[str, Any]) -> logging.Logger:
    """
    Add request context to a logger.
    
    This function creates a new logger with the same name as the input logger,
    but with additional context that will be included in all log messages.
    
    Args:
        logger: The logger to add context to
        context: The context to add
        
    Returns:
        logging.Logger: A new logger with the added context
    """
    # Create a new logger with the same name
    new_logger = get_logger(logger.name)
    
    # Create a filter that adds the context to log records
    class ContextFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            # Add context to record
            if not hasattr(record, "extra"):
                record.extra = {}
            
            # Add context to extra
            for key, value in context.items():
                record.extra[key] = value
            
            return True
    
    # Add filter to all handlers
    for handler in new_logger.handlers:
        handler.addFilter(ContextFilter())
    
    return new_logger


# Usage with FastAPI example:
"""
from fastapi import FastAPI, Request, Response
import uvicorn
import uuid

from shared.utils.src.monitoring.logging import configure_logging, get_logger, set_request_id

# Configure logging
configure_logging(
    level="INFO",
    json_format=True,
    service_name="api-gateway",
    environment="production"
)

# Create logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI()

# Add middleware for request ID
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    # Generate request ID if not provided
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    
    # Set request ID for logging
    set_request_id(request_id)
    
    # Add request ID to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

@app.get("/")
async def root():
    logger.info("Handling request", extra={
        "endpoint": "/",
        "method": "GET"
    })
    return {"message": "Hello World"}
"""
