"""
Database utilities for the API Gateway service.

This module provides functions for database connection and initialization.
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import text
from typing import AsyncGenerator

from shared.utils.src.db_connection import get_async_database_url
from shared.models.src.base import Base

# Configure logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable or construct it
database_url = os.environ.get("DATABASE_URL") or get_async_database_url()

# Create async engine
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True
)

# Create async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session.
    
    Yields:
        AsyncSession: A database session
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()

async def check_db_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if the connection is working, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

async def init_db() -> None:
    """
    Initialize the database.
    
    This function is called during service startup to ensure the database is ready.
    """
    try:
        # Check connection
        is_connected = await check_db_connection()
        if not is_connected:
            raise Exception("Could not connect to database")
        
        logger.info("Database connection successful")
        
        # Get a database session
        async for session in get_db():
            # The session is yielded and then closed automatically
            pass
            
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
