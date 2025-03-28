# API Models Package

This package contains the API models used by the Model Orchestration service.

## Structure

The package is structured as follows:

*   `__init__.py`:  Initializes the package and re-exports all modules for easy access.
*   `enums.py`: Defines all enums used in the API models.
*   `models.py`: Defines the core data models, such as `ModelBase`, `Model`, `ModelCreate`, and `ModelUpdate`.
*   `requests.py`: Defines the request models for different API endpoints (e.g., `ChatRequest`, `CompletionRequest`).
*   `responses.py`: Defines the response models for different API endpoints (e.g., `ChatResponse`, `CompletionResponse`).

## Usage

To use the API models, import them from the `services.model-orchestration.src.models.api` package. For example:

```python
from services.model_orchestration.src.models.api import Model, ChatRequest
```

This will import the `Model` and `ChatRequest` models from their respective modules.

## Contributing

When adding new API models or modifying existing ones, please follow these guidelines:

*   Place enums in `enums.py`.
*   Place core data models in `models.py`.
*   Place request models in `requests.py`.
*   Place response models in `responses.py`.
*   Update the `__all__` variable in each module to include the new models or enums.
*   Update the `__init__.py` file to re-export the new models and enums.
