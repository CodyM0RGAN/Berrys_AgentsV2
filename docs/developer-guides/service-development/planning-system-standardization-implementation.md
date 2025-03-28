# Planning System Standardization Implementation

**Status:** COMPLETED
**Last Updated:** 2025-03-27

[Home](../../README.md) > [Developer Guides](../index.md) > [Service Development](./index.md) > Planning System Standardization Implementation

## Table of Contents
- [Overview](#overview)
- [Enum Standardization](#enum-standardization)
  - [Shared Enums](#shared-enums)
- [Model Standardization](#model-standardization)
  - [Internal Models](#internal-models)
  - [API Models](#api-models)
- [Database Migration](#database-migration)
- [Running the Migrations](#running-the-migrations)
  - [Windows](#windows)
  - [Unix/Linux/macOS](#unixlinuxmacos)
- [Implementation Status](#implementation-status)
- [Next Steps](#next-steps)
- [Lessons Learned](#lessons-learned)
  - [Enum Standardization Importance](#enum-standardization-importance)
  - [Migration Approach](#migration-approach)
  - [Code Centralization Benefits](#code-centralization-benefits)

# Planning System Standardization Implementation

This document outlines the implementation of the standardization plan for the Planning System service, as described in the [Service Standardization Plan](./service-standardization-plan.md).

## Overview

The Planning System service has been standardized to follow the project-wide conventions for model representation, enum usage, and database schema. The following changes have been implemented:

1. Updated internal models to use string columns with validation instead of direct `Enum()` usage
2. Renamed tables from plural to singular (e.g., `strategic_plans` to `strategic_plan`)
3. Updated API models to use shared enums from `shared.models.src.enums` instead of local definitions
4. Added validation for enum values in both API and internal models
5. Created a migration script to rename tables, convert lowercase enum values to uppercase, and add check constraints

## Enum Standardization

### Shared Enums

The Planning System service now uses shared enums from `shared.models.src.enums` instead of local definitions:

```python
from shared.models.src.enums import TaskStatus, DependencyType, ResourceType, TaskPriority, ProjectStatus

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus
```

Note: Currently, the service uses `ProjectStatus` as a temporary substitute for `PlanStatus` since there isn't a dedicated `PlanStatus` enum in the shared enums yet. This should be replaced with a proper `PlanStatus` enum in the future.

## Model Standardization

### Internal Models

Internal models have been updated to use string columns with validation instead of direct `Enum()` usage:

```python
# Before
status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT)

# After
status = Column(String(20), default=PlanStatus.DRAFT.value)
```

The `EnumColumnMixin` is used to add validation for enum values:

```python
class StrategicPlanModel(EnumColumnMixin, Base):
    """Strategic plan database model"""
    __tablename__ = "strategic_plan"  # Renamed from plural to singular
    
    # ... other columns ...
    
    status = Column(String(20), default=PlanStatus.DRAFT.value)  # Changed from Enum to String
    
    # Define enum columns for validation
    __enum_columns__ = {
        'status': PlanStatus
    }
```

Table names have been renamed from plural to singular:

```python
# Before
__tablename__ = "strategic_plans"

# After
__tablename__ = "strategic_plan"
```

Foreign key references have been updated to use the new singular table names:

```python
# Before
plan_id = Column(UUID(as_uuid=True), ForeignKey("strategic_plans.id"), nullable=False)

# After
plan_id = Column(UUID(as_uuid=True), ForeignKey("strategic_plan.id"), nullable=False)
```

### API Models

API models have been updated to use shared enums and add validation for enum values:

```python
# Before
class PlanStatus(str, Enum):
    """Status of a strategic plan"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CANCELLED = "cancelled"

# After
from shared.models.src.enums import ProjectStatus

# Use ProjectStatus values for now, but this should be replaced with a proper PlanStatus enum
PlanStatus = ProjectStatus
```

Validators have been added to handle string values and ensure they are converted to uppercase:

```python
class StrategicPlanBase(BaseModel):
    """Base properties for a strategic plan"""
    # ... other fields ...
    status: PlanStatus = Field(PlanStatus.DRAFT, description="Plan status")
    
    # Add validator for status to handle string values
    @validator('status', pre=True)
    def validate_status(cls, v):
        if isinstance(v, str):
            # Convert to uppercase for case-insensitive matching
            v_upper = v.upper()
            # Try to match with enum values
            for enum_value in PlanStatus:
                if enum_value.value == v_upper:
                    return enum_value
            # If no match, let Pydantic handle the validation error
        return v
```

## Database Migration

A migration script has been created to:
1. Rename tables from plural to singular
2. Convert lowercase enum values to uppercase
3. Add check constraints for enum values

```python
# Configuration variables
# Table renames (plural to singular)
TABLE_RENAMES = [
    ('strategic_plans', 'strategic_plan'),
    ('plan_phases', 'plan_phase'),
    ('plan_milestones', 'plan_milestone'),
    ('planning_tasks', 'planning_task'),
    ('resource_allocations', 'resource_allocation'),
    ('timeline_forecasts', 'timeline_forecast'),
    ('bottleneck_analyses', 'bottleneck_analysis'),
    ('optimization_results', 'optimization_result'),
    ('task_dependencies', 'task_dependency'),
]

# Enum constraints to add
# Format: (table_name, column_name, constraint_name, enum_values)
ENUM_CONSTRAINTS = [
    ('strategic_plan', 'status', 'strategic_plan_status_check', 
     ['DRAFT', 'PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'ARCHIVED', 'CANCELLED']),
    
    ('plan_milestone', 'priority', 'plan_milestone_priority_check',
     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    
    ('planning_task', 'status', 'planning_task_status_check',
     ['PENDING', 'ASSIGNED', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'FAILED', 'CANCELLED']),
    
    ('planning_task', 'priority', 'planning_task_priority_check',
     ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
    
    ('resource_allocation', 'resource_type', 'resource_allocation_type_check',
     ['AGENT', 'MODEL', 'TOOL', 'COMPUTE', 'STORAGE', 'OTHER']),
    
    ('task_dependency', 'dependency_type', 'task_dependency_type_check',
     ['FINISH_TO_START', 'START_TO_START', 'FINISH_TO_FINISH', 'START_TO_FINISH']),
]

# Data conversion for lowercase to uppercase
# Format: (table_name, column_name)
UPPERCASE_CONVERSIONS = [
    ('strategic_plan', 'status'),
    ('plan_milestone', 'priority'),
    ('planning_task', 'status'),
    ('planning_task', 'priority'),
    ('resource_allocation', 'resource_type'),
    ('task_dependency', 'dependency_type'),
]
```

The migration script includes steps to:
1. Rename tables from plural to singular
2. Convert lowercase enum values to uppercase
3. Add check constraints for enum values
4. Update foreign key references

## Running the Migrations

To apply the migrations and update the database schema, follow these steps:

### Windows

```bash
cd services/planning-system/migrations
python planning_system_standardization.py
```

### Unix/Linux/macOS

```bash
cd services/planning-system/migrations
python3 planning_system_standardization.py
```

The migration script will:
1. Rename tables from plural to singular
2. Convert lowercase enum values to uppercase
3. Add check constraints for enum values
4. Update foreign key references

## Implementation Status

The Planning System service standardization is now complete. All planned changes have been implemented:

✅ Updated internal models to use string columns with validation
✅ Renamed tables from plural to singular
✅ Updated API models to use shared enums
✅ Added validation for enum values
✅ Created a migration script for database schema changes

## Next Steps

The next service to be standardized is the Model Orchestration service, as outlined in the [Service Standardization Summary](service-standardization-summary.md). The Model Orchestration service has the following issues that need to be addressed:

1. Lowercase enum values
2. Custom UUID implementation that could be centralized

After the Model Orchestration service, the Service Integration service will be standardized, followed by the Tool Integration service.

## Lessons Learned

1. **Enum Standardization Importance**:
   - Inconsistent enum handling causes integration issues
   - Case sensitivity matters for database constraints
   - Validation should happen at both API and database levels

2. **Migration Approach**:
   - Standardizing one service at a time is effective
   - Starting with the highest priority service provides immediate benefits
   - Comprehensive testing is essential after standardization

3. **Code Centralization Benefits**:
   - Reduces duplication and maintenance burden
   - Ensures consistent behavior across services
   - Makes future changes easier to implement

## See Also

- [Planning System Migration Implementation](planning-system-migration-implementation.md) - Details on the migration of the Planning System service.
- [Service Standardization Plan](service-standardization-plan.md) - Comprehensive plan for standardizing services.
