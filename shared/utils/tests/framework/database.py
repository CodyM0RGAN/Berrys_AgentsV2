"""
Database testing utilities.

This module provides utilities for database testing, including connection management,
transaction handling, and schema validation.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Type, Union, AsyncGenerator, Tuple
import pytest
import pytest_asyncio

from sqlalchemy import MetaData, Table, Column, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text


class DatabaseTestConfig:
    """
    Configuration for database tests.
    
    This class provides configuration options for database tests.
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False,
        create_tables: bool = True,
        drop_tables: bool = True,
    ):
        """
        Initialize the configuration.
        
        Args:
            database_url: Database URL (default: from environment)
            echo: Whether to echo SQL statements
            create_tables: Whether to create tables
            drop_tables: Whether to drop tables
        """
        self.database_url = database_url or os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework_test"
        )
        self.echo = echo
        self.create_tables = create_tables
        self.drop_tables = drop_tables


class DatabaseTestHelper:
    """
    Helper for database tests.
    
    This class provides utilities for database tests, including connection management,
    transaction handling, and schema validation.
    """
    
    def __init__(self, config: Optional[DatabaseTestConfig] = None):
        """
        Initialize the helper.
        
        Args:
            config: Database test configuration
        """
        self.config = config or DatabaseTestConfig()
        self.engine = None
        self.async_session = None
    
    async def setup_database(self, Base) -> AsyncEngine:
        """
        Set up the database for testing.
        
        Args:
            Base: SQLAlchemy declarative base
            
        Returns:
            AsyncEngine: Database engine
        """
        # Create engine
        self.engine = create_async_engine(
            self.config.database_url,
            echo=self.config.echo,
        )
        
        # Create session factory
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        # Create tables
        if self.config.create_tables:
            async with self.engine.begin() as conn:
                if self.config.drop_tables:
                    await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        
        return self.engine
    
    async def teardown_database(self):
        """Tear down the database after testing."""
        if self.engine:
            await self.engine.dispose()
    
    async def create_session(self) -> AsyncSession:
        """
        Create a database session.
        
        Returns:
            AsyncSession: Database session
        """
        if not self.async_session:
            raise ValueError("Database not set up. Call setup_database() first.")
        
        return self.async_session()
    
    @pytest_asyncio.fixture
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
    
    @staticmethod
    async def insert_test_data(session: AsyncSession, table_name: str, data: List[Dict[str, Any]]) -> List[Any]:
        """
        Insert test data into a table.
        
        Args:
            session: Database session
            table_name: Table name
            data: List of data dictionaries
            
        Returns:
            List[Any]: List of inserted records
        """
        if not data:
            return []
        
        # Build insert statement
        columns = list(data[0].keys())
        placeholders = [f":{col}" for col in columns]
        
        sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        RETURNING *
        """
        
        # Execute insert statements
        results = []
        for item in data:
            result = await session.execute(text(sql), item)
            row = result.fetchone()
            results.append(row)
        
        # Commit changes
        await session.commit()
        
        return results
    
    @staticmethod
    async def truncate_table(session: AsyncSession, table_name: str):
        """
        Truncate a table.
        
        Args:
            session: Database session
            table_name: Table name
        """
        await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        await session.commit()
    
    @staticmethod
    async def count_records(session: AsyncSession, table_name: str) -> int:
        """
        Count records in a table.
        
        Args:
            session: Database session
            table_name: Table name
            
        Returns:
            int: Record count
        """
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()
    
    @staticmethod
    async def get_record_by_id(session: AsyncSession, table_name: str, record_id: Any) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            session: Database session
            table_name: Table name
            record_id: Record ID
            
        Returns:
            Optional[Dict[str, Any]]: Record if found
        """
        result = await session.execute(
            text(f"SELECT * FROM {table_name} WHERE id = :id"),
            {"id": record_id}
        )
        row = result.fetchone()
        
        if row is None:
            return None
        
        return {key: value for key, value in row._mapping.items()}
    
    @staticmethod
    async def verify_schema(engine: AsyncEngine, expected_tables: List[str]) -> Tuple[bool, List[str]]:
        """
        Verify that the database schema contains the expected tables.
        
        Args:
            engine: Database engine
            expected_tables: List of expected table names
            
        Returns:
            Tuple[bool, List[str]]: (success, missing tables)
        """
        async with engine.connect() as conn:
            inspector = inspect(conn)
            actual_tables = await inspector.get_table_names()
        
        missing_tables = [table for table in expected_tables if table not in actual_tables]
        return len(missing_tables) == 0, missing_tables
    
    @staticmethod
    async def verify_table_columns(
        engine: AsyncEngine,
        table_name: str,
        expected_columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Verify that a table has the expected columns.
        
        Args:
            engine: Database engine
            table_name: Table name
            expected_columns: List of expected column names
            
        Returns:
            Tuple[bool, List[str]]: (success, missing columns)
        """
        async with engine.connect() as conn:
            inspector = inspect(conn)
            columns = await inspector.get_columns(table_name)
            actual_columns = [column['name'] for column in columns]
        
        missing_columns = [column for column in expected_columns if column not in actual_columns]
        return len(missing_columns) == 0, missing_columns


class MockDatabase:
    """
    Mock database for testing.
    
    This class provides a mock database for testing without a real database connection.
    """
    
    def __init__(self):
        """Initialize the mock database."""
        self.tables = {}
        self.data = {}
    
    def create_table(self, table_name: str, columns: List[str]):
        """
        Create a mock table.
        
        Args:
            table_name: Table name
            columns: Column names
        """
        self.tables[table_name] = columns
        self.data[table_name] = []
    
    def insert(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a record into a mock table.
        
        Args:
            table_name: Table name
            record: Record data
            
        Returns:
            Dict[str, Any]: Inserted record
        """
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Validate columns
        for column in record.keys():
            if column not in self.tables[table_name]:
                raise ValueError(f"Column {column} does not exist in table {table_name}")
        
        # Add record
        self.data[table_name].append(record)
        
        return record
    
    def find(self, table_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find records in a mock table.
        
        Args:
            table_name: Table name
            query: Query conditions
            
        Returns:
            List[Dict[str, Any]]: Matching records
        """
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Filter records
        results = []
        for record in self.data[table_name]:
            match = True
            for key, value in query.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            
            if match:
                results.append(record)
        
        return results
    
    def find_one(self, table_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single record in a mock table.
        
        Args:
            table_name: Table name
            query: Query conditions
            
        Returns:
            Optional[Dict[str, Any]]: Matching record if found
        """
        results = self.find(table_name, query)
        return results[0] if results else None
    
    def update(self, table_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update records in a mock table.
        
        Args:
            table_name: Table name
            query: Query conditions
            update: Update values
            
        Returns:
            int: Number of updated records
        """
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Update records
        count = 0
        for record in self.data[table_name]:
            match = True
            for key, value in query.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            
            if match:
                for key, value in update.items():
                    record[key] = value
                count += 1
        
        return count
    
    def delete(self, table_name: str, query: Dict[str, Any]) -> int:
        """
        Delete records from a mock table.
        
        Args:
            table_name: Table name
            query: Query conditions
            
        Returns:
            int: Number of deleted records
        """
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Find matching records
        to_delete = []
        for i, record in enumerate(self.data[table_name]):
            match = True
            for key, value in query.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            
            if match:
                to_delete.append(i)
        
        # Delete records (in reverse order to avoid index issues)
        for i in sorted(to_delete, reverse=True):
            del self.data[table_name][i]
        
        return len(to_delete)
    
    def count(self, table_name: str, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records in a mock table.
        
        Args:
            table_name: Table name
            query: Optional query conditions
            
        Returns:
            int: Record count
        """
        if query:
            return len(self.find(table_name, query))
        return len(self.data.get(table_name, []))
    
    def clear(self, table_name: str):
        """
        Clear all records from a mock table.
        
        Args:
            table_name: Table name
        """
        if table_name in self.data:
            self.data[table_name] = []
    
    def clear_all(self):
        """Clear all records from all mock tables."""
        for table_name in self.data:
            self.data[table_name] = []
