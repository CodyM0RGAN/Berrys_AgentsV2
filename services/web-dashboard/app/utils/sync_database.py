"""
Synchronous database utilities for the web dashboard application.

This module provides synchronous database utilities for the web dashboard application,
which uses Flask-SQLAlchemy (a synchronous library) instead of the asynchronous
SQLAlchemy used by other services.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
import logging
import traceback

logger = logging.getLogger(__name__)

# Get database URL from environment variable or use default
# Use psycopg2 (synchronous) instead of asyncpg (asynchronous)
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI", 
                        os.getenv("SYNC_DATABASE_URL", 
                                 "postgresql://postgres:postgres@postgres:5432/mas_framework"))

logger.info("Using database URL: %s", DATABASE_URL)
if "asyncpg" in DATABASE_URL:
    logger.warning("WARNING: asyncpg driver detected in URL, this may cause issues with Flask-SQLAlchemy")
    logger.warning("Stack trace: %s", ''.join(traceback.format_stack()))

# Create engine with appropriate parameters based on dialect
engine_kwargs = {
    "echo": False,  # Set to True for SQL query logging
}

# Add connection pool parameters only for PostgreSQL
if DATABASE_URL.startswith("postgresql"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    })

# Create the engine
logger.info("Creating database engine with URL: %s", DATABASE_URL)
logger.info("Engine configuration: %s", engine_kwargs)
try:
    engine = create_engine(
        DATABASE_URL,
        **engine_kwargs
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error("Error creating database engine: %s", str(e), exc_info=True)
    raise

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
)

# Create base class for declarative models
Base = declarative_base(metadata=MetaData())


def get_db():
    """
    Get a database session.
    
    Returns:
        Session: Database session
    """
    logger.info("Creating new database session")
    session = SessionLocal()
    try:
        logger.info("Database session created successfully")
        return session
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}", exc_info=True)
        logger.error("Stack trace: %s", ''.join(traceback.format_stack()))
        raise
    finally:
        session.close()


def init_db():
    """
    Initialize the database by creating all tables.
    """
    logger.info("Initializing database")
    try:
        # Create tables if they don't exist
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        logger.error("Stack trace: %s", ''.join(traceback.format_stack()))
        raise


def check_db_connection():
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    logger.info("Checking database connection")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            logger.info("Database connection established")
            conn.execute(text("SELECT 1"))
            logger.info("Database query executed successfully")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        logger.error("Stack trace: %s", ''.join(traceback.format_stack()))
        return False


def close_db_connection():
    """
    Close the database connection.
    """
    logger.info("Closing database connection")
    try:
        engine.dispose()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connection: {str(e)}", exc_info=True)
        logger.error("Stack trace: %s", ''.join(traceback.format_stack()))
