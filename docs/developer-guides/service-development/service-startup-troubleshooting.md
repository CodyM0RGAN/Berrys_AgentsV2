# Service Startup Troubleshooting Guide

**Status**: Current  
**Last Updated**: March 27, 2025  
**Categories**: troubleshooting, development, reference  
**Services**: all  
**Priority**: High  

> **Navigation**: [Root](/docs) > [Developer Guides](/docs/developer-guides) > [Service Development](/docs/developer-guides/service-development) > Service Startup Troubleshooting

This guide provides a concise reference for troubleshooting service startup issues in the Berrys_AgentsV2 project. It focuses on common patterns and general solutions rather than exhaustive details of specific incidents.

## Current Status

### Running Services
- model-orchestration
- api-gateway
- agent-orchestrator

### Failing Services
- tool-integration
- planning-system
- project-coordinator
- web-dashboard

## Table of Contents
- [Common Troubleshooting Patterns](#common-troubleshooting-patterns)
- [Quick Reference Table](#quick-reference-table)
- [Service-Specific Guidance](#service-specific-guidance)
- [Best Practices](#best-practices)
- [Next Steps](#next-steps)

## Common Troubleshooting Patterns

### Import Errors

#### Symptoms
- Error messages containing `ImportError: cannot import name X from Y`
- Service fails to start immediately with import-related stack trace
- Multiple cascading import errors after fixing the first one

#### Common Root Causes
1. **Missing Classes or Functions**: Required class or function doesn't exist in the specified module
2. **Class Name Mismatches**: Class is imported with a different name than it's defined with
3. **Module Structure Changes**: Refactoring moved classes but imports weren't updated
4. **Dependency Version Mismatches**: Shared code using features from newer versions of dependencies

#### General Solutions
1. **Add Missing Components**: Define missing classes/functions in the appropriate modules
2. **Use Import Aliases**: Use `from X import Y as Z` pattern when class names don't match
3. **Update Import Paths**: Correct import statements to reflect current module structure
4. **Standardize Dependency Versions**: Ensure all services use compatible versions of shared dependencies

### Configuration Issues

#### Symptoms
- Errors related to settings, configuration, or environment variables
- Validation errors in configuration classes
- Missing configuration values

#### Common Root Causes
1. **Configuration Class Structure Changes**: Updates to shared configuration utilities
2. **Pydantic Version Mismatches**: Different services using different Pydantic versions
3. **Missing Environment Variables**: Required environment variables not set
4. **Configuration Format Changes**: Changes in how configuration is structured

#### General Solutions
1. **Standardize Configuration Pattern**: Use `BaseServiceConfig` from shared utilities consistently
2. **Update Pydantic Configuration Style**: Use v2-style `model_config = ConfigDict(...)` instead of v1-style `class Config`
3. **Add Default Values**: Provide sensible defaults for configuration values
4. **Document Required Environment Variables**: Clearly document all required environment variables

### Model Registry Issues

#### Symptoms
- Errors about missing models in the model registry
- Errors about missing fields in models
- Validation errors when converting between models

#### Common Root Causes
1. **Service Not Registered**: Service not included in the model registry
2. **Missing Model Classes**: Required model classes not defined
3. **Field Mismatches**: Fields have different names or types across services
4. **Enum Inconsistencies**: Enum values defined differently across services

#### General Solutions
1. **Register Service**: Add service to the model registry in `shared/models/src/model_registry.py`
2. **Add Missing Models**: Define missing model classes in the appropriate modules
3. **Use Adapters**: Implement adapters to handle field mismatches between services
4. **Standardize Enums**: Use shared enums from `shared/models/src/enums.py`

### Database Schema Issues

#### Symptoms
- Errors about missing tables or columns
- Constraint violations
- Type conversion errors

#### Common Root Causes
1. **Schema Drift**: Database schema doesn't match model definitions
2. **Missing Migrations**: Migrations not applied to the database
3. **Inconsistent Column Types**: Different column types across services
4. **Reserved Names**: Using reserved names for columns

#### General Solutions
1. **Create Migrations**: Create and apply Alembic migrations for schema changes
2. **Use StandardModel**: Inherit from `StandardModel` for consistent base fields
3. **Use Utility Functions**: Use `enum_column()` for enum columns
4. **Follow Naming Conventions**: Use entity-specific prefixes for metadata columns

## Quick Reference Table

| Error Pattern | Likely Cause | Quick Solution |
|---------------|--------------|----------------|
| `ImportError: cannot import name 'X' from 'Y'` | Missing class/function | Add the missing component to the module |
| `ImportError: cannot import name 'field_validator' from 'pydantic'` | Pydantic version mismatch | Upgrade to Pydantic v2 in requirements.txt |
| `ValidationError: Extra inputs are not permitted` | Pydantic config format | Update to v2-style configuration |
| `Cannot import 'get_settings' from 'src.config'` | Missing utility function | Add the function to the config module |
| `Cannot import 'StandardResponse' from 'shared.models.src.api.responses'` | Missing response class | Add alias class for backward compatibility |
| `Cannot import 'get_base' from 'shared.models.src.base'` | Outdated model pattern | Update to use StandardModel directly |
| `relation 'X' does not exist` | Missing database table | Create and apply migration for the table |
| `column 'X' of relation 'Y' does not exist` | Missing database column | Create and apply migration for the column |

## Service-Specific Guidance

### Agent Orchestrator

#### Common Issues
- Missing `AgentList` class in dependent services
- Missing `get_settings` function in config files
- Inconsistent model registry configuration

#### Troubleshooting Steps
1. Check if `AgentList` class is defined in all required services
2. Verify that config.py includes a `get_settings` function
3. Ensure the service is properly registered in the model registry

### Model Orchestration

#### Common Issues
- Missing shared model classes (e.g., `ChatMessage`)
- Import errors for response models
- Inconsistent enum usage

#### Troubleshooting Steps
1. Check if required shared models are defined in shared/models/src
2. Verify that response models are correctly imported
3. Ensure enums are imported from shared/models/src/enums.py

### Project Coordinator

#### Common Issues
- Outdated model patterns using `get_base()`, `json_column()`, etc.
- Field name mismatches in repository methods
- Missing model classes

#### Troubleshooting Steps
1. Update model definitions to use `StandardModel` directly
2. Check field names in repository methods against model definitions
3. Add any missing model classes

### Web Dashboard

#### Common Issues
- Pydantic version mismatches
- Outdated Pydantic configuration style
- Dependency version conflicts

#### Troubleshooting Steps
1. Update requirements.txt to use Pydantic v2
2. Update model configurations to use v2-style
3. Update related dependencies to be compatible with Pydantic v2

### Tool Integration

#### Common Issues
- Missing enum definitions
- Class name mismatches between imports and definitions
- Missing model classes
- Configuration format issues

#### Troubleshooting Steps
1. Add missing enums to shared/models/src/enums.py
2. Use import aliases to handle class name mismatches
3. Add missing model classes or create aliases
4. Update configuration to use BaseServiceConfig

### Planning System

#### Common Issues
- Configuration class name mismatches
- Missing response class imports
- Missing model aliases

#### Troubleshooting Steps
1. Update imports to use the correct configuration class name
2. Add missing response class imports
3. Create aliases for backward compatibility

## Best Practices

### Preventing Startup Issues

1. **Standardize Import Patterns**
   - Use consistent import patterns across services
   - Prefer importing from shared modules when possible
   - Use explicit imports rather than wildcard imports

2. **Implement Graceful Fallbacks**
   - Add fallback mechanisms for missing components
   - Provide meaningful error messages
   - Log detailed information about startup failures

3. **Maintain Compatibility Layers**
   - Add alias classes for backward compatibility
   - Document deprecated patterns and their replacements
   - Implement bridge modules for major refactorings

4. **Follow Naming Conventions**
   - Use consistent naming across services
   - Follow the established patterns for model classes
   - Use descriptive names that reflect the purpose

5. **Document Dependencies**
   - Clearly document all dependencies and their versions
   - Use version ranges rather than exact versions when possible
   - Document any version constraints or incompatibilities

## Next Steps

1. **Implement Automated Startup Tests**
   - Add tests to verify service startup as part of CI/CD
   - Create smoke tests for basic functionality
   - Implement integration tests for cross-service dependencies

2. **Enhance Model Registry**
   - Implement a more robust model registry system
   - Add graceful handling for missing models
   - Provide clear error messages for model mismatches

3. **Standardize Configuration Management**
   - Document standard patterns for service configuration
   - Create templates for new services
   - Implement validation for configuration values

4. **Dependency Management System**
   - Create a system to ensure compatible dependency versions
   - Implement version constraints for critical dependencies
   - Document dependency relationships

## Related Documents

### Prerequisites
- [Service Standardization Plan](/docs/developer-guides/service-development/service-standardization-plan.md) - Understand the standardization efforts
- [Model Standardization Progress](/docs/developer-guides/service-development/model-standardization-progress.md) - Current status of model standardization

### Next Steps
- [Troubleshooting Guide](/docs/developer-guides/service-development/troubleshooting-guide.md) - Comprehensive guide for all types of issues
- [Service Migration Guide](/docs/developer-guides/service-development/service-migration-guide.md) - Guide for migrating services to use shared components

### Reference
- [Service Development Guide](/docs/developer-guides/service-development/index.md) - Guide for developing new services
- [Design Patterns](/docs/developer-guides/service-development/design-patterns.md) - Common design patterns used in the system
