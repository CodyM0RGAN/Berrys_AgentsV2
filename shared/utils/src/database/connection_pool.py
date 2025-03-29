"""
Database connection pool management for Berrys_AgentsV2 platform.

This module provides utilities for configuring and managing database connection
pools for the Berrys_AgentsV2 production environment. It includes functionality
for setting up optimized SQLAlchemy connection pools with monitoring.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import QueuePool

# Import metrics for connection pool monitoring
try:
    from shared.utils.src.monitoring.metrics import gauge
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False
    logging.warning("Metrics module not available, connection pool metrics disabled")

# Configure logging
logger = logging.getLogger(__name__)

class ConnectionPoolMonitor:
    """Monitors database connection pool status and reports metrics."""
    
    def __init__(self, 
                 engine: Engine, 
                 name: str = "default", 
                 interval_seconds: int = 15):
        """
        Initialize connection pool monitor.
        
        Args:
            engine: SQLAlchemy engine to monitor
            name: Identifier for this connection pool
            interval_seconds: Interval in seconds for metrics collection
        """
        self.engine = engine
        self.name = name
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
    
    def start(self) -> None:
        """Start monitoring thread."""
        if not HAS_METRICS:
            logger.info("Metrics not available, skipping connection pool monitoring")
            return
            
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started connection pool monitoring for '{self.name}'")
    
    def stop(self) -> None:
        """Stop monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that collects and reports metrics."""
        while self.running:
            try:
                self._collect_metrics()
            except Exception as e:
                logger.warning(f"Error collecting connection pool metrics: {e}")
            
            time.sleep(self.interval_seconds)
    
    def _collect_metrics(self) -> None:
        """Collect and report connection pool metrics."""
        if not hasattr(self.engine, "pool"):
            return
            
        pool = self.engine.pool
        status = pool.status()
        
        # Record metrics
        gauge("db_pool_checkedin", status.get("checkedin", 0), 
              {"pool": self.name, "status": "available"})
        gauge("db_pool_checkedout", status.get("checkedout", 0), 
              {"pool": self.name, "status": "used"})
        gauge("db_pool_overflow", status.get("overflow", 0), 
              {"pool": self.name, "status": "overflow"})
        
        # Log pool status periodically at debug level
        logger.debug(f"Connection pool '{self.name}' status: "
                    f"used={status.get('checkedout', 0)}, "
                    f"available={status.get('checkedin', 0)}, "
                    f"overflow={status.get('overflow', 0)}")

def optimize_engine_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply optimal engine configuration for production.
    
    Args:
        config: Initial engine configuration dictionary
        
    Returns:
        Dict[str, Any]: Optimized engine configuration
    """
    # Default optimal settings
    optimal_config = {
        "pool_size": 5,                # Base pool size
        "max_overflow": 10,            # Maximum number of overflow connections
        "pool_timeout": 30,            # 30 seconds timeout for getting a connection
        "pool_recycle": 1800,          # Recycle connections after 30 minutes
        "pool_pre_ping": True,         # Verify connections before use
        "connect_args": {
            "connect_timeout": 5,      # Connection timeout in seconds
            "application_name": "berrys_agents_v2"  # App name for monitoring
        }
    }
    
    # Override optimal settings with user-provided settings
    result = optimal_config.copy()
    result.update(config)
    
    # Ensure connect_args is properly merged
    if "connect_args" in config:
        result["connect_args"] = {**optimal_config["connect_args"], **config["connect_args"]}
    
    return result

def create_sync_engine(url: str, 
                      config: Optional[Dict[str, Any]] = None, 
                      pool_name: str = "default") -> Engine:
    """
    Create a synchronized SQLAlchemy engine with optimized configuration.
    
    Args:
        url: Database URL
        config: Additional engine configuration
        pool_name: Name for this connection pool
        
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    # Apply optimal configuration
    engine_config = optimize_engine_config(config or {})
    
    # Create engine
    engine = create_engine(
        url,
        poolclass=QueuePool,
        **engine_config
    )
    
    # Set up connection pool monitoring
    monitor = ConnectionPoolMonitor(engine, name=pool_name)
    monitor.start()
    
    # Set up event listeners for logging
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug(f"Connection checkout: {pool_name}")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logger.debug(f"Connection checkin: {pool_name}")
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.info(f"New connection established: {pool_name}")
    
    @event.listens_for(engine, "reset")
    def receive_reset(dbapi_connection, connection_record):
        logger.debug(f"Connection reset: {pool_name}")
    
    return engine

def create_async_engine_pool(url: str, 
                           config: Optional[Dict[str, Any]] = None, 
                           pool_name: str = "default") -> AsyncEngine:
    """
    Create an asynchronous SQLAlchemy engine with optimized configuration.
    
    Args:
        url: Database URL (should use asyncpg dialect)
        config: Additional engine configuration
        pool_name: Name for this connection pool
        
    Returns:
        AsyncEngine: Configured SQLAlchemy async engine
    """
    # Apply optimal configuration
    engine_config = optimize_engine_config(config or {})
    
    # Create engine
    engine = create_async_engine(
        url,
        **engine_config
    )
    
    # Unfortunately, we can't easily monitor async engine pools
    # as they don't expose status in the same way
    
    return engine

def create_session_factory(engine: Engine) -> scoped_session:
    """
    Create a scoped session factory for a SQLAlchemy engine.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        scoped_session: Session factory
    """
    return scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    )

def create_async_session_factory(engine: AsyncEngine) -> Type[AsyncSession]:
    """
    Create an async session factory for a SQLAlchemy async engine.
    
    Args:
        engine: SQLAlchemy async engine
        
    Returns:
        Type[AsyncSession]: Async session factory
    """
    return sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession
    )


# Usage example:
"""
# Synchronous engine
db_url = "postgresql://username:password@localhost:5432/mydatabase"
engine = create_sync_engine(db_url, pool_name="main")
Session = create_session_factory(engine)

# In request handlers
def handle_request():
    session = Session()
    try:
        # Use session
        result = session.query(MyModel).all()
        return result
    finally:
        session.close()

# Async engine
async_db_url = "postgresql+asyncpg://username:password@localhost:5432/mydatabase"
async_engine = create_async_engine_pool(async_db_url, pool_name="main_async")
AsyncSession = create_async_session_factory(async_engine)

# In async request handlers
async def handle_async_request():
    async with AsyncSession() as session:
        # Use session
        result = await session.execute(select(MyModel))
        return result.scalars().all()
"""
