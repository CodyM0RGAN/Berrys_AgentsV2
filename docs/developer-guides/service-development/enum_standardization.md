# Enum Standardization Guide

## Overview

This guide documents the standardization of enum values across the Berrys_AgentsV2 system. Consistent enum handling is critical for cross-service communication and database integrity.

## Key Principles

1. **Uppercase Values**: All enum string values must be in uppercase (e.g., 'PLANNING' not 'planning')
2. **Central Definition**: All enums are defined in `shared/models/src/enums.py`
3. **Database Constraints**: Database check constraints must match the enum values exactly
4. **Validation**: Use enum validation utilities for type checking

## Implementation Details

### 1. Enum Definition

All enums should be defined in `shared/models/src/enums.py` using Python's Enum class:

```python
from enum import Enum, auto

class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"
```

### 2. Enum Validation

The `shared/utils/src/enum_validation.py` module provides utilities for validating enum values:

- `EnumValidator.validate_enum()`: Validates that a value is a valid enum value
- `EnumColumnMixin`: Mixin class for adding enum validation to SQLAlchemy models
- `enum_column()`: Function to create a string column with enum validation
- `add_enum_validation()`: Function to add enum validation to an existing model class

The validation logic has been updated to:
- Accept uppercase values as the standard
- Issue a deprecation warning when lowercase values are provided
- Automatically convert lowercase values to uppercase during the transition period
- Validate against uppercase enum values in the database

Example of validation behavior:
```python
# This will work but issue a deprecation warning
project = Project(status="draft")  # Warning: Use "DRAFT" instead

# This is the preferred approach
project = Project(status="DRAFT")  # No warning

# This also works
project = Project(status=ProjectStatus.DRAFT)  # No warning
```

### 2. Database Constraints

Database tables should have check constraints that match the enum values:

```sql
ALTER TABLE project ADD CONSTRAINT project_status_check 
CHECK (status IN ('DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'ARCHIVED', 'CANCELLED'));
```

### 3. SQLAlchemy Models

SQLAlchemy models should use string columns with validation:

```python
from sqlalchemy import Column, String
from sqlalchemy.orm import validates
from shared.models.src.enums import ProjectStatus

class Project(Base):
    __tablename__ = "project"
    
    # ...other columns...
    status = Column(String(50), nullable=False, default=ProjectStatus.DRAFT.value)
    
    @validates('status')
    def validate_status(self, key, value):
        if value not in [status.value for status in ProjectStatus]:
            raise ValueError(f"Invalid status: {value}")
        return value
```

### 4. Pydantic Models

Pydantic models should use the Enum classes directly:

```python
from pydantic import BaseModel
from shared.models.src.enums import ProjectStatus

class ProjectResponse(BaseModel):
    # ...other fields...
    status: ProjectStatus
```

## Standardization Process

In March 2025, we standardized all enum values to uppercase. This involved:

1. Updating enum definitions in `shared/models/src/enums.py`
2. Creating a migration script to update database constraints
3. Converting existing data in the database to uppercase
4. Updating documentation

The SQL script for this standardization is available at `shared/database/enum_standardization_postgres.sql`.

## Affected Enums

The following enums were standardized:

1. **ProjectStatus**: DRAFT, PLANNING, IN_PROGRESS, REVIEW, COMPLETED, ARCHIVED, CANCELLED
2. **AgentStatus**: INACTIVE, ACTIVE, BUSY, ERROR, MAINTENANCE
3. **AgentType**: COORDINATOR, ASSISTANT, RESEARCHER, DEVELOPER, DESIGNER, SPECIALIST, AUDITOR, CUSTOM
4. **TaskStatus**: PENDING, ASSIGNED, IN_PROGRESS, BLOCKED, COMPLETED, FAILED, CANCELLED
5. **TaskPriority**: LOW, MEDIUM, HIGH, CRITICAL (represented as integers 1-4 in the database)
6. **ToolIntegrationType**: API, CLI, LIBRARY, SERVICE, CUSTOM
7. **ToolStatus**: ACTIVE, INACTIVE, DEPRECATED, EXPERIMENTAL

## Database Connection Note

When executing SQL scripts directly against the database, use the following credentials:

- Username: `sa` (not `postgres`)
- Database: `mas_framework`

Example:
```powershell
psql -U sa -d mas_framework -f shared/database/enum_standardization_postgres.sql
```

## Troubleshooting

### Common Issues

1. **Case Sensitivity Errors**: Ensure all enum values in code match the database constraints exactly (uppercase)
2. **Cross-Service Communication Failures**: Check that both services are using the same enum values
3. **Database Constraint Violations**: Verify that data being inserted matches the constraint values

### Resolution Steps

1. Check enum definitions in `shared/models/src/enums.py`
2. Verify database constraints match enum values
3. Ensure all services are using the latest enum definitions
4. For legacy data, convert values to uppercase before validation

## Related Documentation

- [Entity Representation Alignment](entity-representation-alignment.md)
- [Model Standardization Progress](model-standardization-progress.md)
- [Troubleshooting Guide](troubleshooting-guide.md)
- [Service Standardization Plan](service-standardization-plan.md) - Comprehensive plan for standardizing services and centralizing redundant code

## Service Standardization

While this guide focuses on enum standardization principles, we've identified that several services are not yet fully compliant with these standards. We've created a comprehensive [Service Standardization Plan](service-standardization-plan.md) that includes:

1. Assessment of current service compliance with enum standards
2. Service-by-service implementation plan for standardization
3. Database migration strategies
4. Centralization of redundant code patterns

Refer to the Service Standardization Plan for details on the implementation approach and timeline.
