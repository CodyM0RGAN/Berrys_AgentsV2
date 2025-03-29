# Service Template

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

This document provides a standardized template for creating new services in the Berrys_AgentsV2 platform. It outlines the recommended file structure, implementation patterns, and best practices for service development.

## Service Structure

A standard service should follow this directory structure:

```
service-name/
├── alembic.ini              # Database migration configuration
├── Dockerfile               # Container definition
├── README.md                # Service documentation
├── requirements.txt         # Dependencies
├── run_tests.bat/sh/ps1     # Test runners
├── logs/                    # Log directory
├── migrations/              # Database migrations
│   └── versions/            # Migration scripts
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration
│   ├── constants.py         # Constants
│   ├── dependencies.py      # Dependency injection
│   ├── exceptions.py        # Custom exceptions
│   ├── api/                 # API layer
│   │   ├── __init__.py
│   │   ├── router.py        # API routes
│   │   └── endpoints/       # Endpoint implementations
│   ├── core/                # Core domain logic
│   │   ├── __init__.py
│   │   └── services/        # Service implementations
│   ├── db/                  # Database access
│   │   ├── __init__.py
│   │   ├── models.py        # Database models
│   │   └── repositories.py  # Data access
│   ├── messaging/           # Messaging components
│   │   ├── __init__.py
│   │   ├── commands.py      # Command definitions
│   │   ├── events.py        # Event definitions
│   │   ├── publisher.py     # Event publisher
│   │   └── subscriber.py    # Event subscriber
│   ├── models/              # Data models
│   │   ├── __init__.py
│   │   ├── api.py           # API models (DTOs)
│   │   └── domain.py        # Domain models
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py       # Helper functions
└── tests/                   # Tests
    ├── __init__.py
    ├── conftest.py          # Test configuration
    ├── integration/         # Integration tests
    └── unit/                # Unit tests
```

## Key Files

### main.py

```python
#!/usr/bin/env python3
"""
Service entry point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router
from src.config import settings
from src.messaging.subscriber import start_subscribers

app = FastAPI(
    title=settings.SERVICE_NAME,
    description=settings.SERVICE_DESCRIPTION,
    version=settings.SERVICE_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Start event subscribers on app startup"""
    await start_subscribers()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

### config.py

```python
"""
Configuration settings
"""
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings"""
    # Service metadata
    SERVICE_NAME: str = "service-name"
    SERVICE_DESCRIPTION: str = "Service description"
    SERVICE_VERSION: str = "0.1.0"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Messaging settings
    REDIS_URL: str = Field(..., env="REDIS_URL")
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### dependencies.py

```python
"""
Dependency injection
"""
from typing import Generator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import Repository
from src.db.session import get_db_session
from src.core.services.service import Service

async def get_repository(
    session: AsyncSession = Depends(get_db_session)
) -> Repository:
    """Get repository dependency"""
    return Repository(session)

async def get_service(
    repository: Repository = Depends(get_repository)
) -> Service:
    """Get service dependency"""
    return Service(repository)
```

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.main"]
```

## Development Standards

### API Layer

- Use FastAPI for API definitions
- Implement proper input validation using Pydantic models
- Include comprehensive API documentation
- Follow RESTful API design principles
- Implement proper error handling and status codes

### Core Domain Logic

- Separate business logic into service classes
- Keep services focused on a single responsibility
- Implement proper error handling with custom exceptions
- Use dependency injection for external dependencies

### Data Access

- Use SQLAlchemy for database access
- Implement the repository pattern for data access
- Use Alembic for database migrations
- Keep database models separate from API models

### Messaging

- Follow the established message format for events and commands
- Use the publisher/subscriber pattern for messaging
- Implement idempotent message handling
- Include proper error handling for message processing

### Testing

- Write comprehensive unit tests for all components
- Implement integration tests for critical paths
- Use pytest for test implementation
- Mock external dependencies in unit tests

## Implementation Guidelines

### Error Handling

Implement custom exceptions for domain-specific errors:

```python
class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class ResourceNotFoundError(ServiceError):
    """Resource not found error"""
    pass

class ValidationError(ServiceError):
    """Validation error"""
    pass
```

Convert exceptions to appropriate HTTP responses:

```python
@router.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": str(exc)},
    )
```

### Event Publishing

Publish events using the standard event format:

```python
async def publish_resource_created(resource_id: str, resource_data: dict):
    """Publish resource created event"""
    event = {
        "id": str(uuid.uuid4()),
        "type": "resource.created",
        "source": settings.SERVICE_NAME,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "resource_id": resource_id,
            "resource_data": resource_data
        }
    }
    
    await publisher.publish("events", event)
```

### Event Subscription

Subscribe to events using the standard subscription pattern:

```python
@subscriber.subscribe("events", ["resource.created"])
async def handle_resource_created(event: dict):
    """Handle resource created event"""
    resource_id = event["data"]["resource_id"]
    resource_data = event["data"]["resource_data"]
    
    # Process the event
    await process_resource_created(resource_id, resource_data)
```

## References

- [System Overview](architecture/system-overview.md)
- [Communication Patterns](architecture/communication-patterns.md)
- [Message Contracts](message-contracts.md)
- [Database Schema](database-schema.md)
