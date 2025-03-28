import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
from logging.handlers import RotatingFileHandler

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # "json" or "text"
LOG_DIR = os.getenv("LOG_DIR", "logs")
SERVICE_NAME = os.getenv("SERVICE_NAME", "mas-framework")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
LOG_FILE = os.path.join(LOG_DIR, f"{SERVICE_NAME}.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, f"{SERVICE_NAME}-error.log")

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class JsonFormatter(logging.Formatter):
    """
    Formatter for JSON logs.
    """
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "service": SERVICE_NAME,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
            
        # Add extra fields if available
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        return json.dumps(log_data)


def setup_logging(
    service_name: Optional[str] = None,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_dir: Optional[str] = None,
) -> None:
    """
    Set up logging configuration.
    
    Args:
        service_name: Name of the service
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        log_dir: Directory for log files
    """
    global SERVICE_NAME, LOG_LEVEL, LOG_FORMAT, LOG_DIR, LOG_FILE, ERROR_LOG_FILE
    
    # Update configuration if provided
    if service_name:
        SERVICE_NAME = service_name
    if log_level:
        LOG_LEVEL = log_level.upper()
    if log_format:
        LOG_FORMAT = log_format.lower()
    if log_dir:
        LOG_DIR = log_dir
        os.makedirs(LOG_DIR, exist_ok=True)
        LOG_FILE = os.path.join(LOG_DIR, f"{SERVICE_NAME}.log")
        ERROR_LOG_FILE = os.path.join(LOG_DIR, f"{SERVICE_NAME}-error.log")
    
    # Get log level
    level = LOG_LEVELS.get(LOG_LEVEL, logging.INFO)
    
    # Create formatters
    if LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # File handler for error logs
    error_file_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)
    
    # Log configuration
    root_logger.info(
        f"Logging configured: level={LOG_LEVEL}, format={LOG_FORMAT}, "
        f"service={SERVICE_NAME}, log_dir={LOG_DIR}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding extra context to logs.
    """
    def process(self, msg, kwargs):
        # Ensure extra is in kwargs
        if "extra" not in kwargs:
            kwargs["extra"] = {}
            
        # Add adapter extra to kwargs extra
        kwargs["extra"].update(self.extra)
        
        return msg, kwargs


def get_logger_with_context(name: str, context: Dict[str, Any]) -> LoggerAdapter:
    """
    Get a logger with additional context.
    
    Args:
        name: Logger name
        context: Additional context to include in logs
        
    Returns:
        LoggerAdapter: Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, {"extra": context})


# Set up logging on module import
setup_logging()
