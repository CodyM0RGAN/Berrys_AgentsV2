"""
Database monitoring utilities for the Berrys_AgentsV2 project.

This module provides utilities for monitoring database operations and errors.
"""

import logging
import time
import functools
import os
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'db_operations_{datetime.now().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('db_monitoring')

# SQLAlchemy query performance logging
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time."""
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.debug("SQL: %s", statement)
    logger.debug("Parameters: %s", parameters)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time."""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger.debug("Total execution time: %.3f ms", total * 1000)
    if total > 0.5:  # Log slow queries (more than 500ms)
        logger.warning("Slow query detected (%.3f ms): %s", total * 1000, statement)

# Session operation logging
def log_session_operation(func):
    """Decorator to log session operations."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Session operation: %s", func.__name__)
        try:
            result = func(*args, **kwargs)
            logger.info("Session operation completed: %s", func.__name__)
            return result
        except Exception as e:
            logger.error("Session operation failed: %s - %s", func.__name__, str(e))
            raise
    return wrapper

# Database health check
def check_database_health(engine):
    """Check database health."""
    try:
        # Check connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.scalar() == 1
            
        # Check connection pool
        pool_status = {
            'pool_size': engine.pool.size(),
            'checkedin': engine.pool.checkedin(),
            'overflow': engine.pool.overflow(),
            'checkedout': engine.pool.checkedout(),
        }
        logger.info("Database connection pool status: %s", pool_status)
        
        return {
            'status': 'healthy',
            'pool': pool_status
        }
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

# Migration logging
def log_migration(migration_id, direction, status, error=None):
    """Log migration execution."""
    logger.info("Migration %s - Direction: %s - Status: %s", migration_id, direction, status)
    if error:
        logger.error("Migration error: %s", error)

# Schema change logging
def log_schema_change(table_name, operation, details):
    """Log schema change."""
    logger.info("Schema change - Table: %s - Operation: %s - Details: %s", table_name, operation, details)

# Data validation
def validate_data(session, model_class, validation_func):
    """Validate data in the database."""
    try:
        instances = session.query(model_class).all()
        invalid_instances = []
        
        for instance in instances:
            if not validation_func(instance):
                invalid_instances.append(instance)
        
        if invalid_instances:
            logger.warning("Data validation failed for %d instances of %s", 
                          len(invalid_instances), model_class.__name__)
            return False, invalid_instances
        
        logger.info("Data validation passed for all instances of %s", model_class.__name__)
        return True, []
    except Exception as e:
        logger.error("Data validation error: %s", str(e))
        raise
