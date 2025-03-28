"""
Health check utilities for the Berrys_AgentsV2 project.

This module provides utilities for monitoring service health.
"""

import logging
import time
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Callable

from .db_monitoring import check_database_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'health_check_{datetime.now().strftime("%Y-%m-%d")}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('health_check')

def create_health_check_router(
    get_db_session: Callable[[], AsyncSession],
    get_db_engine: Callable[[], AsyncEngine],
    service_name: str
) -> APIRouter:
    """
    Create a health check router for a service.
    
    Args:
        get_db_session: Function that returns a database session
        get_db_engine: Function that returns a database engine
        service_name: Name of the service
        
    Returns:
        APIRouter: FastAPI router with health check endpoints
    """
    router = APIRouter(tags=["health"])
    
    @router.get("/health")
    async def health_check():
        """
        Check service health.
        
        Returns:
            Dict: Health check results
        """
        start_time = time.time()
        
        try:
            # Check database health
            db_engine = get_db_engine()
            db_health = check_database_health(db_engine)
            
            # Check service health
            service_health = {
                'status': 'healthy',
                'uptime': get_uptime(),
                'memory_usage': get_memory_usage()
            }
            
            # Overall health
            overall_status = 'healthy' if db_health['status'] == 'healthy' else 'unhealthy'
            
            response_time = time.time() - start_time
            
            return {
                'service': service_name,
                'status': overall_status,
                'database': db_health,
                'service_details': service_health,
                'response_time_ms': response_time * 1000
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Health check failed: {str(e)}"
            )
    
    @router.get("/health/database")
    async def database_health():
        """
        Check database health.
        
        Returns:
            Dict: Database health check results
        """
        try:
            db_engine = get_db_engine()
            db_health = check_database_health(db_engine)
            return db_health
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database health check failed: {str(e)}"
            )
    
    return router

def get_uptime() -> float:
    """
    Get service uptime in seconds.
    
    Returns:
        float: Uptime in seconds
    """
    # This is a placeholder. In a real implementation, you would track
    # the service start time and calculate the uptime.
    return 0.0

def get_memory_usage() -> Dict[str, Any]:
    """
    Get service memory usage.
    
    Returns:
        Dict: Memory usage details
    """
    # This is a placeholder. In a real implementation, you would use
    # a library like psutil to get memory usage.
    return {
        'total_mb': 0,
        'used_mb': 0,
        'percent': 0
    }
