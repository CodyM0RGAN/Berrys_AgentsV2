# Model Orchestration Service

The Model Orchestration service provides a unified API for interacting with various AI model providers, including OpenAI, Anthropic, and Ollama. It handles model registration, discovery, and request processing, as well as token counting, cost tracking, and fallback mechanisms.

## Features

- **Model Management**: Register, discover, update, and delete models
- **Request Processing**: Process chat, completion, embedding, image generation, and audio requests
- **Provider Abstraction**: Unified API across different providers (OpenAI, Anthropic, Ollama)
- **Token Counting**: Count tokens for requests to ensure they don't exceed model limits
- **Cost Tracking**: Track costs for model usage
- **Fallback Mechanisms**: Automatically fall back to alternative models if primary model fails
- **Caching**: Cache responses for improved performance and reduced costs
- **Streaming**: Stream responses for improved user experience
- **Metrics**: Track usage metrics for monitoring and billing

## Architecture

The service follows a clean architecture pattern with the following components:

- **API Models**: Pydantic models for request/response validation
- **Database Models**: SQLAlchemy models for data persistence
- **Providers**: Provider implementations for different AI model providers
- **Services**: Business logic for model operations
- **Routers**: FastAPI routers for API endpoints
- **Dependencies**: Dependency injection for services and database access

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Docker (optional)

### Environment Variables

Create a `.env` file in the service root directory with the following variables:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mas_framework
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OLLAMA_URL=http://localhost:11434
JWT_SECRET=your_jwt_secret
ENVIRONMENT=development
```

### Installation

#### Using Docker

```bash
docker-compose up -d model-orchestration
```

#### Manual Installation

```bash
cd services/model-orchestration
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## API Endpoints

### Model Management

- `POST /api/models`: Register a new model
- `GET /api/models`: List models
- `GET /api/models/{model_id}`: Get model details
- `PUT /api/models/{model_id}`: Update model
- `DELETE /api/models/{model_id}`: Delete model

### Request Processing

- `POST /api/models/chat`: Process chat request
- `POST /api/models/completion`: Process completion request
- `POST /api/models/embedding`: Process embedding request
- `POST /api/models/image`: Process image generation request
- `POST /api/models/audio/transcription`: Process audio transcription request
- `POST /api/models/audio/translation`: Process audio translation request

## Testing

### Running Tests

#### Windows

```bash
run_tests.bat
```

#### Linux/macOS

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Test Coverage

The test suite includes:

- Unit tests for all components
- Integration tests for API endpoints
- Provider-specific tests
- Error handling tests

## Development

### Adding a New Provider

1. Create a new provider implementation in `src/providers/`
2. Implement the `ModelProvider` interface
3. Register the provider in `src/providers/provider_factory.py`

### Adding a New Capability

1. Update the `ModelCapability` enum in `src/models/api.py`
2. Add the corresponding request/response models
3. Implement the capability in the provider implementations
4. Add the corresponding endpoint in `src/routers/models.py`

## Integration with Other Services

The Model Orchestration service integrates with other services in the system through:

- **Event Bus**: Publishes events for model operations
- **Command Bus**: Receives commands from other services
- **API**: Provides a REST API for other services to consume

## Troubleshooting

### Common Issues

- **API Key Issues**: Ensure that the API keys for the providers are correctly set in the environment variables
- **Database Connection Issues**: Check the database connection string and ensure the database is running
- **Redis Connection Issues**: Check the Redis connection string and ensure Redis is running
- **Provider Availability Issues**: Check the provider status and ensure the provider is available

### Logs

Logs are available in the `logs/` directory and are rotated daily.

## License

This project is licensed under the terms of the LICENSE file included in the repository.
