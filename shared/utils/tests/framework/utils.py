"""
Test utilities for common testing scenarios.

This module provides utilities for common testing scenarios, including
mocking, patching, and assertion helpers.
"""

import os
import json
import re
import uuid
import inspect
import asyncio
from typing import Dict, Any, List, Optional, Callable, TypeVar, Union, Tuple, Type
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from pydantic import BaseModel

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class MockUtils:
    """
    Utilities for mocking.
    
    This class provides utilities for mocking objects and functions.
    """
    
    @staticmethod
    def create_mock(
        spec: Optional[Type] = None,
        **kwargs: Any
    ) -> MagicMock:
        """
        Create a mock object.
        
        Args:
            spec: Optional specification for the mock
            **kwargs: Attribute values for the mock
            
        Returns:
            MagicMock: Mock object
        """
        mock = MagicMock(spec=spec)
        
        for key, value in kwargs.items():
            setattr(mock, key, value)
        
        return mock
    
    @staticmethod
    def create_async_mock(
        spec: Optional[Type] = None,
        **kwargs: Any
    ) -> AsyncMock:
        """
        Create an async mock object.
        
        Args:
            spec: Optional specification for the mock
            **kwargs: Attribute values for the mock
            
        Returns:
            AsyncMock: Async mock object
        """
        mock = AsyncMock(spec=spec)
        
        for key, value in kwargs.items():
            setattr(mock, key, value)
        
        return mock
    
    @staticmethod
    def patch_object(
        target: Any,
        attribute: str,
        new: Optional[Any] = None,
        **kwargs: Any
    ) -> Any:
        """
        Patch an object attribute.
        
        Args:
            target: Target object
            attribute: Attribute name
            new: New value
            **kwargs: Additional arguments for patch
            
        Returns:
            Any: Patch object
        """
        return patch.object(target, attribute, new=new, **kwargs)
    
    @staticmethod
    def patch_property(
        target: Any,
        property_name: str,
        return_value: Any,
        **kwargs: Any
    ) -> Any:
        """
        Patch a property.
        
        Args:
            target: Target object
            property_name: Property name
            return_value: Return value
            **kwargs: Additional arguments for patch
            
        Returns:
            Any: Patch object
        """
        return patch.object(
            target,
            property_name,
            new_callable=PropertyMock,
            return_value=return_value,
            **kwargs
        )
    
    @staticmethod
    def patch_module(
        module_name: str,
        **kwargs: Any
    ) -> Any:
        """
        Patch a module.
        
        Args:
            module_name: Module name
            **kwargs: Attribute values for the module
            
        Returns:
            Any: Patch object
        """
        module_mock = MagicMock()
        
        for key, value in kwargs.items():
            setattr(module_mock, key, value)
        
        return patch.dict("sys.modules", {module_name: module_mock})
    
    @staticmethod
    def patch_env(
        **kwargs: str
    ) -> Any:
        """
        Patch environment variables.
        
        Args:
            **kwargs: Environment variable values
            
        Returns:
            Any: Patch object
        """
        return patch.dict("os.environ", kwargs)
    
    @staticmethod
    def mock_response(
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        raise_for_status: Optional[bool] = None,
    ) -> MagicMock:
        """
        Create a mock HTTP response.
        
        Args:
            status_code: Status code
            json_data: JSON data
            text: Response text
            headers: Response headers
            cookies: Response cookies
            content: Response content
            raise_for_status: Whether to raise for status
            
        Returns:
            MagicMock: Mock response
        """
        mock_response = MagicMock()
        mock_response.status_code = status_code
        
        if json_data is not None:
            mock_response.json.return_value = json_data
        
        if text is not None:
            mock_response.text = text
        elif json_data is not None:
            mock_response.text = json.dumps(json_data)
        
        if headers is not None:
            mock_response.headers = headers
        
        if cookies is not None:
            mock_response.cookies = cookies
        
        if content is not None:
            mock_response.content = content
        
        if raise_for_status is not None:
            if raise_for_status:
                mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        return mock_response
    
    @staticmethod
    def mock_async_response(
        status_code: int = 200,
        json_data: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        content: Optional[bytes] = None,
        raise_for_status: Optional[bool] = None,
    ) -> AsyncMock:
        """
        Create a mock async HTTP response.
        
        Args:
            status_code: Status code
            json_data: JSON data
            text: Response text
            headers: Response headers
            cookies: Response cookies
            content: Response content
            raise_for_status: Whether to raise for status
            
        Returns:
            AsyncMock: Mock async response
        """
        mock_response = AsyncMock()
        mock_response.status_code = status_code
        
        if json_data is not None:
            mock_response.json = AsyncMock(return_value=json_data)
        
        if text is not None:
            mock_response.text = text
        elif json_data is not None:
            mock_response.text = json.dumps(json_data)
        
        if headers is not None:
            mock_response.headers = headers
        
        if cookies is not None:
            mock_response.cookies = cookies
        
        if content is not None:
            mock_response.content = content
        
        if raise_for_status is not None:
            if raise_for_status:
                mock_response.raise_for_status = AsyncMock(side_effect=Exception("HTTP Error"))
        
        return mock_response


class AssertionUtils:
    """
    Utilities for assertions.
    
    This class provides utilities for assertions in tests.
    """
    
    @staticmethod
    def assert_dict_subset(subset: Dict[str, Any], superset: Dict[str, Any], path: str = ""):
        """
        Assert that a dictionary is a subset of another dictionary.
        
        Args:
            subset: Subset dictionary
            superset: Superset dictionary
            path: Current path for error messages
        """
        for key, value in subset.items():
            current_path = f"{path}.{key}" if path else key
            
            assert key in superset, f"Key '{current_path}' not found in superset"
            
            if isinstance(value, dict) and isinstance(superset[key], dict):
                AssertionUtils.assert_dict_subset(value, superset[key], current_path)
            else:
                assert superset[key] == value, \
                    f"Value mismatch at '{current_path}': expected {value}, got {superset[key]}"
    
    @staticmethod
    def assert_model_equals(model: BaseModel, expected: Dict[str, Any], exclude: Optional[List[str]] = None):
        """
        Assert that a model equals expected values.
        
        Args:
            model: Model to check
            expected: Expected values
            exclude: Optional fields to exclude
        """
        exclude = exclude or []
        model_dict = model.dict(exclude=set(exclude))
        
        for key, value in expected.items():
            if key not in exclude:
                assert key in model_dict, f"Key '{key}' not found in model"
                assert model_dict[key] == value, \
                    f"Value mismatch for '{key}': expected {value}, got {model_dict[key]}"
    
    @staticmethod
    def assert_models_equal(model1: BaseModel, model2: BaseModel, exclude: Optional[List[str]] = None):
        """
        Assert that two models are equal.
        
        Args:
            model1: First model
            model2: Second model
            exclude: Optional fields to exclude
        """
        exclude = exclude or []
        dict1 = model1.dict(exclude=set(exclude))
        dict2 = model2.dict(exclude=set(exclude))
        
        assert dict1 == dict2, f"Models are not equal: {dict1} != {dict2}"
    
    @staticmethod
    def assert_json_equals(json1: str, json2: str):
        """
        Assert that two JSON strings are equal.
        
        Args:
            json1: First JSON string
            json2: Second JSON string
        """
        dict1 = json.loads(json1)
        dict2 = json.loads(json2)
        
        assert dict1 == dict2, f"JSON strings are not equal: {dict1} != {dict2}"
    
    @staticmethod
    def assert_regex_match(text: str, pattern: str):
        """
        Assert that a string matches a regex pattern.
        
        Args:
            text: String to check
            pattern: Regex pattern
        """
        assert re.match(pattern, text), f"String '{text}' does not match pattern '{pattern}'"
    
    @staticmethod
    def assert_contains_all(container: Any, items: List[Any]):
        """
        Assert that a container contains all items.
        
        Args:
            container: Container to check
            items: Items to check for
        """
        for item in items:
            assert item in container, f"Item '{item}' not found in container"
    
    @staticmethod
    def assert_not_contains_any(container: Any, items: List[Any]):
        """
        Assert that a container does not contain any of the items.
        
        Args:
            container: Container to check
            items: Items to check for
        """
        for item in items:
            assert item not in container, f"Item '{item}' found in container"
    
    @staticmethod
    def assert_is_uuid(value: str):
        """
        Assert that a string is a valid UUID.
        
        Args:
            value: String to check
        """
        try:
            uuid.UUID(value)
        except ValueError:
            pytest.fail(f"String '{value}' is not a valid UUID")
    
    @staticmethod
    def assert_is_iso_date(value: str):
        """
        Assert that a string is a valid ISO date.
        
        Args:
            value: String to check
        """
        iso_pattern = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
        assert re.match(iso_pattern, value), f"String '{value}' is not a valid ISO date"
    
    @staticmethod
    def assert_raises_with_message(exception_type: Type[Exception], message: str, func: Callable, *args, **kwargs):
        """
        Assert that a function raises an exception with a specific message.
        
        Args:
            exception_type: Exception type
            message: Expected message
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        with pytest.raises(exception_type) as excinfo:
            func(*args, **kwargs)
        
        assert str(excinfo.value) == message, \
            f"Expected message '{message}', got '{str(excinfo.value)}'"
    
    @staticmethod
    async def assert_async_raises_with_message(
        exception_type: Type[Exception],
        message: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Assert that an async function raises an exception with a specific message.
        
        Args:
            exception_type: Exception type
            message: Expected message
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        with pytest.raises(exception_type) as excinfo:
            await func(*args, **kwargs)
        
        assert str(excinfo.value) == message, \
            f"Expected message '{message}', got '{str(excinfo.value)}'"


class DatabaseTestUtils:
    """
    Utilities for database testing.
    
    This class provides utilities for database testing.
    """
    
    @staticmethod
    async def create_test_data(session: AsyncSession, table_name: str, data: List[Dict[str, Any]]) -> List[Any]:
        """
        Create test data in a database table.
        
        Args:
            session: Database session
            table_name: Table name
            data: List of data dictionaries
            
        Returns:
            List[Any]: List of created records
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
        Truncate a database table.
        
        Args:
            session: Database session
            table_name: Table name
        """
        await session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        await session.commit()
    
    @staticmethod
    async def count_records(session: AsyncSession, table_name: str, where_clause: Optional[str] = None) -> int:
        """
        Count records in a database table.
        
        Args:
            session: Database session
            table_name: Table name
            where_clause: Optional WHERE clause
            
        Returns:
            int: Record count
        """
        sql = f"SELECT COUNT(*) FROM {table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        result = await session.execute(text(sql))
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
    async def get_records(
        session: AsyncSession,
        table_name: str,
        where_clause: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get records from a database table.
        
        Args:
            session: Database session
            table_name: Table name
            where_clause: Optional WHERE clause
            params: Optional query parameters
            order_by: Optional ORDER BY clause
            limit: Optional LIMIT clause
            
        Returns:
            List[Dict[str, Any]]: List of records
        """
        sql = f"SELECT * FROM {table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        result = await session.execute(text(sql), params or {})
        rows = result.fetchall()
        
        return [{key: value for key, value in row._mapping.items()} for row in rows]


class AsyncTestUtils:
    """
    Utilities for asynchronous testing.
    
    This class provides utilities for asynchronous testing.
    """
    
    @staticmethod
    async def gather_with_concurrency(n: int, *tasks):
        """
        Run tasks with a concurrency limit.
        
        Args:
            n: Concurrency limit
            *tasks: Tasks to run
            
        Returns:
            List[Any]: Task results
        """
        semaphore = asyncio.Semaphore(n)
        
        async def sem_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*(sem_task(task) for task in tasks))
    
    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """
        Wait for a condition to be true.
        
        Args:
            condition: Condition function
            timeout: Timeout in seconds
            interval: Check interval in seconds
            
        Returns:
            bool: Whether the condition was met
        """
        end_time = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < end_time:
            if condition():
                return True
            
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    async def wait_for_async_condition(
        condition: Callable[[], Any],
        timeout: float = 5.0,
        interval: float = 0.1,
    ) -> bool:
        """
        Wait for an async condition to be true.
        
        Args:
            condition: Async condition function
            timeout: Timeout in seconds
            interval: Check interval in seconds
            
        Returns:
            bool: Whether the condition was met
        """
        end_time = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < end_time:
            if await condition():
                return True
            
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    def run_async(func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Run an async function in a new event loop.
        
        Args:
            func: Async function
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()
    
    @staticmethod
    async def run_with_timeout(func: Callable[..., Any], timeout: float, *args, **kwargs) -> Any:
        """
        Run an async function with a timeout.
        
        Args:
            func: Async function
            timeout: Timeout in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Any: Function result
        """
        return await asyncio.wait_for(func(*args, **kwargs), timeout)


class FileTestUtils:
    """
    Utilities for file testing.
    
    This class provides utilities for file testing.
    """
    
    @staticmethod
    def create_temp_file(content: str, suffix: Optional[str] = None) -> str:
        """
        Create a temporary file.
        
        Args:
            content: File content
            suffix: Optional file suffix
            
        Returns:
            str: File path
        """
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def create_temp_dir() -> str:
        """
        Create a temporary directory.
        
        Returns:
            str: Directory path
        """
        import tempfile
        
        return tempfile.mkdtemp()
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        Read a file.
        
        Args:
            file_path: File path
            
        Returns:
            str: File content
        """
        with open(file_path, "r") as f:
            return f.read()
    
    @staticmethod
    def write_file(file_path: str, content: str):
        """
        Write a file.
        
        Args:
            file_path: File path
            content: File content
        """
        with open(file_path, "w") as f:
            f.write(content)
    
    @staticmethod
    def delete_file(file_path: str):
        """
        Delete a file.
        
        Args:
            file_path: File path
        """
        if os.path.exists(file_path):
            os.remove(file_path)
    
    @staticmethod
    def delete_dir(dir_path: str):
        """
        Delete a directory.
        
        Args:
            dir_path: Directory path
        """
        import shutil
        
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    @staticmethod
    def assert_file_exists(file_path: str):
        """
        Assert that a file exists.
        
        Args:
            file_path: File path
        """
        assert os.path.exists(file_path), f"File '{file_path}' does not exist"
    
    @staticmethod
    def assert_file_not_exists(file_path: str):
        """
        Assert that a file does not exist.
        
        Args:
            file_path: File path
        """
        assert not os.path.exists(file_path), f"File '{file_path}' exists"
    
    @staticmethod
    def assert_file_content(file_path: str, expected_content: str):
        """
        Assert that a file has the expected content.
        
        Args:
            file_path: File path
            expected_content: Expected content
        """
        with open(file_path, "r") as f:
            content = f.read()
        
        assert content == expected_content, \
            f"File content mismatch: expected '{expected_content}', got '{content}'"
    
    @staticmethod
    def assert_file_content_contains(file_path: str, expected_content: str):
        """
        Assert that a file contains the expected content.
        
        Args:
            file_path: File path
            expected_content: Expected content
        """
        with open(file_path, "r") as f:
            content = f.read()
        
        assert expected_content in content, \
            f"File content does not contain '{expected_content}'"
    
    @staticmethod
    def assert_file_content_matches(file_path: str, pattern: str):
        """
        Assert that a file content matches a regex pattern.
        
        Args:
            file_path: File path
            pattern: Regex pattern
        """
        with open(file_path, "r") as f:
            content = f.read()
        
        assert re.match(pattern, content), \
            f"File content '{content}' does not match pattern '{pattern}'"


class TestDecorators:
    """
    Decorators for tests.
    
    This class provides decorators for tests.
    """
    
    @staticmethod
    def skip_if(condition: bool, reason: str) -> Callable[[F], F]:
        """
        Skip a test if a condition is true.
        
        Args:
            condition: Condition to check
            reason: Skip reason
            
        Returns:
            Callable[[F], F]: Decorator
        """
        def decorator(func: F) -> F:
            return pytest.mark.skipif(condition, reason=reason)(func)
        
        return decorator
    
    @staticmethod
    def skip_if_env(env_var: str, value: str, reason: str) -> Callable[[F], F]:
        """
        Skip a test if an environment variable has a specific value.
        
        Args:
            env_var: Environment variable name
            value: Environment variable value
            reason: Skip reason
            
        Returns:
            Callable[[F], F]: Decorator
        """
        def decorator(func: F) -> F:
            return pytest.mark.skipif(
                os.environ.get(env_var) == value,
                reason=reason
            )(func)
        
        return decorator
    
    @staticmethod
    def skip_if_not_env(env_var: str, value: str, reason: str) -> Callable[[F], F]:
        """
        Skip a test if an environment variable does not have a specific value.
        
        Args:
            env_var: Environment variable name
            value: Environment variable value
            reason: Skip reason
            
        Returns:
            Callable[[F], F]: Decorator
        """
        def decorator(func: F) -> F:
            return pytest.mark.skipif(
                os.environ.get(env_var) != value,
                reason=reason
            )(func)
        
        return decorator
    
    @staticmethod
    def retry(max_retries: int = 3, delay: float = 0.1) -> Callable[[F], F]:
        """
        Retry a test if it fails.
        
        Args:
            max_retries: Maximum number of retries
            delay: Delay between retries in seconds
            
        Returns:
            Callable[[F], F]: Decorator
        """
        def decorator(func: F) -> F:
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def wrapper(*args, **kwargs):
                    for i in range(max_retries):
                        try:
                            return await func(*args, **kwargs)
                        except Exception as e:
                            if i == max_retries - 1:
                                raise
                            await asyncio.sleep(delay)
                
                return wrapper
            else:
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    import time
                    
                    for i in range(max_retries):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            if i == max_retries - 1:
                                raise
                            time.sleep(delay)
                
                return wrapper
        
        return decorator
    
    @staticmethod
    def timeout(seconds: float) -> Callable[[F], F]:
        """
        Set a timeout for a test.
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Callable[[F], F]: Decorator
        """
        def decorator(func: F) -> F:
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def wrapper(*args, **kwargs):
                    return await asyncio.wait_for(func(*args, **kwargs), seconds)
                
                return wrapper
            else:
                return pytest.mark.timeout(seconds)(func)
        
        return decorator
