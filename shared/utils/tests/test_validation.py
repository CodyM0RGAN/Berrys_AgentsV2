"""
Tests for validation utilities.

This module contains tests for the validation utilities
in shared/utils/src/validation.py.
"""

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

import pytest
from pydantic import BaseModel, Field

from shared.utils.src.exceptions import ValidationError as ServiceValidationError
from shared.utils.src.validation import (
    validate_boolean,
    validate_datetime,
    validate_dict,
    validate_enum,
    validate_list,
    validate_model,
    validate_number,
    validate_string,
    validate_type,
    validate_uuid,
)


# Test models and enums
class TestStatus(str, Enum):
    """Test status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class TestSettings(BaseModel):
    """Test settings model."""
    setting1: str
    setting2: int


class TestModel(BaseModel):
    """Test model."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    status: TestStatus = Field(default=TestStatus.ACTIVE)
    count: int = Field(default=0, ge=0, le=100)
    settings: Optional[TestSettings] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, str]] = None


# Tests for validate_type
def test_validate_type():
    """Test validate_type."""
    # Valid type
    assert validate_type("test", str, "name") == "test"
    assert validate_type(123, int, "count") == 123
    assert validate_type(123.45, float, "amount") == 123.45
    assert validate_type(True, bool, "active") is True
    assert validate_type([1, 2, 3], list, "items") == [1, 2, 3]
    assert validate_type({"key": "value"}, dict, "metadata") == {"key": "value"}
    
    # None is always valid
    assert validate_type(None, str, "name") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_type(123, str, "name")
    
    with pytest.raises(ServiceValidationError):
        validate_type("123", int, "count")
    
    with pytest.raises(ServiceValidationError):
        validate_type("123.45", float, "amount")
    
    with pytest.raises(ServiceValidationError):
        validate_type(1, bool, "active")
    
    with pytest.raises(ServiceValidationError):
        validate_type("not a list", list, "items")
    
    with pytest.raises(ServiceValidationError):
        validate_type("not a dict", dict, "metadata")


# Tests for validate_string
def test_validate_string():
    """Test validate_string."""
    # Valid string
    assert validate_string("test", "name") == "test"
    
    # None is always valid
    assert validate_string(None, "name") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_string(123, "name")
    
    # String length validation
    assert validate_string("test", "name", min_length=3, max_length=10) == "test"
    
    with pytest.raises(ServiceValidationError):
        validate_string("te", "name", min_length=3)
    
    with pytest.raises(ServiceValidationError):
        validate_string("test", "name", max_length=3)
    
    # Pattern validation
    assert validate_string("test123", "name", pattern=r"^[a-z]+\d+$") == "test123"
    
    with pytest.raises(ServiceValidationError):
        validate_string("test", "name", pattern=r"^\d+$")


# Tests for validate_number
def test_validate_number():
    """Test validate_number."""
    # Valid number
    assert validate_number(123, "count") == 123
    assert validate_number(123.45, "amount") == 123.45
    
    # None is always valid
    assert validate_number(None, "count") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_number("123", "count")
    
    with pytest.raises(ServiceValidationError):
        validate_number(True, "count")
    
    # Number range validation
    assert validate_number(5, "count", min_value=0, max_value=10) == 5
    
    with pytest.raises(ServiceValidationError):
        validate_number(-1, "count", min_value=0)
    
    with pytest.raises(ServiceValidationError):
        validate_number(11, "count", max_value=10)
    
    # Integer only validation
    assert validate_number(5, "count", integer_only=True) == 5
    
    with pytest.raises(ServiceValidationError):
        validate_number(5.5, "count", integer_only=True)


# Tests for validate_boolean
def test_validate_boolean():
    """Test validate_boolean."""
    # Valid boolean
    assert validate_boolean(True, "active") is True
    assert validate_boolean(False, "active") is False
    
    # None is always valid
    assert validate_boolean(None, "active") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_boolean(1, "active")
    
    with pytest.raises(ServiceValidationError):
        validate_boolean("true", "active")


# Tests for validate_datetime
def test_validate_datetime():
    """Test validate_datetime."""
    # Valid datetime
    now = datetime.now()
    assert validate_datetime(now, "created_at") == now
    
    # Valid ISO 8601 string
    iso_string = "2025-03-27T12:00:00Z"
    result = validate_datetime(iso_string, "created_at")
    assert isinstance(result, datetime)
    assert result.year == 2025
    assert result.month == 3
    assert result.day == 27
    assert result.hour == 12
    assert result.minute == 0
    assert result.second == 0
    
    # None is always valid
    assert validate_datetime(None, "created_at") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_datetime(123, "created_at")
    
    # Invalid string format
    with pytest.raises(ServiceValidationError):
        validate_datetime("not a datetime", "created_at")


# Tests for validate_uuid
def test_validate_uuid():
    """Test validate_uuid."""
    # Valid UUID string
    uuid_str = "123e4567-e89b-12d3-a456-426614174000"
    assert validate_uuid(uuid_str, "id") == uuid_str
    
    # Valid UUID object
    uuid_obj = uuid.UUID(uuid_str)
    assert validate_uuid(uuid_obj, "id") == uuid_str
    
    # None is always valid
    assert validate_uuid(None, "id") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_uuid(123, "id")
    
    # Invalid UUID format
    with pytest.raises(ServiceValidationError):
        validate_uuid("not a uuid", "id")


# Tests for validate_enum
def test_validate_enum():
    """Test validate_enum."""
    # Valid enum value
    assert validate_enum(TestStatus.ACTIVE, TestStatus, "status") == TestStatus.ACTIVE
    
    # Valid enum name
    assert validate_enum("ACTIVE", TestStatus, "status") == TestStatus.ACTIVE
    
    # Valid enum value as string
    assert validate_enum("ACTIVE", TestStatus, "status") == TestStatus.ACTIVE
    
    # None is always valid
    assert validate_enum(None, TestStatus, "status") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_enum(123, TestStatus, "status")
    
    # Invalid enum value
    with pytest.raises(ServiceValidationError):
        validate_enum("INVALID", TestStatus, "status")


# Tests for validate_list
def test_validate_list():
    """Test validate_list."""
    # Valid list
    assert validate_list([1, 2, 3], "items") == [1, 2, 3]
    
    # None is always valid
    assert validate_list(None, "items") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_list("not a list", "items")
    
    # List length validation
    assert validate_list([1, 2, 3], "items", min_length=2, max_length=5) == [1, 2, 3]
    
    with pytest.raises(ServiceValidationError):
        validate_list([1], "items", min_length=2)
    
    with pytest.raises(ServiceValidationError):
        validate_list([1, 2, 3, 4, 5, 6], "items", max_length=5)
    
    # Item validation
    def validate_item(item, index):
        if not isinstance(item, int):
            raise ServiceValidationError(
                message=f"Item at index {index} must be an integer",
                validation_errors={f"items[{index}]": f"Expected integer, got {type(item).__name__}"}
            )
        return item
    
    assert validate_list([1, 2, 3], "items", item_validator=validate_item) == [1, 2, 3]
    
    with pytest.raises(ServiceValidationError):
        validate_list([1, "2", 3], "items", item_validator=validate_item)


# Tests for validate_dict
def test_validate_dict():
    """Test validate_dict."""
    # Valid dict
    assert validate_dict({"key": "value"}, "metadata") == {"key": "value"}
    
    # None is always valid
    assert validate_dict(None, "metadata") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_dict("not a dict", "metadata")
    
    # Required keys validation
    assert validate_dict({"key1": "value1", "key2": "value2"}, "metadata", required_keys=["key1", "key2"]) == {"key1": "value1", "key2": "value2"}
    
    with pytest.raises(ServiceValidationError):
        validate_dict({"key1": "value1"}, "metadata", required_keys=["key1", "key2"])
    
    # Key validation
    def validate_key(key):
        if not key.startswith("key_"):
            raise ServiceValidationError(
                message=f"Key must start with 'key_'",
                validation_errors={"key": f"Invalid key format: {key}"}
            )
        return key
    
    assert validate_dict({"key_1": "value1", "key_2": "value2"}, "metadata", key_validator=validate_key) == {"key_1": "value1", "key_2": "value2"}
    
    with pytest.raises(ServiceValidationError):
        validate_dict({"invalid": "value"}, "metadata", key_validator=validate_key)
    
    # Value validation
    def validate_value(value, key):
        if not isinstance(value, str):
            raise ServiceValidationError(
                message=f"Value for key {key} must be a string",
                validation_errors={key: f"Expected string, got {type(value).__name__}"}
            )
        return value
    
    assert validate_dict({"key1": "value1", "key2": "value2"}, "metadata", value_validator=validate_value) == {"key1": "value1", "key2": "value2"}
    
    with pytest.raises(ServiceValidationError):
        validate_dict({"key1": "value1", "key2": 123}, "metadata", value_validator=validate_value)


# Tests for validate_model
def test_validate_model():
    """Test validate_model."""
    # Valid model instance
    model = TestModel(
        name="Test",
        description="This is a test description",
        status=TestStatus.ACTIVE,
        count=42,
        settings=TestSettings(setting1="value1", setting2=123),
        tags=["tag1", "tag2"],
        metadata={"key": "value"}
    )
    assert validate_model(model, TestModel, "model") == model
    
    # Valid dict
    model_dict = {
        "name": "Test",
        "description": "This is a test description",
        "status": TestStatus.ACTIVE,
        "count": 42,
        "settings": {"setting1": "value1", "setting2": 123},
        "tags": ["tag1", "tag2"],
        "metadata": {"key": "value"}
    }
    result = validate_model(model_dict, TestModel, "model")
    assert isinstance(result, TestModel)
    assert result.name == model_dict["name"]
    assert result.description == model_dict["description"]
    assert result.status == model_dict["status"]
    assert result.count == model_dict["count"]
    assert result.settings.setting1 == model_dict["settings"]["setting1"]
    assert result.settings.setting2 == model_dict["settings"]["setting2"]
    assert result.tags == model_dict["tags"]
    assert result.metadata == model_dict["metadata"]
    
    # None is always valid
    assert validate_model(None, TestModel, "model") is None
    
    # Invalid type
    with pytest.raises(ServiceValidationError):
        validate_model("not a model", TestModel, "model")
    
    # Invalid dict (missing required field)
    with pytest.raises(ServiceValidationError):
        validate_model({"name": "Test"}, TestModel, "model")
    
    # Invalid dict (field validation error)
    with pytest.raises(ServiceValidationError):
        validate_model({"name": "Te", "description": "Too short"}, TestModel, "model")
