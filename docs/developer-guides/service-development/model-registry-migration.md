# Model Registry Migration

> **Draft-of-Thought Documentation**: This document details the migration of the ModelRegistry class from `shared.models.src.base` to `shared.utils.src.conversion.base.interfaces` as part of the code centralization initiative, and the backward compatibility solution implemented.

## Overview

As part of the Code Centralization and Shared Component Development initiative, the `ModelRegistry` class and `register_models` function were moved from `shared.models.src.base` to `shared.utils.src.conversion.base.interfaces`. This document details the migration process, the backward compatibility solution implemented, and the lessons learned.

## Migration Details

### Original Location

The `ModelRegistry` class and `register_models` function were originally defined in:
- `shared/models/src/base.py`

### New Location

As part of the code centralization initiative, they were moved to:
- `shared/utils/src/conversion/base/interfaces.py`

### Impact

This migration caused import errors in code that was still importing from the original location, such as:
- `shared/models/src/model_registry.py`
- Tests that depend on these modules, like `shared/models/tests/adapters/test_agent_to_model.py`

## Backward Compatibility Solution

To maintain backward compatibility while allowing the codebase to transition to the new structure, we implemented a bridge module approach:

1. Created a bridge module at `shared/models/src/model_registry_bridge.py` that re-exports the `ModelRegistry` class and `register_models` function from their new location:

```python
"""
Bridge module for model registry functionality.

This module provides backward compatibility for the model registry functionality
that was moved from shared.models.src.base to shared.utils.src.conversion.base.interfaces.
"""

from shared.utils.src.conversion.base.interfaces import ModelRegistry
from shared.utils.src.conversion.base.interfaces import model_registry

def register_models(sqlalchemy_model, pydantic_model, model_type):
    """
    Register a mapping between SQLAlchemy and Pydantic models.
    
    Args:
        sqlalchemy_model: The SQLAlchemy model class
        pydantic_model: The Pydantic model class
        model_type: The type of model (e.g., 'default', 'create', 'update')
    """
    model_registry.register_entity_converter(sqlalchemy_model.__tablename__, pydantic_model)
```

2. Updated `shared/models/src/model_registry.py` to import from the bridge module:

```python
from shared.models.src.model_registry_bridge import ModelRegistry, register_models
```

3. Fixed a related issue in `AgentToModelAdapter` where it was trying to use a non-existent `ModelCapability.CODE_GENERATION` enum value:

```python
AGENT_TYPE_TO_CAPABILITY_MAP = {
    AgentType.COORDINATOR: [ModelCapability.CHAT, ModelCapability.COMPLETION],
    AgentType.ASSISTANT: [ModelCapability.CHAT, ModelCapability.COMPLETION],
    AgentType.RESEARCHER: [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.EMBEDDING],
    AgentType.DEVELOPER: [ModelCapability.CHAT, ModelCapability.COMPLETION],  # Removed CODE_GENERATION as it doesn't exist
    AgentType.DESIGNER: [ModelCapability.IMAGE_GENERATION],
    AgentType.SPECIALIST: [ModelCapability.CHAT, ModelCapability.COMPLETION],
    AgentType.AUDITOR: [ModelCapability.CHAT, ModelCapability.COMPLETION],
    AgentType.CUSTOM: [ModelCapability.CHAT, ModelCapability.COMPLETION],
}
```

4. Updated the test to match the implementation by removing the expectation for the `CODE_GENERATION` capability:

```python
self.assertEqual(model_agent["capabilities"], [ModelCapability.CHAT.value, ModelCapability.COMPLETION.value])
```

## Migration Plan

This bridge module approach is a temporary solution to maintain backward compatibility. The long-term plan is to update all imports to use the new location directly. The migration plan is as follows:

1. **Phase 1: Bridge Module (Completed)**
   - Implement bridge module for backward compatibility
   - Update tests to work with the new structure

2. **Phase 2: Update Imports (Planned)**
   - Identify all locations that import from the original location
   - Update imports to use the new location directly
   - Add deprecation warnings to the bridge module

3. **Phase 3: Remove Bridge Module (Planned)**
   - Once all imports have been updated, remove the bridge module
   - Update documentation to reflect the new structure

## Lessons Learned

1. **Import Path Changes**: When moving classes and functions as part of a refactoring initiative, it's important to consider the impact on existing imports. A bridge module approach can provide a smooth transition.

2. **Test Coverage**: Comprehensive test coverage helped identify the issue quickly. The tests failed with clear error messages that pointed to the root cause.

3. **Documentation**: Documenting the migration process and the backward compatibility solution is essential for future developers who may encounter similar issues.

4. **Enum Validation**: The `ModelCapability.CODE_GENERATION` issue highlights the importance of keeping enums consistent across the codebase. When updating enums, it's important to update all references to them.

## Related Documentation

- [Code Centralization Implementation](code-centralization-implementation.md)
- [Service Migration Guide](service-migration-guide.md)
- [Model Standardization Progress](model-standardization-progress.md)
