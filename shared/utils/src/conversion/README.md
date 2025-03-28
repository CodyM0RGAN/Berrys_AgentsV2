# Model Conversion Layer

This package provides a standardized way to convert between different model representations, such as SQLAlchemy ORM models and Pydantic models.

## Overview

The model conversion layer is designed to address the challenges of Phase 7 of the Model Standardization project, providing a consistent and type-safe approach to model conversion across the entire system.

Key features:
- Standard conversion interfaces for different model types
- Entity-specific converters for each entity type
- API converters for handling API models
- Robust validation and error handling
- Utility functions for common conversion tasks
- Model registry for centralized converter management

## Components

### Base Interfaces

- **ModelConverter**: Base interface for model conversion between different representations
- **EntityConverter**: Interface for converting between ORM models and Pydantic models
- **ApiConverter**: Interface for converting between internal models and API models
- **ModelRegistry**: Registry for model converters

### Entity Converters

Entity converters provide conversion between SQLAlchemy ORM models and Pydantic models for specific entities:

- **ProjectEntityConverter**: Converter for Project entities

### API Converters

API converters provide conversion between internal Pydantic models and API models for specific entities:

- **ProjectApiConverter**: Converter for Project API models

### Utility Functions

- **convert_to_pydantic**: Convert an ORM instance to a Pydantic model
- **convert_to_orm**: Convert a Pydantic model to an ORM model
- **batch_convert_to_pydantic**: Convert a list of ORM instances to Pydantic models
- **batch_convert_to_orm**: Convert a list of Pydantic models to ORM models
- **convert_enum_values**: Convert string values to enum instances
- **is_enum_type**: Check if a field type is an enum type
- **get_enum_class**: Get the enum class from a field type
- **convert_to_enum**: Convert a value to an enum instance

### Exceptions

- **ConversionError**: Base exception for conversion errors
- **ValidationError**: Exception for validation errors
- **TypeConversionError**: Exception for type conversion errors
- **MissingFieldError**: Exception for missing required fields
- **RegistrationError**: Exception for model registration errors

## Usage

### Using Entity Converters

```python
from shared.utils.src.conversion import ProjectEntityConverter

# Create a ProjectEntityConverter
converter = ProjectEntityConverter(ProjectDB)

# Convert from ORM model to Pydantic model
project_pydantic = converter.to_pydantic(project_db)

# Convert from Pydantic model to ORM model
project_db = converter.to_orm(project_pydantic)

# Convert to external representation
external_data = converter.to_external(project_db)

# Create from external representation
project_pydantic = converter.from_external(external_data)

# Update an existing ORM model
updated_project_db = converter.update_orm(project_pydantic, project_db)
```

### Using API Converters

```python
from shared.utils.src.conversion import ProjectApiConverter

# Create a ProjectApiConverter
converter = ProjectApiConverter()

# Convert from internal model to API model
project_response = converter.to_api(project_pydantic)

# Convert from API model to internal model
project_pydantic = converter.from_api(project_response)

# Convert from create request
project_pydantic = converter.from_create_request(create_request)

# Apply update request
updated_project = converter.from_update_request(update_request, project_pydantic)

# Convert to summary
project_summary = converter.to_summary(project_pydantic)
```

### Using Utility Functions

```python
from shared.utils.src.conversion import convert_to_pydantic, convert_to_orm

# Convert from ORM model to Pydantic model
project_pydantic = convert_to_pydantic(project_db, ProjectPydantic)

# Convert from Pydantic model to ORM model
project_db = convert_to_orm(project_pydantic, ProjectDB)
```

### Using the Model Registry

```python
from shared.utils.src.conversion import model_registry, ProjectEntityConverter, ProjectApiConverter

# Register converters
model_registry.register_entity_converter("project", ProjectEntityConverter(ProjectDB))
model_registry.register_api_converter("project", ProjectApiConverter())

# Get converters
entity_converter = model_registry.get_entity_converter("project")
api_converter = model_registry.get_api_converter("project")

# Use converters
project_pydantic = entity_converter.to_pydantic(project_db)
project_response = api_converter.to_api(project_pydantic)
```

## Error Handling

The conversion layer provides detailed error messages and specific exception types:

```python
from shared.utils.src.conversion import ConversionError, ValidationError

try:
    project_pydantic = converter.to_pydantic(project_db)
except ValidationError as e:
    # Handle validation errors
    print(f"Validation error: {e}")
    print(f"Source data: {e.source_data}")
except ConversionError as e:
    # Handle conversion errors
    print(f"Conversion error: {e}")
    print(f"Source data: {e.source_data}")
```

## Examples

For detailed examples, see the [conversion_layer_example.py](../../examples/conversion_layer_example.py) file.

## Related Documentation

- [Model Standardization Progress](../../../docs/developer-guides/service-development/model-standardization-progress.md)
- [Model Mapping System](../../../docs/developer-guides/service-development/model-mapping-system.md)
- [Entity Representation Alignment](../../../docs/developer-guides/service-development/entity-representation-alignment.md)
- [Adapter Usage Examples](../../../docs/developer-guides/service-development/adapter-usage-examples.md)
