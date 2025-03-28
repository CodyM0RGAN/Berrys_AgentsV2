# Pydantic Best Practices Guide

This guide provides best practices for working with Pydantic in the Berrys_AgentsV2 project, including compatibility with Pydantic V2, common patterns, and optimization techniques.

## Quick Reference

- Use `model_config` instead of `Config` inner class for Pydantic V2 compatibility
- Use `from_attributes=True` instead of `orm_mode=True` for ORM integration
- Set `protected_namespaces=()` when using field names with reserved prefixes like `model_`
- Use `Field` for field validation and metadata
- Use `model_validator` instead of `root_validator` for model-level validation

## Pydantic V2 Compatibility

Pydantic V2 introduced several breaking changes that require updates to existing code. The following sections outline the key changes and how to address them.

### Protected Namespace Conflicts

Pydantic V2 introduced protected namespaces, which caused warnings for field names that start with "model_" as they conflict with the protected namespace "model_". To resolve this issue, set the `protected_namespaces` configuration to an empty tuple:

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    model_id: str
    model_name: str
    
    model_config = {
        "protected_namespaces": ()
    }
```

This configuration disables the protected namespace check for the model, allowing field names that start with "model_".

### ORM Mode Migration

Pydantic V2 renamed `orm_mode` to `from_attributes`. Update your models to use the new configuration:

```python
# Pydantic V1
class MyModel(BaseModel):
    id: str
    name: str
    
    class Config:
        orm_mode = True

# Pydantic V2
class MyModel(BaseModel):
    id: str
    name: str
    
    model_config = {
        "from_attributes": True
    }
```

### Root Validator Migration

Pydantic V2 replaced `root_validator` with `model_validator`. Update your validators to use the new decorator:

```python
# Pydantic V1
class MyModel(BaseModel):
    a: int
    b: int
    
    @root_validator
    def validate_a_b(cls, values):
        a, b = values.get('a'), values.get('b')
        if a is not None and b is not None and a > b:
            raise ValueError('a must be <= b')
        return values

# Pydantic V2
class MyModel(BaseModel):
    a: int
    b: int
    
    @model_validator(mode='after')
    def validate_a_b(self):
        if self.a > self.b:
            raise ValueError('a must be <= b')
        return self
```

Note that in Pydantic V2, the `model_validator` operates on the model instance (`self`) rather than the class (`cls`) and the values dictionary. The `mode='after'` parameter indicates that the validator should run after all fields have been validated.

### Config Class Migration

Migrate from the legacy `Config` inner class to the new `model_config` dictionary:

```python
# Pydantic V1
class MyModel(BaseModel):
    id: str
    name: str
    
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        extra = 'ignore'

# Pydantic V2
class MyModel(BaseModel):
    id: str
    name: str
    
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "extra": "ignore"
    }
```

Note: It's important to use either the `Config` inner class (for Pydantic V1) OR the `model_config` dictionary (for Pydantic V2), but not both simultaneously as this will cause a `PydanticUserError` with the message "Config" and "model_config" cannot be used together".

## Common Patterns

### Field Validation

Use `Field` for field validation and metadata:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str = Field(description="User ID")
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, lt=120)
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
```

### Model Inheritance

Use model inheritance to create specialized models:

```python
from pydantic import BaseModel

class BaseUser(BaseModel):
    id: str
    name: str
    
class AdminUser(BaseUser):
    admin_level: int
    permissions: list[str]
    
class RegularUser(BaseUser):
    subscription_level: str
```

### Model Composition

Use model composition to create complex models:

```python
from pydantic import BaseModel
from typing import Optional

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    
class User(BaseModel):
    id: str
    name: str
    address: Optional[Address] = None
```

### Field Aliases

Use field aliases to map between different naming conventions:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: str = Field(alias="userId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    
    model_config = {
        "populate_by_name": True
    }
```

### Custom Validators

Use field validators for field-level validation:

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    email: str
    
    @field_validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('email must contain @')
        return v
```

## Optimization Techniques

### Use Frozen Models

Use frozen models for immutable data:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    
    model_config = {
        "frozen": True
    }
```

### Use JSON Schema Generation

Generate JSON schema for models:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    
schema = User.model_json_schema()
```

### Use Model Dumping

Use `model_dump` to convert models to dictionaries:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    
user = User(id="123", name="John")
user_dict = user.model_dump()
```

### Use Model Copying

Use `model_copy` to create copies of models:

```python
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    
user = User(id="123", name="John")
user_copy = user.model_copy(update={"name": "Jane"})
```

## Best Practices for Berrys_AgentsV2

### API Models

Use Pydantic models for API request and response validation:

```python
from pydantic import BaseModel, Field
from typing import Optional

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    
class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    
    model_config = {
        "from_attributes": True
    }
```

### ORM Integration

Use Pydantic models with SQLAlchemy models:

```python
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

SQLBase = declarative_base()

class UserModel(SQLBase):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    
class User(BaseModel):
    id: str
    name: str
    email: str
    
    model_config = {
        "from_attributes": True
    }
    
# Convert SQLAlchemy model to Pydantic model
user_model = session.query(UserModel).first()
user = User.model_validate(user_model)
```

### Configuration Management

Use Pydantic models for configuration management:

```python
from pydantic import BaseModel, Field
from typing import Optional

class DatabaseConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    
class ApiConfig(BaseModel):
    host: str
    port: int
    debug: bool = False
    
class Settings(BaseModel):
    database: DatabaseConfig
    api: ApiConfig
    log_level: str = "INFO"
    environment: str
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "APP_",
        "protected_namespaces": ()
    }
```

## Example: Creating a New Pydantic Model

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import uuid

class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    priority: int = Field(ge=1, le=5, default=3)
    due_date: Optional[datetime] = None
    
    @field_validator('name')
    def name_must_not_contain_invalid_chars(cls, v):
        if any(c in v for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            raise ValueError('name contains invalid characters')
        return v

class Task(TaskCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    status: str = "PENDING"
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            uuid.UUID: str,
            datetime: lambda dt: dt.isoformat()
        }
    }
    
    @model_validator(mode='after')
    def validate_dates(self):
        if self.due_date is not None and self.due_date < self.created_at:
            raise ValueError('due_date must be after created_at')
        return self
```

## References

- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic V2 Model Configuration](https://docs.pydantic.dev/latest/api/config/)
- [Pydantic V2 Validators](https://docs.pydantic.dev/latest/api/functional_validators/)

## Pydantic V2 Migration

### Key Changes

-   Replaced `class Config` with `model_config` dictionary attribute.
-   Replaced `@validator` decorator with `@field_validator`.
-   Replaced `root_validator` with `@model_validator`.
-   Replaced `orm_mode = True` with `from_attributes = True`.
-   The `field` and `config` parameters are not available in Pydantic V2; use the `info` parameter instead.

### Example

```python
from pydantic import BaseModel, field_validator, model_validator

class Item(BaseModel):
    id: int
    description: str | None = None
    price: float

    @field_validator('price')
    def price_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('Price must be positive')
        return value

    @model_validator(mode='after')
    def check_description_length(self):
        if self.description and len(self.description) > 100:
            raise ValueError('Description too long')
        return self
```
