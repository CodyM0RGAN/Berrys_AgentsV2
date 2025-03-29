"""
Database testing utilities for Berrys_AgentsV2.

This module provides utilities for database testing, including:
- Creating in-memory test databases
- Setting up database tables for testing
- Database state management for tests
- Isolation mechanisms for concurrent tests
"""

import os
import uuid
import tempfile
from typing import Optional, Dict, Any, List, Union, Callable, Type
from contextlib import contextmanager

import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import StaticPool

# Import the shared base model if available
try:
    from shared.models.src.base import StandardModel
    HAS_STANDARD_MODEL = True
except ImportError:
    StandardModel = None
    HAS_STANDARD_MODEL = False


class TestingBase:
    """Base class for testing models."""
    pass


# Create a base class for test models
TestBase = declarative_base(cls=TestingBase)


def get_in_memory_db_engine(echo: bool = False) -> sa.engine.Engine:
    """
    Create an in-memory SQLite database engine for testing.
    
    Args:
        echo: Whether to echo SQL statements.
        
    Returns:
        SQLAlchemy engine instance.
    """
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=echo
    )


def get_temp_postgres_engine(db_name: Optional[str] = None, echo: bool = False) -> sa.engine.Engine:
    """
    Create a temporary PostgreSQL database engine for testing.
    
    This requires a local PostgreSQL server with appropriate permissions.
    
    Args:
        db_name: Optional database name. If not provided, a random name will be generated.
        echo: Whether to echo SQL statements.
        
    Returns:
        SQLAlchemy engine instance.
    """
    test_db_name = db_name or f"test_db_{uuid.uuid4().hex}"
    
    # Connect to PostgreSQL server (postgres database) to create test database
    engine = create_engine("postgresql://postgres:postgres@localhost/postgres")
    conn = engine.connect()
    conn.execute("COMMIT")  # Exit the transaction
    conn.execute(f'CREATE DATABASE "{test_db_name}"')
    conn.close()
    
    # Create engine for the test database
    test_engine = create_engine(f"postgresql://postgres:postgres@localhost/{test_db_name}", echo=echo)
    
    return test_engine


def create_test_database(engine: sa.engine.Engine, base_class: Optional[Type] = None) -> None:
    """
    Create database tables for testing.
    
    Args:
        engine: SQLAlchemy engine instance.
        base_class: SQLAlchemy declarative base class. If not provided, uses the TestBase class.
    """
    base = base_class or TestBase
    base.metadata.create_all(engine)


def drop_test_database(engine: sa.engine.Engine, base_class: Optional[Type] = None) -> None:
    """
    Drop database tables used for testing.
    
    Args:
        engine: SQLAlchemy engine instance.
        base_class: SQLAlchemy declarative base class. If not provided, uses the TestBase class.
    """
    base = base_class or TestBase
    base.metadata.drop_all(engine)


@contextmanager
def test_database_session(
    engine: Optional[sa.engine.Engine] = None,
    base_class: Optional[Type] = None,
    echo: bool = False
) -> Session:
    """
    Context manager that provides a database session for testing.
    
    This creates an in-memory database, sets up tables, and provides a session.
    The database is torn down when the context manager exits.
    
    Args:
        engine: SQLAlchemy engine instance. If not provided, creates an in-memory SQLite database.
        base_class: SQLAlchemy declarative base class. If not provided, uses the TestBase class.
        echo: Whether to echo SQL statements.
        
    Yields:
        SQLAlchemy session for testing.
    """
    engine = engine or get_in_memory_db_engine(echo=echo)
    base = base_class or TestBase
    
    # Create tables
    create_test_database(engine, base)
    
    # Create session
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)()
    
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
        # Drop tables
        drop_test_database(engine, base)


def seed_test_data(session: Session, model_class: Type, data: List[Dict[str, Any]]) -> List[Any]:
    """
    Seed test data into the database.
    
    Args:
        session: SQLAlchemy session.
        model_class: Model class to create instances of.
        data: List of dictionaries containing data for model instances.
        
    Returns:
        List of created model instances.
    """
    instances = []
    for item in data:
        instance = model_class(**item)
        session.add(instance)
        instances.append(instance)
    
    session.commit()
    return instances


class TransactionTestMixin:
    """
    Mixin for SQLAlchemy transaction testing.
    
    This mixin provides methods for setting up and tearing down
    a database connection and transaction for testing.
    
    Usage:
        class TestMyClass(TransactionTestMixin, unittest.TestCase):
            def setUp(self):
                self.engine = get_in_memory_db_engine()
                self.setup_db(self.engine)
                
            def tearDown(self):
                self.teardown_db()
                
            def test_something(self):
                # Test code using self.session
    """
    
    def setup_db(self, engine: sa.engine.Engine, base_class: Optional[Type] = None) -> None:
        """
        Set up database connection and transaction for testing.
        
        Args:
            engine: SQLAlchemy engine instance.
            base_class: SQLAlchemy declarative base class. If not provided, uses the TestBase class.
        """
        self.engine = engine
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.session_factory = sessionmaker(bind=self.connection)
        self.session = self.session_factory()
        
        # Create tables
        base = base_class or TestBase
        base.metadata.create_all(engine)
    
    def teardown_db(self) -> None:
        """Tear down database connection and transaction."""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'transaction'):
            self.transaction.rollback()
        if hasattr(self, 'connection'):
            self.connection.close()


# Example test models
class TestUser(TestBase):
    """Example test model for users."""
    
    __tablename__ = "test_user"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class TestProject(TestBase):
    """Example test model for projects."""
    
    __tablename__ = "test_project"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
