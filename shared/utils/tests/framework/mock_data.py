"""
Mock data generators for testing.

This module provides utilities for generating mock data for testing purposes,
including factories for creating test instances of models.
"""

import uuid
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Type, Union, TypeVar, Generic

from pydantic import BaseModel

T = TypeVar('T')


class MockDataGenerator:
    """
    Base class for mock data generators.
    
    This class provides common functionality for generating mock data.
    """
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """
        Generate a random string.
        
        Args:
            length: Length of the string
            
        Returns:
            str: Random string
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """
        Generate a random email address.
        
        Returns:
            str: Random email address
        """
        username = MockDataGenerator.random_string(8)
        domain = MockDataGenerator.random_string(6)
        return f"{username}@{domain}.com"
    
    @staticmethod
    def random_uuid() -> str:
        """
        Generate a random UUID.
        
        Returns:
            str: Random UUID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def random_datetime(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> datetime:
        """
        Generate a random datetime.
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            datetime: Random datetime
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        
        if end_date is None:
            end_date = datetime.now()
        
        delta = end_date - start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start_date + timedelta(seconds=random_seconds)
    
    @staticmethod
    def random_bool() -> bool:
        """
        Generate a random boolean.
        
        Returns:
            bool: Random boolean
        """
        return random.choice([True, False])
    
    @staticmethod
    def random_int(min_value: int = 0, max_value: int = 100) -> int:
        """
        Generate a random integer.
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            int: Random integer
        """
        return random.randint(min_value, max_value)
    
    @staticmethod
    def random_float(min_value: float = 0.0, max_value: float = 1.0) -> float:
        """
        Generate a random float.
        
        Args:
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            float: Random float
        """
        return random.uniform(min_value, max_value)
    
    @staticmethod
    def random_choice(choices: List[Any]) -> Any:
        """
        Choose a random item from a list.
        
        Args:
            choices: List of choices
            
        Returns:
            Any: Random choice
        """
        return random.choice(choices)
    
    @staticmethod
    def random_dict(keys: List[str], value_generator: callable) -> Dict[str, Any]:
        """
        Generate a random dictionary.
        
        Args:
            keys: List of keys
            value_generator: Function to generate values
            
        Returns:
            Dict[str, Any]: Random dictionary
        """
        return {key: value_generator() for key in keys}
    
    @staticmethod
    def random_list(item_generator: callable, length: int = 5) -> List[Any]:
        """
        Generate a random list.
        
        Args:
            item_generator: Function to generate items
            length: Length of the list
            
        Returns:
            List[Any]: Random list
        """
        return [item_generator() for _ in range(length)]


class ModelFactory(Generic[T]):
    """
    Factory for creating test instances of models.
    
    This class provides a generic factory for creating test instances of models.
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize the factory.
        
        Args:
            model_class: Model class
        """
        self.model_class = model_class
        self.field_generators = {}
    
    def register_field_generator(self, field_name: str, generator: callable) -> 'ModelFactory[T]':
        """
        Register a generator for a specific field.
        
        Args:
            field_name: Field name
            generator: Generator function
            
        Returns:
            ModelFactory[T]: Self
        """
        self.field_generators[field_name] = generator
        return self
    
    def build(self, **kwargs) -> T:
        """
        Build a model instance.
        
        Args:
            **kwargs: Field values
            
        Returns:
            T: Model instance
        """
        # Start with default values
        data = {}
        
        # Add generated values
        for field_name, generator in self.field_generators.items():
            if field_name not in kwargs:
                data[field_name] = generator()
        
        # Override with provided values
        data.update(kwargs)
        
        # Create model instance
        return self.model_class(**data)
    
    def build_batch(self, count: int, **kwargs) -> List[T]:
        """
        Build multiple model instances.
        
        Args:
            count: Number of instances to build
            **kwargs: Field values
            
        Returns:
            List[T]: List of model instances
        """
        return [self.build(**kwargs) for _ in range(count)]


# Common model factories

def create_user_factory(model_class: Type[T]) -> ModelFactory[T]:
    """
    Create a factory for user models.
    
    Args:
        model_class: User model class
        
    Returns:
        ModelFactory[T]: User model factory
    """
    return ModelFactory(model_class) \
        .register_field_generator('id', MockDataGenerator.random_uuid) \
        .register_field_generator('username', lambda: MockDataGenerator.random_string(8)) \
        .register_field_generator('email', MockDataGenerator.random_email) \
        .register_field_generator('created_at', MockDataGenerator.random_datetime) \
        .register_field_generator('updated_at', MockDataGenerator.random_datetime)


def create_project_factory(model_class: Type[T]) -> ModelFactory[T]:
    """
    Create a factory for project models.
    
    Args:
        model_class: Project model class
        
    Returns:
        ModelFactory[T]: Project model factory
    """
    return ModelFactory(model_class) \
        .register_field_generator('id', MockDataGenerator.random_uuid) \
        .register_field_generator('name', lambda: f"Project {MockDataGenerator.random_string(5)}") \
        .register_field_generator('description', lambda: f"Description for project {MockDataGenerator.random_string(10)}") \
        .register_field_generator('created_at', MockDataGenerator.random_datetime) \
        .register_field_generator('updated_at', MockDataGenerator.random_datetime) \
        .register_field_generator('status', lambda: MockDataGenerator.random_choice(['DRAFT', 'ACTIVE', 'COMPLETED', 'ARCHIVED']))


def create_agent_factory(model_class: Type[T]) -> ModelFactory[T]:
    """
    Create a factory for agent models.
    
    Args:
        model_class: Agent model class
        
    Returns:
        ModelFactory[T]: Agent model factory
    """
    return ModelFactory(model_class) \
        .register_field_generator('id', MockDataGenerator.random_uuid) \
        .register_field_generator('name', lambda: f"Agent {MockDataGenerator.random_string(5)}") \
        .register_field_generator('description', lambda: f"Description for agent {MockDataGenerator.random_string(10)}") \
        .register_field_generator('type', lambda: MockDataGenerator.random_choice(['RESEARCHER', 'PLANNER', 'EXECUTOR', 'REVIEWER'])) \
        .register_field_generator('project_id', MockDataGenerator.random_uuid) \
        .register_field_generator('created_at', MockDataGenerator.random_datetime) \
        .register_field_generator('updated_at', MockDataGenerator.random_datetime) \
        .register_field_generator('state', lambda: MockDataGenerator.random_choice(['CREATED', 'INITIALIZED', 'ACTIVE', 'PAUSED', 'STOPPED']))


def create_tool_factory(model_class: Type[T]) -> ModelFactory[T]:
    """
    Create a factory for tool models.
    
    Args:
        model_class: Tool model class
        
    Returns:
        ModelFactory[T]: Tool model factory
    """
    return ModelFactory(model_class) \
        .register_field_generator('id', MockDataGenerator.random_uuid) \
        .register_field_generator('name', lambda: f"Tool {MockDataGenerator.random_string(5)}") \
        .register_field_generator('description', lambda: f"Description for tool {MockDataGenerator.random_string(10)}") \
        .register_field_generator('capability', lambda: f"Capability {MockDataGenerator.random_string(5)}") \
        .register_field_generator('source', lambda: MockDataGenerator.random_choice(['INTERNAL', 'EXTERNAL', 'MCP'])) \
        .register_field_generator('created_at', MockDataGenerator.random_datetime) \
        .register_field_generator('updated_at', MockDataGenerator.random_datetime) \
        .register_field_generator('status', lambda: MockDataGenerator.random_choice(['DISCOVERED', 'APPROVED', 'DEPRECATED']))
