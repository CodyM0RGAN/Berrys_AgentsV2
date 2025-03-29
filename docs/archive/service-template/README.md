# Service Template Reference Implementation

This directory contains a reference implementation for a service in the Berrys_AgentsV2 system. It provides a standardized structure and patterns that should be followed when implementing new services.

## Directory Structure

```
service-name/
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── src/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Service configuration
│   ├── dependencies.py       # Dependency injection
│   ├── exceptions.py         # Custom exceptions
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── api.py            # API request/response models
│   │   └── internal.py       # Internal data models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── resource.py       # API endpoints for resources
│   ├── services/
│   │   ├── __init__.py
│   │   └── resource_service.py # Core business logic
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── events.py         # Event definitions and handlers
│   │   └── commands.py       # Command definitions and handlers
│   └── utils/
│       ├── __init__.py
│       └── helpers.py        # Utility functions
└── tests/                    # Unit and integration tests
    ├── __init__.py
    ├── conftest.py           # Test fixtures
    ├── test_main.py          # API tests
    └── test_services/        # Service tests
        ├── __init__.py
        └── test_resource_service.py
```

## Key Components

### 1. Application Entry Point (`main.py`)

The main.py file is the entry point for the FastAPI application. It:
- Initializes the FastAPI app
- Sets up middleware
- Includes routers
- Configures exception handlers
- Defines startup and shutdown events

### 2. Configuration (`config.py`)

The config.py file defines the service configuration using Pydantic settings:
- Environment variables
- Default values
- Validation rules

### 3. Dependency Injection (`dependencies.py`)

The dependencies.py file defines FastAPI dependencies:
- Database session
- Service instances
- Authentication

### 4. Custom Exceptions (`exceptions.py`)

The exceptions.py file defines custom exception classes:
- Domain-specific exceptions
- Error codes
- HTTP status mappings

### 5. Data Models

#### API Models (`models/api.py`)

Pydantic models for API requests and responses:
- Request validation
- Response serialization
- Documentation

#### Internal Models (`models/internal.py`)

Internal data models for business logic:
- Domain entities
- Value objects
- DTOs

### 6. API Endpoints (`routers/resource.py`)

FastAPI routers for API endpoints:
- Route definitions
- Request handling
- Response formatting
- Authentication and authorization

### 7. Business Logic (`services/resource_service.py`)

Service classes for business logic:
- Domain operations
- Data access
- External service integration

### 8. Messaging

#### Events (`messaging/events.py`)

Event definitions and handlers:
- Event schemas
- Event publishing
- Event subscription

#### Commands (`messaging/commands.py`)

Command definitions and handlers:
- Command schemas
- Command handling
- Command responses

### 9. Utilities (`utils/helpers.py`)

Utility functions and helpers:
- Common operations
- Formatting
- Validation

### 10. Tests

#### Test Fixtures (`tests/conftest.py`)

Test fixtures for pytest:
- Database fixtures
- Service mocks
- Authentication fixtures

#### API Tests (`tests/test_main.py`)

Tests for API endpoints:
- Request validation
- Response validation
- Error handling

#### Service Tests (`tests/test_services/test_resource_service.py`)

Tests for service business logic:
- Unit tests
- Integration tests
- Edge cases

## Implementation Guidelines

1. **Separation of Concerns**: Keep API, business logic, and data access separate
2. **Dependency Injection**: Use FastAPI's dependency injection for services
3. **Async First**: Use async/await for all I/O operations
4. **Error Handling**: Use custom exceptions and global exception handlers
5. **Validation**: Use Pydantic models for validation
6. **Testing**: Write tests for all components
7. **Documentation**: Document all public APIs and functions
8. **Configuration**: Use environment variables for configuration
9. **Logging**: Use structured logging
10. **Monitoring**: Add metrics and health checks

## Example Files

The following files provide concrete examples of the patterns described above:

### 1. Application Entry Point (`main.py`)

The main.py file is the entry point for the FastAPI application. It:
- Initializes the FastAPI app
- Sets up middleware
- Includes routers
- Configures exception handlers
- Defines startup and shutdown events

### 2. Configuration (`config.py`)

The config.py file defines the service configuration using Pydantic settings:
- Environment variables
- Default values
- Validation rules

### 3. Custom Exceptions (`exceptions.py`)

The exceptions.py file defines custom exception classes:
- Base service error
- Resource not found error
- Validation error
- Authentication error
- External service error

### 4. Dependency Injection (`dependencies.py`)

The dependencies.py file defines FastAPI dependencies:
- Authentication dependencies
- Service dependencies
- Database session dependency

### 5. API Models (`models/api.py`)

Pydantic models for API requests and responses:
- Resource base model
- Resource create model
- Resource update model
- Resource response model
- Pagination model

### 6. Database Models (`models/internal.py`)

SQLAlchemy models for database entities:
- Resource model
- Relationship examples
- Model conversion methods

### 7. API Endpoints (`routers/resources.py`)

FastAPI router for resource endpoints:
- CRUD operations
- Pagination
- Filtering
- Authentication

### 8. Business Logic (`services/resource_service.py`)

Service class for resource operations:
- Database operations
- Business logic
- Event publishing

### 9. Event Handling (`messaging/events.py`)

Event handling for the service:
- Event handler registration
- Event handling methods
- Event publishing helpers

### 10. Command Handling (`messaging/commands.py`)

Command handling for the service:
- Command handler registration
- Command handling methods
- Command sending helpers

### 11. Utilities (`utils/helpers.py`)

Utility functions and helpers:
- JSON serialization
- Error formatting
- Pagination helpers
- Dictionary operations

### 12. Docker Configuration (`Dockerfile`)

Docker configuration for the service:
- Base image
- Dependencies installation
- Code copying
- Environment setup
- Service startup

### 13. Dependencies (`requirements.txt`)

Python dependencies for the service:
- Web framework
- Database
- Messaging
- Monitoring
- Testing
- Utilities
