"""
Base test classes for the standardized testing framework.

This module provides base test classes that can be used across all services
to ensure consistent testing patterns and utilities.
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any, Generator, Optional, List, Type, Union
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from httpx import AsyncClient

from shared.utils.src.exceptions import ValidationError


class BaseTest:
    """
    Base class for all tests in the Berrys_AgentsV2 system.
    
    This class provides common functionality and utilities for all tests.
    """
    
    @classmethod
    def setup_class(cls):
        """Set up test class."""
        pass
    
    @classmethod
    def teardown_class(cls):
        """Tear down test class."""
        pass
    
    def setup_method(self):
        """Set up test method."""
        pass
    
    def teardown_method(self):
        """Tear down test method."""
        pass
    
    @staticmethod
    def get_test_db_url() -> str:
        """
        Get the test database URL from environment variables.
        
        Returns:
            str: Test database URL
        """
        return os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test"
        )


class BaseAsyncTest(BaseTest):
    """
    Base class for asynchronous tests.
    
    This class provides common functionality and utilities for asynchronous tests.
    """
    
    @pytest.fixture(scope="function")
    def event_loop(self):
        """Create an event loop for each test."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()


class BaseDatabaseTest(BaseAsyncTest):
    """
    Base class for database tests.
    
    This class provides common functionality and utilities for database tests,
    including database connection management and transaction handling.
    """
    
    # Database engine and session
    engine = None
    async_session = None
    
    @classmethod
    async def setup_database(cls, Base):
        """
        Set up the database for testing.
        
        Args:
            Base: SQLAlchemy declarative base
        """
        # Create engine
        cls.engine = create_async_engine(
            cls.get_test_db_url(),
            echo=False,
        )
        
        # Create session factory
        cls.async_session = sessionmaker(
            cls.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables
        async with cls.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    
    @classmethod
    async def teardown_database(cls):
        """Tear down the database after testing."""
        if cls.engine:
            await cls.engine.dispose()
    
    @pytest_asyncio.fixture(scope="function")
    async def db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a test database session.
        
        Yields:
            AsyncSession: Database session
        """
        if not self.async_session:
            raise ValueError("Database not set up. Call setup_database() first.")
        
        # Create session
        async with self.async_session() as session:
            # Start transaction
            async with session.begin():
                # Return session
                yield session
                
                # Rollback transaction
                await session.rollback()
    
    @staticmethod
    async def execute_sql(session: AsyncSession, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute raw SQL query.
        
        Args:
            session: Database session
            sql: SQL query
            params: Query parameters
            
        Returns:
            Any: Query result
        """
        result = await session.execute(text(sql), params or {})
        return result


class BaseAPITest(BaseAsyncTest):
    """
    Base class for API tests.
    
    This class provides common functionality and utilities for API tests,
    including request building and response validation.
    """
    
    @staticmethod
    def build_url(base_url: str, path: str) -> str:
        """
        Build a URL from base URL and path.
        
        Args:
            base_url: Base URL
            path: Path
            
        Returns:
            str: Full URL
        """
        # Remove trailing slash from base URL
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        
        # Remove leading slash from path
        if path.startswith("/"):
            path = path[1:]
        
        return f"{base_url}/{path}"
    
    @staticmethod
    def assert_successful_response(response: Dict[str, Any], expected_data: Optional[Dict[str, Any]] = None):
        """
        Assert that a response is successful.
        
        Args:
            response: Response data
            expected_data: Expected data
        """
        assert response["success"] is True
        assert "message" in response
        
        if expected_data:
            assert "data" in response
            for key, value in expected_data.items():
                assert response["data"][key] == value
    
    @staticmethod
    def assert_error_response(response: Dict[str, Any], expected_error: Optional[str] = None):
        """
        Assert that a response is an error.
        
        Args:
            response: Response data
            expected_error: Expected error message
        """
        assert response["success"] is False
        assert "error" in response
        
        if expected_error:
            assert response["error"] == expected_error


class BaseModelTest(BaseTest):
    """
    Base class for model tests.
    
    This class provides common functionality and utilities for model tests,
    including model validation and serialization testing.
    """
    
    @staticmethod
    def assert_model_fields(model: Any, expected_fields: Dict[str, Any]):
        """
        Assert that a model has the expected field values.
        
        Args:
            model: Model instance
            expected_fields: Expected field values
        """
        for field, value in expected_fields.items():
            assert getattr(model, field) == value
    
    @staticmethod
    def assert_model_validation_error(model_class: Type, invalid_data: Dict[str, Any], expected_error_fields: List[str]):
        """
        Assert that model validation fails with the expected error fields.
        
        Args:
            model_class: Model class
            invalid_data: Invalid data
            expected_error_fields: Expected error fields
        """
        with pytest.raises(ValidationError) as excinfo:
            model_class(**invalid_data)
        
        error = excinfo.value
        for field in expected_error_fields:
            assert field in error.errors


class BaseServiceTest(BaseAsyncTest):
    """
    Base class for service tests.
    
    This class provides common functionality and utilities for service tests,
    including dependency mocking and service method testing.
    """
    
    @staticmethod
    def create_mock_repository():
        """
        Create a mock repository.
        
        Returns:
            MagicMock: Mock repository
        """
        return MagicMock()
    
    @staticmethod
    def create_mock_service():
        """
        Create a mock service.
        
        Returns:
            MagicMock: Mock service
        """
        return MagicMock()
    
    @staticmethod
    def create_async_mock_repository():
        """
        Create an async mock repository.
        
        Returns:
            AsyncMock: Async mock repository
        """
        return AsyncMock()
    
    @staticmethod
    def create_async_mock_service():
        """
        Create an async mock service.
        
        Returns:
            AsyncMock: Async mock service
        """
        return AsyncMock()


class BaseIntegrationTest(BaseDatabaseTest, BaseAPITest):
    """
    Base class for integration tests.
    
    This class provides common functionality and utilities for integration tests,
    combining database and API testing capabilities.
    """
    
    pass
