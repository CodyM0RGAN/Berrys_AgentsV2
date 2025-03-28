# Model Orchestration Service Standardization Implementation

**Status:** COMPLETED
**Last Updated:** 2025-03-27

[Home](../../README.md) > [Developer Guides](../index.md) > [Service Development](./index.md) > Model Orchestration Standardization Implementation

## Table of Contents
- [Overview](#overview)
- [Current Issues](#current-issues)
- [Implementation Plan](#implementation-plan)
  - [1. Update Internal Models](#1-update-internal-models)
  - [2. Update API Models](#2-update-api-models)
  - [3. Centralize UUID Type Implementation](#3-centralize-uuid-type-implementation)
  - [4. Set Up Alembic Migration Infrastructure](#4-set-up-alembic-migration-infrastructure)
  - [5. Create Migration Script](#5-create-migration-script)
- [Implementation Details](#implementation-details)
  - [1. UUID Type Implementation](#1-uuid-type-implementation)
  - [2. Enum Standardization](#2-enum-standardization)
  - [3. Table Renaming](#3-table-renaming)
  - [4. Migration Script](#4-migration-script)
- [Testing](#testing)
- [Next Steps](#next-steps)
- [Related Documents](#related-documents)

# Model Orchestration Service Standardization Implementation

This document outlines the implementation details for standardizing the Model Orchestration service as part of the Service Standardization Initiative.

## Overview

The Model Orchestration service standardization follows the guidelines established in the [Service Standardization Guide](service-standardization-guide.md) and [Enum Standardization](enum_standardization.md) documents. The implementation includes:

1. Centralizing the UUID type implementation
2. Standardizing enum usage
3. Renaming tables from plural to singular
4. Adding validation for case-insensitive enum values

## Current Issues

Based on the assessment of the Model Orchestration service, the following issues needed to be addressed:

1. **Enum Inconsistencies**:
   - Local enum definitions in `api.py` with **lowercase** values (e.g., `ModelStatus.ACTIVE = "active"`)
   - Direct `Enum()` usage in SQLAlchemy models
   - No enum validation in place

2. **Table Naming**:
   - Plural table names (e.g., `models` instead of `model`)

3. **Custom UUID Implementation**:
   - Custom UUID type implementation that should be centralized in `shared/utils/src/database.py`

4. **Missing Alembic Setup**:
   - No Alembic migration infrastructure in place

## Implementation Plan

### 1. Update Internal Models

1. Replace direct `Enum()` usage with string columns:
   ```python
   # Before
   status = Column(Enum(ModelStatus), nullable=False, default=ModelStatus.ACTIVE)
   
   # After
   status = Column(String(20), nullable=False, default=ModelStatus.ACTIVE.value)
   ```

2. Add validation using `EnumColumnMixin`:
   ```python
   class ModelModel(EnumColumnMixin, Base):
       # ...
       __enum_columns__ = {
           'status': ModelStatus,
           'provider': ModelProvider
       }
   ```

3. Rename tables from plural to singular:
   ```python
   # Before
   __tablename__ = "models"
   
   # After
   __tablename__ = "model"
   ```

4. Update foreign key references to use singular table names:
   ```python
   # Before
   model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
   
   # After
   model_id = Column(UUID(as_uuid=True), ForeignKey("model.id"), nullable=False)
   ```

### 2. Update API Models

1. Replace local enum definitions with imports from shared models:
   ```python
   # Before
   class ModelStatus(str, Enum):
       ACTIVE = "active"
       INACTIVE = "inactive"
       DEPRECATED = "deprecated"
   
   # After
   from shared.models.src.enums import ModelStatus
   ```

2. Update validation logic for uppercase values:
   ```python
   @validator('status', pre=True)
   def validate_status(cls, v):
       if isinstance(v, str):
           # Convert to uppercase for case-insensitive matching
           v_upper = v.upper()
           # Try to match with enum values
           for enum_value in ModelStatus:
               if enum_value.value == v_upper:
                   return enum_value
       return v
   ```

### 3. Centralize UUID Type Implementation

1. Move the custom UUID implementation to `shared/utils/src/database.py`:
   ```python
   # Add to shared/utils/src/database.py
   class UUID(TypeDecorator):
       """Platform-independent UUID type.
       
       Uses PostgreSQL's UUID type when available, otherwise uses String(36).
       """
       # ... implementation details ...
   ```

2. Update the Model Orchestration service to use the shared UUID implementation:
   ```python
   # Before
   from .api import ModelProvider, ModelCapability, ModelStatus, RequestType
   
   # After
   from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus, RequestType
   from shared.utils.src.database import UUID
   ```

### 4. Set Up Alembic Migration Infrastructure

1. Create Alembic configuration:
   ```bash
   cd services/model-orchestration
   alembic init migrations
   ```

2. Configure Alembic to use the correct database URL and models:
   ```python
   # In alembic.ini
   sqlalchemy.url = postgresql://sa:sa@localhost/mas_framework
   
   # In migrations/env.py
   from services.model-orchestration.src.models.internal import Base
   target_metadata = Base.metadata
   ```

### 5. Create Migration Script

1. Create a migration script for table renames, enum value conversions, and check constraints:
   ```python
   # Configuration variables
   TABLE_RENAMES = [
       ('models', 'model'),
       ('requests', 'request'),
       ('provider_quotas', 'provider_quota'),
   ]
   
   ENUM_CONSTRAINTS = [
       ('model', 'status', 'model_status_check', 
        ['ACTIVE', 'INACTIVE', 'DEPRECATED']),
       ('model', 'provider', 'model_provider_check',
        ['OPENAI', 'ANTHROPIC', 'OLLAMA', 'CUSTOM']),
       ('request', 'request_type', 'request_type_check',
        ['CHAT', 'COMPLETION', 'EMBEDDING', 'IMAGE_GENERATION', 'AUDIO_TRANSCRIPTION', 'AUDIO_TRANSLATION']),
       ('request', 'provider', 'request_provider_check',
        ['OPENAI', 'ANTHROPIC', 'OLLAMA', 'CUSTOM']),
       ('provider_quota', 'provider', 'provider_quota_provider_check',
        ['OPENAI', 'ANTHROPIC', 'OLLAMA', 'CUSTOM']),
   ]
   
   UPPERCASE_CONVERSIONS = [
       ('model', 'status'),
       ('model', 'provider'),
       ('request', 'request_type'),
       ('request', 'provider'),
       ('provider_quota', 'provider'),
   ]
   ```

2. Implement the upgrade and downgrade functions:
   ```python
   def upgrade():
       """
       Upgrade to standardized enums and table names:
       1. Rename tables from plural to singular
       2. Convert existing data from lowercase to uppercase
       3. Add check constraints for enum values
       """
       # ... implementation details ...
   
   def downgrade():
       """
       Downgrade from standardized enums and table names:
       1. Remove check constraints
       2. Convert data from uppercase to lowercase (if needed)
       3. Rename tables from singular to plural
       """
       # ... implementation details ...
   ```

## Implementation Details

### 1. UUID Type Implementation

The UUID type implementation has been centralized in the `shared/utils/src/database.py` file. This provides a consistent UUID handling across different database backends:

```python
class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    This implementation ensures consistent UUID handling across different database backends.
    """
    impl = String
    cache_ok = True

    def __init__(self, as_uuid=True):
        """Initialize the UUID type.
        
        Args:
            as_uuid: Whether to return Python uuid.UUID objects (True) or strings (False)
        """
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        """Load the dialect-specific implementation."""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        """Process the value before binding to a statement."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        """Process the value retrieved from the database."""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if not isinstance(value, uuid.UUID) and self.as_uuid and value is not None:
                try:
                    return uuid.UUID(value)
                except (ValueError, TypeError):
                    return value
            return value
```

### 2. Enum Standardization

The Model Orchestration service now uses shared enums from `shared.models.src.enums` instead of local enum definitions:

```python
# Import shared enums
from shared.models.src.enums import ModelProvider, ModelCapability, ModelStatus, RequestType
```

Validators have been added to handle case-insensitive string values:

```python
@validator('provider', 'status', pre=True)
def validate_enums(cls, v, values, field):
    if isinstance(v, str):
        # Convert to uppercase for case-insensitive matching
        v_upper = v.upper()
        
        # Determine which enum to use based on field name
        enum_class = None
        if field.name == 'provider':
            enum_class = ModelProvider
        elif field.name == 'status':
            enum_class = ModelStatus
        
        if enum_class:
            # Try to match with enum values
            for enum_value in enum_class:
                if enum_value.value == v_upper:
                    return enum_value
            
            # If no match, let Pydantic handle the validation error
    return v
```

### 3. Table Renaming

Tables have been renamed from plural to singular:

| Old Name (Plural) | New Name (Singular) |
|-------------------|---------------------|
| models            | model               |
| requests          | request             |
| provider_quotas   | provider_quota      |

This change is implemented in both the SQLAlchemy models and the migration script:

```python
# In SQLAlchemy models
class ModelModel(Base, EnumColumnMixin):
    __tablename__ = "model"
    # ...

class RequestModel(Base, EnumColumnMixin):
    __tablename__ = "request"
    # ...

class ProviderQuotaModel(Base, EnumColumnMixin):
    __tablename__ = "provider_quota"
    # ...
```

### 4. Migration Script

A migration script has been created to handle the database changes:

```python
# Configuration variables
# Table renames (plural to singular)
TABLE_RENAMES = [
    ('models', 'model'),
    ('requests', 'request'),
    ('provider_quotas', 'provider_quota'),
]

# Enum constraints to add
ENUM_CONSTRAINTS = [
    ('model', 'status', 'model_status_check', 
     ['ACTIVE', 'INACTIVE', 'DEPRECATED']),
    ('model', 'provider', 'model_provider_check',
     ['OPENAI', 'ANTHROPIC', 'OLLAMA', 'CUSTOM']),
    # ...
]

# Data conversion for lowercase to uppercase
UPPERCASE_CONVERSIONS = [
    ('model', 'status'),
    ('model', 'provider'),
    # ...
]
```

## Testing

The standardization changes have been tested to ensure:

1. Backward compatibility with existing code
2. Proper handling of case-insensitive enum values
3. Successful database migrations
4. Correct UUID handling across different database backends

## Next Steps

1. Apply similar standardization to other services
2. Update documentation to reflect the new standards
3. Ensure all team members are aware of the new standards

## Related Documents

- [Service Standardization Plan](service-standardization-plan.md)
- [Enum Standardization](enum_standardization.md)
- [Planning System Standardization Implementation](planning-system-standardization-implementation.md)
- [Model Standardization Progress](model-standardization-progress.md)

## See Also

- [Model Orchestration Migration Implementation](model-orchestration-migration-implementation.md) - Details on the migration of the Model Orchestration service.
- [Service Standardization Plan](service-standardization-plan.md) - Comprehensive plan for standardizing services.
