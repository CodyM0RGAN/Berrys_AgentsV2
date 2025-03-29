# Service Startup Troubleshooting Guide

**Status**: Current  
**Last Updated**: March 28, 2025  
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
- tool-integration
- planning-system
- project-coordinator
- web-dashboard

### Recent Fixes (March 28, 2025)
1. **Fixed Async/Sync Mismatch in Web Dashboard**: Modified `services/web-dashboard/app/routes/api.py` to properly handle async methods using `asyncio.run()`.
2. **Fixed PostgreSQL Authentication for pgvector**: Added the `PGPASSWORD` environment variable to the `pgvector` service in `docker-compose.yml`.
3. **Fixed Import Path Issues**: Updated import paths to use the correct modules, particularly for FastAPI/Starlette middleware.
4. **Fixed Reserved Attribute Names in SQLAlchemy Models**: Renamed `metadata` attributes in various models to avoid conflicts with SQLAlchemy's reserved names.
5. **Fixed Redis Client Compatibility Issues**: Updated Redis client code to use `redis.asyncio` instead of the deprecated `aioredis` package.
6. **Added Missing Exception Classes**: Added missing exception classes to `shared/utils/src/exceptions.py`.
7. **Fixed Circular Import in Web Dashboard**: Resolved circular import issues in the web dashboard's API module.
8. **Fixed Database Connection in Agent Orchestrator**: Modified `services/agent-orchestrator/src/database.py` to explicitly set the host to "postgres" when getting the database URL.
9. **Fixed SQL Query Errors in Agent Specialization Service**: Updated `services/agent-orchestrator/src/services/agent_specialization_service.py` to properly use SQLAlchemy's text() function for raw SQL queries.
10. **Fixed Authentication Requirement in Specializations API**: Modified `services/agent-orchestrator/src/routers/specializations.py` to make the list_specializations endpoint public by removing the authentication requirement.

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
| `ModuleNotFoundError: No module named 'fastapi.middleware.base'` | Incorrect import path | Change to `from starlette.middleware.base import BaseHTTPMiddleware` |
| `AttributeError: 'coroutine' object has no attribute 'get'` | Async method called without awaiting | Use `asyncio.run()` to run async methods in synchronous context |
| `TypeError: duplicate base class TimeoutError` | Redis client compatibility issue | Update to use `redis.asyncio` instead of `aioredis` |
| `fe_sendauth: no password supplied` | PostgreSQL authentication issue | Add `PGPASSWORD` environment variable to service configuration |
| `sqlalchemy.exc.InvalidRequestError: Attribute 'metadata' already exists` | Reserved attribute name in SQLAlchemy | Rename attribute to entity-specific name (e.g., `template_metadata`) |
| `ImportError: cannot import name 'agent_orchestrator' from partially initialized module 'app.api'` | Circular import | Restructure imports to avoid circular dependencies |
| `Database connection check failed: Multiple exceptions: [Errno 111] Connect call failed ('::1', 5432, 0, 0), [Errno 111] Connect call failed ('127.0.0.1', 5432)` | Database connection issue | Explicitly set the host parameter when getting the database URL |
| `Textual SQL expression '\\n SELECT \\n ...' should be explicitly declared as text('\\n SELECT \\n ...')` | Raw SQL query issue | Use SQLAlchemy's text() function to wrap raw SQL queries |
| `{"detail":"Not authenticated"}` | Authentication requirement | Remove authentication dependency for public endpoints |

## Service-Specific Guidance

### Agent Orchestrator

#### Common Issues
- Missing `AgentList` class in dependent services
- Missing `get_settings` function in config files
- Inconsistent model registry configuration
- Database connection issues (trying to connect to localhost instead of postgres container)
- Raw SQL queries not using SQLAlchemy's text() function
- Authentication requirements on public endpoints

#### Troubleshooting Steps
1. Check if `AgentList` class is defined in all required services
2. Verify that config.py includes a `get_settings` function
3. Ensure the service is properly registered in the model registry
4. Explicitly set the host parameter when getting the database URL:
   ```python
   # Before
   database_url = os.environ.get("DATABASE_URL") or get_async_database_url()
   
   # After
   database_url = os.environ.get("DATABASE_URL") or get_async_database_url(host="postgres")
   ```
5. Wrap raw SQL queries with SQLAlchemy's text() function:
   ```python
   # Before
   result = await self.db.execute(query, params)
   
   # After
   from sqlalchemy import text
   result = await self.db.execute(text(query), params)
   ```
6. Remove authentication requirements for public endpoints:
   ```python
   # Before
   async def list_specializations(
       current_user: Optional[UserInfo] = Depends(get_optional_user),
       specialization_service = Depends(get_agent_specialization_service),
   ) -> List[AgentSpecializationRequirement]:
   
   # After
   async def list_specializations(
       specialization_service = Depends(get_agent_specialization_service),
   ) -> List[AgentSpecializationRequirement]:
   ```

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
- Async/sync mismatches in API client calls
- Circular imports in API modules

#### Troubleshooting Steps
1. Update requirements.txt to use Pydantic v2
2. Update model configurations to use v2-style
3. Update related dependencies to be compatible with Pydantic v2
4. Use `asyncio.run()` to handle async methods in synchronous Flask routes:
   ```python
   # Before
   response_data = project_client.send_chat_message(...)
   
   # After
   import asyncio
   response_data = asyncio.run(project_client.send_chat_message(...))
   ```
5. Restructure imports to avoid circular dependencies:
   - Move shared imports to a common module
   - Use lazy imports where necessary
   - Consider using dependency injection

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
