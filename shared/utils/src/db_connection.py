"""
Database connection utility for multi-environment setup.

This module provides functions to select the appropriate database connection string
based on the environment (development, test, production).
"""
import os
from typing import Optional


def get_environment() -> str:
    """
    Get the current environment from the ENVIRONMENT environment variable.
    
    Returns:
        str: The current environment (DEVELOPMENT, TEST, PRODUCTION)
    """
    return os.environ.get("ENVIRONMENT", "DEVELOPMENT").upper()


def get_database_name() -> str:
    """
    Get the database name based on the current environment.
    
    Returns:
        str: The database name for the current environment
    """
    env = get_environment()
    
    if env == "PRODUCTION":
        return "mas_framework_prod"
    elif env == "TEST":
        return "mas_framework_test"
    else:  # DEVELOPMENT is the default
        return "mas_framework_dev"


def get_async_database_url(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
) -> str:
    """
    Get the async database URL for the current environment.
    
    Args:
        user (Optional[str]): Database user
        password (Optional[str]): Database password
        host (Optional[str]): Database host
        port (Optional[str]): Database port
        
    Returns:
        str: The async database URL for the current environment
    """
    # Check if ASYNC_DATABASE_URL is set in environment variables
    if "ASYNC_DATABASE_URL" in os.environ:
        return os.environ["ASYNC_DATABASE_URL"]
    
    # Get values from environment variables if not provided
    user = user or os.environ.get("DB_USER", "postgres")
    password = password or os.environ.get("DB_PASSWORD", "postgres")
    host = host or os.environ.get("DB_HOST", "postgres")
    port = port or os.environ.get("DB_PORT", "5432")
    
    # Get database name based on environment
    db_name = get_database_name()
    
    # Construct and return the URL
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}"


def get_sync_database_url(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
) -> str:
    """
    Get the sync database URL for the current environment.
    
    Args:
        user (Optional[str]): Database user
        password (Optional[str]): Database password
        host (Optional[str]): Database host
        port (Optional[str]): Database port
        
    Returns:
        str: The sync database URL for the current environment
    """
    # Check if SYNC_DATABASE_URL is set in environment variables
    if "SYNC_DATABASE_URL" in os.environ:
        return os.environ["SYNC_DATABASE_URL"]
    
    # Get values from environment variables if not provided
    user = user or os.environ.get("DB_USER", "postgres")
    password = password or os.environ.get("DB_PASSWORD", "postgres")
    host = host or os.environ.get("DB_HOST", "postgres")
    port = port or os.environ.get("DB_PORT", "5432")
    
    # Get database name based on environment
    db_name = get_database_name()
    
    # Construct and return the URL
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
