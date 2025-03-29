# Model Mapping System

This document provides a comprehensive overview of the model mapping system in the Berrys_AgentsV2 project, including diagrams and implementation details.

## Overview

The model mapping system provides a standardized way to convert between SQLAlchemy ORM models and Pydantic API models. This ensures consistency across services and simplifies data transformation.

Key components:
- Base model classes for SQLAlchemy and Pydantic models
- Model registry for mapping between model types
- Conversion utilities for transforming instances
- Standardized metadata handling

## Implementation

The model mapping system is implemented in the following files:

- `shared/models/src/base.py` - Base model classes and utilities
- `shared/models/src/model_registry.py` - Model registration and conversion
- `scripts/generate_model_diagram.py` - Diagram generation tool

## Model Hierarchy

The following diagram shows the inheritance hierarchy of the base models:

```mermaid
classDiagram
    class SQLAlchemyBaseModelMixin {
        +UUID id
        +DateTime created_at
        +DateTime updated_at
        +to_dict()
        +from_dict()
        +update_from_dict()
    }
    
    class PydanticBaseModel {
        +Config
    }
    
    class BaseModel {
        +Config
    }
    
    class EntityBase {
        +UUID id
        +DateTime created_at
        +DateTime updated_at
    }
    
    class CreateBase {
    }
    
    class UpdateBase {
        +Config
    }
    
    class ResponseBase~T~ {
        +T data
        +Optional[str] message
    }
    
    class PaginatedResponse~T~ {
        +List[T] items
        +int total
        +int page
        +int size
        +int pages
    }
    
    PydanticBaseModel <|-- BaseModel
    BaseModel <|-- EntityBase
    BaseModel <|-- CreateBase
    BaseModel <|-- UpdateBase
    BaseModel <|-- ResponseBase~T~
    BaseModel <|-- PaginatedResponse~T~
```

## Model Registry

The model registry is responsible for mapping between SQLAlchemy and Pydantic models. It provides methods for registering models and converting instances.

```mermaid
classDiagram
    class ModelRegistry {
        -Dict[Type, Dict[str, Type]] _sqlalchemy_to_pydantic
        -Dict[Type, Type] _pydantic_to_sqlalchemy
        +register(sqlalchemy_model, pydantic_model, model_type)
        +get_pydantic_model(sqlalchemy_model, model_type)
        +get_sqlalchemy_model(pydantic_model)
        +to_pydantic(sqlalchemy_instance, model_type)
        +to_sqlalchemy(pydantic_instance)
    }
    
    class SQLAlchemyModel {
        +UUID id
        +DateTime created_at
        +DateTime updated_at
        +entity_metadata
    }
    
    class PydanticModel {
        +UUID id
        +DateTime created_at
        +DateTime updated_at
        +Dict metadata
    }
    
    class CreateModel {
        +required_field
        +optional_field
    }
    
    class UpdateModel {
        +optional_field
    }
    
    ModelRegistry --> SQLAlchemyModel : maps to
    ModelRegistry --> PydanticModel : maps to
    ModelRegistry --> CreateModel : maps to
    ModelRegistry --> UpdateModel : maps to
    SQLAlchemyModel <-- PydanticModel : converts to/from
    SQLAlchemyModel <-- CreateModel : creates
    SQLAlchemyModel <-- UpdateModel : updates
```

### Registration Example

```python
# Register a model mapping
from shared.models.src.base import register_models
from app.models.project import Project  # SQLAlchemy model
from shared.models.src.project import Project as ProjectPydantic  # Pydantic model

register_models(Project, ProjectPydantic, "default")
```

### Conversion Example

```python
# Convert between SQLAlchemy and Pydantic models
from shared.models.src.base import to_pydantic, to_sqlalchemy

# SQLAlchemy to Pydantic
project_db = session.query(Project).first()
project_api = to_pydantic(project_db, "default")

# Pydantic to SQLAlchemy
project_api = ProjectPydantic(name="New Project", description="A new project")
project_db = to_sqlalchemy(project_api)
```

## Entity Relationships

The following diagram shows the relationships between the main entities in the system:

```mermaid
erDiagram
    PROJECT ||--o{ TASK : contains
    PROJECT ||--o{ AGENT : uses
    PROJECT ||--o{ TOOL : uses
    PROJECT ||--o{ MODEL : uses
    AGENT ||--o{ TASK : performs
    AGENT ||--o{ TOOL : uses
    TASK ||--o{ TASK : depends-on
    TASK }|--|| USER : assigned-to
    USER ||--o{ PROJECT : owns
    MODEL ||--o{ REQUEST : processes
```

## Service Model Interactions

The following diagram shows how models are used across different services:

```mermaid
flowchart TD
    subgraph "Shared Models"
        SM[Shared Models]
        SM --> SE[Shared Enums]
        SM --> SB[Shared Base Models]
    end
    
    subgraph "Web Dashboard"
        WD[Web Dashboard Models]
        WD --> WDB[Web Dashboard Base]
        WDB --> SB
    end
    
    subgraph "Project Coordinator"
        PC[Project Coordinator Models]
        PC --> PCB[Project Coordinator Base]
        PCB --> SB
    end
    
    subgraph "Agent Orchestrator"
        AO[Agent Orchestrator Models]
        AO --> AOB[Agent Orchestrator Base]
        AOB --> SB
    end
    
    subgraph "Model Orchestration"
        MO[Model Orchestration Models]
        MO --> MOB[Model Orchestration Base]
        MOB --> SB
    end
    
    subgraph "API Gateway"
        AG[API Gateway Models]
        AG --> SM
    end
    
    subgraph "Model Registry"
        MR[Model Registry]
        MR --> WD
        MR --> PC
        MR --> AO
        MR --> MO
    end
    
    subgraph "Database"
        DB[(PostgreSQL Database)]
        WD --> DB
        PC --> DB
        AO --> DB
        MO --> DB
    end
```

## Model Conversion Flow

The following diagram shows the flow of data during model conversion:

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant R as Model Registry
    participant S as SQLAlchemy Model
    participant P as Pydantic Model
    participant D as Database
    
    C->>A: Send API Request
    A->>P: Validate with Pydantic
    P->>R: Convert to SQLAlchemy
    R->>S: Create SQLAlchemy Instance
    S->>D: Save to Database
    D-->>S: Return Data
    S->>R: Convert to Pydantic
    R->>P: Create Pydantic Instance
    P->>A: Return API Response
    A->>C: Send Response
```

## Metadata Handling

The model mapping system provides standardized handling of metadata fields:

```python
# In SQLAlchemy models
from shared.models.src.base import metadata_column

class Project(Base):
    __tablename__ = "project"
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    project_metadata = metadata_column("project")  # Creates a JSONB column with standard naming
```

```python
# In Pydantic models
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Standard metadata field
```

The model registry automatically converts between `project_metadata` in SQLAlchemy and `metadata` in Pydantic.

## Related Documentation

- [Model Standardization Progress](./model-standardization-progress.md) - Overall progress on model standardization
- [Model Standardization History](./model-standardization-history.md) - Historical context and lessons learned
- [Entity Representation Alignment](./entity-representation-alignment.md) - Documentation of entity differences and adapters
- [Adapter Usage Examples](./adapter-usage-examples.md) - Examples of how to use the adapters
- [SQLAlchemy Guide](../../best-practices/sqlalchemy-guide.md) - Best practices for SQLAlchemy models
- [Pydantic Guide](../../best-practices/pydantic-guide.md) - Best practices for Pydantic models
