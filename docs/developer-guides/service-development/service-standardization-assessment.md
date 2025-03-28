# Service Standardization Assessment

> **Last Updated**: March 26, 2025
>
> This document provides a detailed assessment of each service's compliance with our standardization guidelines. It serves as a tracking tool for our standardization efforts.

## Overview

This assessment tracks the following standardization aspects for each service:

1. **Enum Standards**: Using shared enums from `shared/models/src/enums.py` with UPPERCASE values
2. **Table Naming**: Using singular table names (e.g., `agent` not `agents`)
3. **Validation**: Using enum validation utilities from `shared/utils/src/enum_validation.py`
4. **Code Patterns**: Using centralized code patterns for common functionality
5. **Migration Status**: Status of database migrations for standardization

## Service Assessment Matrix

| Service | Enum Standards | Table Naming | Validation | Code Patterns | Migration Status | Overall |
|---------|----------------|--------------|------------|---------------|------------------|---------|
| Web Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Project Coordinator | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Agent Orchestrator | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Planning System | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Model Orchestration | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Service Integration | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tool Integration | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Detailed Service Assessments

### 1. Agent Orchestrator

#### Enum Standards
- **Status**: ❌ Non-compliant
- **Issues**:
  - Defines local enums in `api.py` instead of importing from shared models
  - Uses different enum names (e.g., `AgentState` instead of `AgentStatus`)
- **Required Changes**:
  - Replace local enum definitions with imports from `shared/models/src/enums.py`
  - Map `AgentState` to `AgentStatus` and other relevant enums

#### Table Naming
- **Status**: ❌ Non-compliant
- **Issues**:
  - Uses plural table names (`agents`, `agent_templates`, etc.)
- **Required Changes**:
  - Rename tables to singular form (`agent`, `agent_template`, etc.)
  - Update all references to these tables

#### Validation
- **Status**: ❌ Non-compliant
- **Issues**:
  - No enum validation in place
  - Uses direct `Enum()` SQLAlchemy types
- **Required Changes**:
  - Add `EnumColumnMixin` or use `enum_column()` function
  - Convert `Enum()` columns to `String` with validation

#### Code Patterns
- **Status**: ❌ Non-compliant
- **Issues**:
  - Custom model conversion logic
  - Redundant API response models
- **Required Changes**:
  - Use centralized model conversion utilities
  - Adopt shared API response patterns

#### Migration Status
- **Status**: ❌ Not started
- **Required Migrations**:
  - Table renames (plural → singular)
  - Add enum check constraints
  - Data conversion if needed

### 2. Planning System

#### Enum Standards
- **Status**: ❌ Non-compliant
- **Issues**:
  - Defines local enums in `api.py` with **lowercase** values
  - Examples: `PlanStatus.DRAFT = "draft"`, `TaskStatus.IN_PROGRESS = "in_progress"`
- **Required Changes**:
  - Replace local enum definitions with imports
  - Convert lowercase values to UPPERCASE

#### Table Naming
- **Status**: ❌ Non-compliant
- **Issues**:
  - Uses plural table names (`strategic_plans`, `plan_phases`, etc.)
- **Required Changes**:
  - Rename tables to singular form (`strategic_plan`, `plan_phase`, etc.)
  - Update all references to these tables

#### Validation
- **Status**: ❌ Non-compliant
- **Issues**:
  - No enum validation in place
  - Uses direct `Enum()` SQLAlchemy types
- **Required Changes**:
  - Add `EnumColumnMixin` or use `enum_column()` function
  - Convert `Enum()` columns to `String` with validation

#### Code Patterns
- **Status**: ❌ Non-compliant
- **Issues**:
  - Custom model conversion logic
  - Redundant API response models
- **Required Changes**:
  - Use centralized model conversion utilities
  - Adopt shared API response patterns

#### Migration Status
- **Status**: ❌ Not started
- **Required Migrations**:
  - Table renames (plural → singular)
  - Add enum check constraints
  - Data conversion from lowercase to UPPERCASE

### 3. Model Orchestration

#### Enum Standards
- **Status**: ❌ Non-compliant
- **Issues**:
  - Defines local enums in `api.py` with **lowercase** values
  - Examples: `ModelStatus.ACTIVE = "active"`, `RequestType.CHAT = "chat"`
- **Required Changes**:
  - Replace local enum definitions with imports
  - Convert lowercase values to UPPERCASE

#### Table Naming
- **Status**: ✅ Compliant
- **Notes**: Already uses singular table names (`model`, `request`, etc.)

#### Validation
- **Status**: ❌ Non-compliant
- **Issues**:
  - No enum validation in place
  - Uses direct `Enum()` SQLAlchemy types
- **Required Changes**:
  - Add `EnumColumnMixin` or use `enum_column()` function
  - Convert `Enum()` columns to `String` with validation

#### Code Patterns
- **Status**: ❌ Non-compliant
- **Issues**:
  - Custom UUID type implementation
  - Custom model conversion logic
- **Required Changes**:
  - Move UUID type to shared utilities
  - Use centralized model conversion utilities

#### Migration Status
- **Status**: ❌ Not started
- **Required Migrations**:
  - Add enum check constraints
  - Data conversion from lowercase to UPPERCASE

### 4. Service Integration

#### Enum Standards
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely defines local enums instead of importing from shared models
- **Required Changes**:
  - Replace local enum definitions with imports
  - Ensure UPPERCASE values are used

#### Table Naming
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely uses plural table names
- **Required Changes**:
  - Rename tables to singular form
  - Update all references to these tables

#### Validation
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely no enum validation in place
- **Required Changes**:
  - Add `EnumColumnMixin` or use `enum_column()` function
  - Convert `Enum()` columns to `String` with validation

#### Code Patterns
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely uses custom model conversion logic
- **Required Changes**:
  - Use centralized model conversion utilities
  - Adopt shared API response patterns

#### Migration Status
- **Status**: ❌ Not started
- **Required Migrations**:
  - Table renames (plural → singular)
  - Add enum check constraints
  - Data conversion if needed

### 5. Tool Integration

#### Enum Standards
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely defines local enums instead of importing from shared models
- **Required Changes**:
  - Replace local enum definitions with imports
  - Ensure UPPERCASE values are used

#### Table Naming
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely uses plural table names
- **Required Changes**:
  - Rename tables to singular form
  - Update all references to these tables

#### Validation
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely no enum validation in place
- **Required Changes**:
  - Add `EnumColumnMixin` or use `enum_column()` function
  - Convert `Enum()` columns to `String` with validation

#### Code Patterns
- **Status**: ❌ Non-compliant
- **Issues**:
  - Likely uses custom model conversion logic
- **Required Changes**:
  - Use centralized model conversion utilities
  - Adopt shared API response patterns

#### Migration Status
- **Status**: ❌ Not started
- **Required Migrations**:
  - Table renames (plural → singular)
  - Add enum check constraints
  - Data conversion if needed

## Implementation Priorities

1. **Agent Orchestrator** (Highest Priority)
   - Most actively used in project creation flows
   - Critical for cross-service communication
   - [Detailed implementation plan](agent-orchestrator-standardization-plan.md)

2. **Planning System**
   - Extensive use of lowercase enum values
   - Complex model structure

3. **Model Orchestration**
   - Contains UUID implementation that should be centralized first
   - Lowercase enum values need standardization

4. **Service Integration & Tool Integration**
   - Lower priority but should be standardized for consistency

## Progress Tracking

| Milestone | Target Date | Status | Notes |
|-----------|-------------|--------|-------|
| Centralize UUID Type | April 5, 2025 | Not Started | Extract from Model Orchestration |
| Create Model Conversion Utilities | April 12, 2025 | Not Started | Implement in shared utils |
| Agent Orchestrator Standardization | April 26, 2025 | Not Started | Highest priority service |
| Planning System Standardization | May 17, 2025 | Not Started | Complex model structure |
| Model Orchestration Standardization | May 31, 2025 | Not Started | After UUID centralization |
| Service Integration Standardization | June 14, 2025 | Not Started | Lower priority |
| Tool Integration Standardization | June 28, 2025 | Not Started | Lower priority |
| Comprehensive Testing | July 12, 2025 | Not Started | End-to-end validation |
| Documentation & Training | July 19, 2025 | Not Started | Final phase |

## Related Documentation

- [Service Standardization Plan](service-standardization-plan.md) - Comprehensive implementation plan
- [Service Standardization Summary](service-standardization-summary.md) - Concise summary of standardization status
- [Enum Standardization Guide](enum_standardization.md) - Detailed guide on enum standardization
- [Model Standardization Progress](model-standardization-progress.md) - Progress report on model standardization
