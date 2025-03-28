# Service Boundary Adapters

This directory contains the service boundary adapters for the Berrys Agents V2 project. These adapters facilitate the conversion of entities between different service representations, ensuring consistent data flow across service boundaries.

## Overview

The adapter framework provides a standardized way to convert entities between different service representations. Each adapter is responsible for converting entities between two specific services, with bidirectional conversion methods for each entity type.

## Adapter Structure

Each adapter follows a consistent structure:

1. **Bidirectional Conversion Methods**: Each adapter provides methods for converting entities in both directions (e.g., `project_to_model` and `project_from_model`).
2. **Entity-Specific Methods**: Each adapter provides methods for each entity type (e.g., projects, agents, tasks).
3. **Validation and Error Handling**: Each adapter includes validation and error handling to ensure data integrity.
4. **Logging**: Each adapter logs transformations for debugging purposes.

## Available Adapters

The following adapters are available:

1. **WebToCoordinatorAdapter**: Converts between Web Dashboard and Project Coordinator representations
2. **CoordinatorToAgentAdapter**: Converts between Project Coordinator and Agent Orchestrator representations
3. **AgentToModelAdapter**: Converts between Agent Orchestrator and Model Orchestration representations

## Common Utilities

The adapter framework includes several common utilities:

1. **normalize_enum_value()**: Normalizes enum values across different representations
2. **AdapterValidationError**: Exception for input validation failures
3. **EntityConversionError**: Exception for conversion failures

## Usage

For detailed usage examples, see the [Adapter Usage Examples](../../../docs/developer-guides/service-development/adapter-usage-examples.md) document.

Basic usage:

```python
from shared.models.src.adapters import (
    WebToCoordinatorAdapter,
    CoordinatorToAgentAdapter,
    AgentToModelAdapter
)

# Web Dashboard → Project Coordinator
coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)

# Project Coordinator → Agent Orchestrator
agent_project = CoordinatorToAgentAdapter.project_to_agent(coordinator_project)

# Agent Orchestrator → Model Orchestration
model_project = AgentToModelAdapter.project_to_model(agent_project)
```

## Testing

The adapter framework includes comprehensive tests:

1. **Unit Tests**: Tests for each adapter
2. **Integration Tests**: Tests for the full chain of transformations

To run the tests:

```bash
cd shared/models
python run_tests.py
```

## Contributing

When adding a new adapter or modifying an existing one, please follow these guidelines:

1. **Consistent Naming**: Use the `EntityToTargetAdapter` naming pattern
2. **Bidirectional Methods**: Provide methods for both directions
3. **Entity-Specific Methods**: Provide methods for each entity type
4. **Validation**: Include input validation
5. **Error Handling**: Use the provided exception types
6. **Logging**: Log transformations for debugging
7. **Tests**: Add unit tests and integration tests

## Related Documentation

- [Model Standardization Notes](../../../docs/developer-guides/service-development/model-standardization-notes.md)
- [Entity Representation Alignment](../../../docs/developer-guides/service-development/entity-representation-alignment.md)
- [Model Mapping System](../../../docs/developer-guides/service-development/model-mapping-system.md)
