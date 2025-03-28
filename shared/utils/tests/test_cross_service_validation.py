"""
Tests for cross-service validation utilities.

This module contains tests for the cross-service validation utilities
in shared/utils/src/cross_service_validation.py.
"""

import asyncio
import pytest
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError

from shared.utils.src.cross_service_validation import (
    CrossServiceValidationError,
    create_field_validator,
    create_validators_from_model,
    validate_cross_service_request,
    validate_service_response,
    validate_project_id,
    validate_agent_id,
    validate_task_id,
    validate_model_id,
    validate_tool_id,
    validate_user_id,
    validate_plan_id,
)
from shared.utils.src.exceptions import ValidationError as ServiceValidationError


# Test models
class TestStatus(str, Enum):
    """Test status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class TestSettings(BaseModel):
    """Test settings model."""
    setting1: str
    setting2: int


class TestRequest(BaseModel):
    """Test request model."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    status: TestStatus = Field(default=TestStatus.ACTIVE)
    count: int = Field(default=0, ge=0, le=100)
    settings: Optional[TestSettings] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class TestResponse(BaseModel):
    """Test response model."""
    id: str
    name: str
    description: str
    status: TestStatus
    count: int
    created_at: datetime
    updated_at: datetime
    settings: Optional[TestSettings] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


# Test client class
class TestClient:
    """Test client class."""
    
    @validate_cross_service_request(
        target_service="test-service",
        request_model=TestRequest
    )
    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test item."""
        # Simulate a successful response
        return {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": item_data["name"],
            "description": item_data["description"],
            "status": item_data["status"].value if isinstance(item_data["status"], TestStatus) else item_data["status"],
            "count": item_data["count"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "settings": item_data.get("settings"),
            "tags": item_data.get("tags", []),
            "metadata": item_data.get("metadata")
        }
    
    @validate_cross_service_request(
        target_service="test-service",
        field_validators={
            "name": lambda value: value if isinstance(value, str) and 3 <= len(value) <= 100 else None,
            "count": lambda value: value if isinstance(value, int) and 0 <= value <= 100 else None,
        }
    )
    async def update_item(self, item_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a test item."""
        # Simulate a successful response
        return {
            "id": item_id,
            "name": item_data.get("name", "Default Name"),
            "description": item_data.get("description", "Default Description"),
            "status": item_data.get("status", TestStatus.ACTIVE.value),
            "count": item_data.get("count", 0),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "settings": item_data.get("settings"),
            "tags": item_data.get("tags", []),
            "metadata": item_data.get("metadata")
        }
    
    @validate_service_response(
        source_service="test-service",
        response_model=TestResponse
    )
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a test item."""
        # Simulate a successful response
        return {
            "id": item_id,
            "name": "Test Item",
            "description": "This is a test item",
            "status": TestStatus.ACTIVE.value,
            "count": 42,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "settings": {"setting1": "value1", "setting2": 123},
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
        }
    
    @validate_service_response(
        source_service="test-service",
        field_validators={
            "id": lambda value: value if isinstance(value, str) else None,
            "name": lambda value: value if isinstance(value, str) and 3 <= len(value) <= 100 else None,
        }
    )
    async def get_item_with_field_validators(self, item_id: str) -> Dict[str, Any]:
        """Get a test item with field validators."""
        # Simulate a successful response
        return {
            "id": item_id,
            "name": "Test Item",
            "description": "This is a test item",
            "status": TestStatus.ACTIVE.value,
            "count": 42,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "settings": {"setting1": "value1", "setting2": 123},
            "tags": ["tag1", "tag2"],
            "metadata": {"key": "value"}
        }


# Tests for validate_cross_service_request decorator
@pytest.mark.asyncio
async def test_validate_cross_service_request_with_valid_data():
    """Test validate_cross_service_request with valid data."""
    client = TestClient()
    
    # Valid data
    item_data = {
        "name": "Test Item",
        "description": "This is a test item with a valid description",
        "status": TestStatus.ACTIVE,
        "count": 42,
        "settings": {"setting1": "value1", "setting2": 123},
        "tags": ["tag1", "tag2"],
        "metadata": {"key": "value"}
    }
    
    # Should not raise an exception
    result = await client.create_item(item_data)
    
    # Verify the result
    assert result["name"] == item_data["name"]
    assert result["description"] == item_data["description"]
    assert result["status"] == item_data["status"].value
    assert result["count"] == item_data["count"]
    assert result["settings"] == item_data["settings"]
    assert result["tags"] == item_data["tags"]
    assert result["metadata"] == item_data["metadata"]


@pytest.mark.asyncio
async def test_validate_cross_service_request_with_invalid_data():
    """Test validate_cross_service_request with invalid data."""
    client = TestClient()
    
    # Invalid data
    item_data = {
        "name": "Te",  # Too short
        "description": "Too short",  # Too short
        "status": "INVALID_STATUS",  # Invalid status
        "count": 101,  # Too large
        "settings": {"setting1": "value1"},  # Missing setting2
        "tags": [123],  # Invalid tag type
        "metadata": {"key": "value"}
    }
    
    # Should raise a ValidationError
    with pytest.raises(ServiceValidationError):
        await client.create_item(item_data)


@pytest.mark.asyncio
async def test_validate_cross_service_request_with_field_validators():
    """Test validate_cross_service_request with field validators."""
    client = TestClient()
    
    # Valid data
    item_data = {
        "name": "Test Item",
        "count": 42,
    }
    
    # Should not raise an exception
    result = await client.update_item("123", item_data)
    
    # Verify the result
    assert result["name"] == item_data["name"]
    assert result["count"] == item_data["count"]
    
    # Invalid data
    invalid_data = {
        "name": "Te",  # Too short
        "count": 101,  # Too large
    }
    
    # Should raise a ValidationError
    with pytest.raises(ServiceValidationError):
        await client.update_item("123", invalid_data)


# Tests for validate_service_response decorator
@pytest.mark.asyncio
async def test_validate_service_response_with_valid_data():
    """Test validate_service_response with valid data."""
    client = TestClient()
    
    # Should not raise an exception
    result = await client.get_item("123")
    
    # Verify the result
    assert result.id == "123"
    assert result.name == "Test Item"
    assert result.description == "This is a test item"
    assert result.status == TestStatus.ACTIVE
    assert result.count == 42
    assert result.settings.setting1 == "value1"
    assert result.settings.setting2 == 123
    assert result.tags == ["tag1", "tag2"]
    assert result.metadata == {"key": "value"}


@pytest.mark.asyncio
async def test_validate_service_response_with_field_validators():
    """Test validate_service_response with field validators."""
    client = TestClient()
    
    # Should not raise an exception
    result = await client.get_item_with_field_validators("123")
    
    # Verify the result
    assert result["id"] == "123"
    assert result["name"] == "Test Item"


# Tests for entity ID validators
def test_validate_project_id():
    """Test validate_project_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_project_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_project_id(invalid_id)


def test_validate_agent_id():
    """Test validate_agent_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_agent_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_agent_id(invalid_id)


def test_validate_task_id():
    """Test validate_task_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_task_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_task_id(invalid_id)


def test_validate_model_id():
    """Test validate_model_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_model_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_model_id(invalid_id)


def test_validate_tool_id():
    """Test validate_tool_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_tool_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_tool_id(invalid_id)


def test_validate_user_id():
    """Test validate_user_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_user_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_user_id(invalid_id)


def test_validate_plan_id():
    """Test validate_plan_id."""
    # Valid UUID
    valid_id = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_plan_id(valid_id) == valid_id
    
    # Invalid UUID
    invalid_id = "not-a-uuid"
    with pytest.raises(ServiceValidationError):
        validate_plan_id(invalid_id)


# Tests for create_field_validator
def test_create_field_validator_string():
    """Test create_field_validator for string fields."""
    validator = create_field_validator(str, "name", min_length=3, max_length=100)
    
    # Valid string
    assert validator("Test") == "Test"
    
    # Invalid string (too short)
    with pytest.raises(ServiceValidationError):
        validator("Te")
    
    # Invalid string (too long)
    with pytest.raises(ServiceValidationError):
        validator("T" * 101)
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validator(123)


def test_create_field_validator_int():
    """Test create_field_validator for integer fields."""
    validator = create_field_validator(int, "count", min_value=0, max_value=100)
    
    # Valid integer
    assert validator(42) == 42
    
    # Invalid integer (too small)
    with pytest.raises(ServiceValidationError):
        validator(-1)
    
    # Invalid integer (too large)
    with pytest.raises(ServiceValidationError):
        validator(101)
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validator("not an integer")


def test_create_field_validator_enum():
    """Test create_field_validator for enum fields."""
    validator = create_field_validator(TestStatus, "status")
    
    # Valid enum value
    assert validator(TestStatus.ACTIVE) == TestStatus.ACTIVE
    
    # Valid enum string value
    assert validator("ACTIVE") == "ACTIVE"
    
    # Invalid enum value
    with pytest.raises(ServiceValidationError):
        validator("INVALID_STATUS")
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validator(123)


def test_create_field_validator_model():
    """Test create_field_validator for model fields."""
    validator = create_field_validator(TestSettings, "settings")
    
    # Valid model
    valid_settings = TestSettings(setting1="value1", setting2=123)
    assert validator(valid_settings) == valid_settings
    
    # Valid dict
    valid_dict = {"setting1": "value1", "setting2": 123}
    assert validator(valid_dict) == valid_dict
    
    # Invalid dict (missing field)
    with pytest.raises(ServiceValidationError):
        validator({"setting1": "value1"})
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validator("not a model")


def test_create_field_validator_list():
    """Test create_field_validator for list fields."""
    validator = create_field_validator(List[str], "tags")
    
    # Valid list
    assert validator(["tag1", "tag2"]) == ["tag1", "tag2"]
    
    # Invalid list (invalid item type)
    with pytest.raises(ServiceValidationError):
        validator(["tag1", 123])
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validator("not a list")


# Tests for create_validators_from_model
def test_create_validators_from_model():
    """Test create_validators_from_model."""
    validators = create_validators_from_model(TestRequest)
    
    # Check that all fields have validators
    assert "name" in validators
    assert "description" in validators
    assert "status" in validators
    assert "count" in validators
    assert "settings" in validators
    assert "tags" in validators
    assert "metadata" in validators
    
    # Test name validator
    assert validators["name"]("Test") == "Test"
    with pytest.raises(ServiceValidationError):
        validators["name"]("Te")
    
    # Test description validator
    assert validators["description"]("This is a valid description") == "This is a valid description"
    with pytest.raises(ServiceValidationError):
        validators["description"]("Too short")
    
    # Test status validator
    assert validators["status"](TestStatus.ACTIVE) == TestStatus.ACTIVE
    with pytest.raises(ServiceValidationError):
        validators["status"]("INVALID_STATUS")
    
    # Test count validator
    assert validators["count"](42) == 42
    with pytest.raises(ServiceValidationError):
        validators["count"](101)
    
    # Test settings validator
    valid_settings = TestSettings(setting1="value1", setting2=123)
    assert validators["settings"](valid_settings) == valid_settings
    with pytest.raises(ServiceValidationError):
        validators["settings"]({"setting1": "value1"})
    
    # Test tags validator
    assert validators["tags"](["tag1", "tag2"]) == ["tag1", "tag2"]
    with pytest.raises(ServiceValidationError):
        validators["tags"](["tag1", 123])
    
    # Test metadata validator
    assert validators["metadata"]({"key": "value"}) == {"key": "value"}
    assert validators["metadata"](None) is None
