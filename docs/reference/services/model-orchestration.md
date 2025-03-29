# Model Orchestration Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Model Orchestration service manages interactions between agents and AI models in the Berrys_AgentsV2 platform. It handles model selection, request formatting, execution, and response processing to provide agents with AI capabilities.

## Service Responsibilities

- **Model Selection**: Choosing appropriate models based on request requirements
- **Request Formatting**: Preparing prompts and contexts for models
- **Model Execution**: Sending requests to external AI model providers
- **Response Processing**: Processing and transforming model outputs
- **Context Management**: Maintaining conversation context across requests
- **Token Usage Tracking**: Monitoring and optimizing token consumption
- **Performance Monitoring**: Tracking model performance metrics

## Service Architecture

The Model Orchestration service is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        MES[Model Execution Service]
        MCS[Model Catalog Service]
        MPS[Prompt Engineering Service]
        CMS[Context Management Service]
        TPM[Token & Performance Monitoring]
    end
    
    subgraph "Repository Layer"
        MR[Model Repository]
        ER[Execution Repository]
        CR[Context Repository]
        PR[Prompt Repository]
    end
    
    subgraph "External Interfaces"
        EM1[OpenAI Models]
        EM2[Anthropic Models]
        EM3[Open Source Models]
        AO[Agent Orchestrator]
    end
    
    API --> MES
    API --> MCS
    API --> MPS
    API --> CMS
    API --> TPM
    
    MES --> MR
    MES --> ER
    MCS --> MR
    MPS --> PR
    CMS --> CR
    TPM --> ER
    
    MES --> EM1
    MES --> EM2
    MES --> EM3
    
    AO --> API
    
    style API fill:#d0e0ff,stroke:#0066cc
    style MES fill:#ffe0d0,stroke:#cc6600
    style MCS fill:#ffe0d0,stroke:#cc6600
    style MPS fill:#ffe0d0,stroke:#cc6600
    style CMS fill:#ffe0d0,stroke:#cc6600
    style TPM fill:#ffe0d0,stroke:#cc6600
    style MR fill:#d0ffd0,stroke:#00cc00
    style ER fill:#d0ffd0,stroke:#00cc00
    style CR fill:#d0ffd0,stroke:#00cc00
    style PR fill:#d0ffd0,stroke:#00cc00
    style EM1 fill:#d0e0ff,stroke:#0066cc
    style EM2 fill:#d0e0ff,stroke:#0066cc
    style EM3 fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    Model ||--o{ ModelExecution : used_in
    ModelExecution ||--|| ExecutionResult : produces
    ModelExecution }o--|| Agent : requested_by
    ModelExecution }o--|| Task : part_of
    Prompt ||--o{ ModelExecution : used_in
    Context ||--o{ ModelExecution : provides_context_for
    
    Model {
        UUID id
        string name
        string provider
        string version
        string capabilities
        jsonb parameters
        boolean active
        timestamp created_at
        timestamp updated_at
    }
    
    ModelExecution {
        UUID id
        UUID model_id
        UUID agent_id
        UUID task_id
        UUID prompt_id
        UUID context_id
        string execution_type
        string status
        timestamp created_at
        timestamp completed_at
    }
    
    ExecutionResult {
        UUID id
        UUID execution_id
        text content
        jsonb metadata
        int prompt_tokens
        int completion_tokens
        int total_tokens
        float execution_time_ms
        timestamp created_at
    }
    
    Prompt {
        UUID id
        string name
        string description
        text template
        jsonb parameters
        string version
        timestamp created_at
        timestamp updated_at
    }
    
    Context {
        UUID id
        UUID agent_id
        UUID task_id
        jsonb messages
        int token_count
        timestamp created_at
        timestamp updated_at
    }
```

## API Endpoints

### Model Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /models | List available models |
| GET | /models/{model_id} | Get model details |
| POST | /models | Register new model |
| PUT | /models/{model_id} | Update model |
| DELETE | /models/{model_id} | Deactivate model |
| GET | /models/{model_id}/capabilities | Get model capabilities |
| GET | /models/{model_id}/performance | Get model performance metrics |

### Model Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /execute | Execute model with prompt |
| POST | /execute/streaming | Execute model with streaming response |
| GET | /executions | List executions |
| GET | /executions/{execution_id} | Get execution details |
| GET | /executions/{execution_id}/result | Get execution result |
| POST | /execute/batch | Execute batch of prompts |

### Prompt Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /prompts | List prompts |
| GET | /prompts/{prompt_id} | Get prompt details |
| POST | /prompts | Create prompt |
| PUT | /prompts/{prompt_id} | Update prompt |
| DELETE | /prompts/{prompt_id} | Delete prompt |
| POST | /prompts/{prompt_id}/render | Render prompt with parameters |

### Context Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /contexts | List contexts |
| GET | /contexts/{context_id} | Get context details |
| POST | /contexts | Create context |
| PUT | /contexts/{context_id} | Update context |
| DELETE | /contexts/{context_id} | Delete context |
| PUT | /contexts/{context_id}/append | Append message to context |
| PUT | /contexts/{context_id}/truncate | Truncate context to fit token limit |

## Request/Response Examples

### Execute Model

Request:

```http
POST /execute HTTP/1.1
Content-Type: application/json

{
  "model_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "prompt": {
    "type": "text",
    "content": "Analyze the following customer data and identify key purchasing patterns...",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 2000
    }
  },
  "context_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
  "execution_type": "analysis"
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "execution_id": "h1i2j3k4-5l6m-7n8o-9p0q-1r2s3t4u5v6w",
  "model_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "status": "completed",
  "created_at": "2025-03-29T06:15:00.123456Z",
  "completed_at": "2025-03-29T06:15:02.234567Z",
  "result": {
    "content": "Based on the customer data analysis, I've identified the following purchasing patterns...",
    "metadata": {
      "confidence": 0.85,
      "key_topics": ["seasonal patterns", "customer segments", "product affinities"]
    },
    "token_usage": {
      "prompt_tokens": 512,
      "completion_tokens": 728,
      "total_tokens": 1240
    },
    "execution_time_ms": 2111
  }
}
```

### Streaming Execution

Request:

```http
POST /execute/streaming HTTP/1.1
Content-Type: application/json

{
  "model_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "prompt": {
    "type": "text",
    "content": "Generate a report on recent market trends in the technology sector...",
    "parameters": {
      "temperature": 0.5,
      "max_tokens": 3000
    }
  },
  "context_id": "g1h2i3j4-5k6l-7m8n-9o0p-1q2r3s4t5u6v",
  "execution_type": "report_generation"
}
```

Response (streaming):

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"execution_id": "i2j3k4l5-6m7n-8o9p-0q1r-2s3t4u5v6w7x", "content": "# Technology Sector Market Trends\n\n## Introduction\n", "chunk_index": 0}

data: {"execution_id": "i2j3k4l5-6m7n-8o9p-0q1r-2s3t4u5v6w7x", "content": "The technology sector has experienced significant changes in recent months...", "chunk_index": 1}

data: {"execution_id": "i2j3k4l5-6m7n-8o9p-0q1r-2s3t4u5v6w7x", "content": "## Key Trends\n\n1. Artificial Intelligence Adoption\n", "chunk_index": 2}

...

data: {"execution_id": "i2j3k4l5-6m7n-8o9p-0q1r-2s3t4u5v6w7x", "content": "## Conclusion\n\nBased on these trends, we can anticipate continued growth...", "chunk_index": 15, "finish_reason": "stop"}

data: {"execution_id": "i2j3k4l5-6m7n-8o9p-0q1r-2s3t4u5v6w7x", "token_usage": {"prompt_tokens": 245, "completion_tokens": 1827, "total_tokens": 2072}, "execution_time_ms": 12543}
```

## Event Publishing

The Model Orchestration service publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| model.execution_requested | Model execution request received | Execution request |
| model.execution_completed | Model execution completed | Successful execution |
| model.execution_failed | Model execution failed | Failed execution |
| model.registered | New model registered | Model registration |
| model.updated | Model updated | Model update |
| model.deactivated | Model deactivated | Model deactivation |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440015",
  "type": "model.execution_requested",
  "source": "model-orchestration",
  "timestamp": "2025-03-29T06:15:00.123456Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "h1i2j3k4-5l6m-7n8o-9p0q-1r2s3t4u5v6w",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "model_id": "e1f2g3h4-5i6j-7k8l-9m0n-1o2p3q4r5s6t",
    "execution_type": "analysis",
    "priority": "high"
  }
}
```

## Integration Points

### Agent Orchestrator

- **Agent Initialization**: Initialize agent models
- **Task Execution**: Process agent tasks requiring model interaction
- **Agent Communication**: Enable communication between agents

### Tool Integration

- **Tool Chain**: Chain model outputs to tool inputs
- **Result Processing**: Process tool results for further model analysis

### Planning System

- **Task Planning**: Provide AI capabilities for task planning
- **Task Decomposition**: Assist in task breakdown and dependency analysis

## Supported Models

The service supports various model providers:

| Provider | Supported Models | Integration Type |
|----------|------------------|------------------|
| OpenAI | GPT-4, GPT-4o, GPT-3.5 Turbo | API |
| Anthropic | Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku | API |
| Mistral | Mistral Large, Mistral Medium, Mistral Small | API |
| Local | LLaMA-3, Stable Diffusion | Direct |

## Model Selection Strategy

The service uses a sophisticated model selection algorithm:

1. **Requirement Analysis**: Analyze the request requirements
2. **Capability Matching**: Match requirements to model capabilities
3. **Performance Consideration**: Consider past performance metrics
4. **Cost Optimization**: Balance capability needs with token costs
5. **Availability Check**: Verify model availability and latency
6. **Fallback Configuration**: Define fallback options if preferred model is unavailable

## Context Management

Conversation contexts are managed through:

- **Context Windows**: Maintain recent message history
- **Token Counting**: Track token usage in context
- **Context Truncation**: Intelligent truncation to fit token limits
- **Context Compression**: Summarize older messages to save tokens
- **Key Information Extraction**: Preserve critical information during compression

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/model_orchestration
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
LOCAL_MODEL_ENDPOINT=http://localhost:8000
LOG_LEVEL=INFO
```

## Performance Optimization

The service implements several performance optimizations:

- **Model Result Caching**: Cache results for identical prompts
- **Request Batching**: Batch similar requests when possible
- **Parallel Processing**: Process multiple requests in parallel
- **Streaming Responses**: Stream large responses to reduce latency
- **Adaptive Timeouts**: Adjust timeouts based on model response patterns
- **Resource Pools**: Maintain connection pools to model providers

## Deployment

The service is deployed as a Docker container:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Monitoring and Health

### Health Checks

The service provides health check endpoints:

- **GET /health/liveness**: Confirms the service is running
- **GET /health/readiness**: Confirms the service is ready to accept requests
- **GET /health/dependencies**: Checks the status of service dependencies

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- **model_execution_count**: Total number of model executions
- **model_execution_duration_seconds**: Execution time histogram
- **model_token_usage**: Token usage by model and execution type
- **model_error_rate**: Error rate by model
- **model_latency**: Latency by model
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| High latency | Model provider congestion, large context size | Use smaller contexts, batch requests, implement caching |
| Context token limits | Exceeding model's context window | Implement context truncation, use context compression |
| Model unavailability | API outage, rate limiting | Implement fallbacks, use circuit breakers, retry with backoff |
| Token usage spikes | Inefficient prompts, unnecessary context | Optimize prompts, prune contexts, implement token budgeting |
| Inconsistent responses | Low temperature settings, prompt variability | Standardize prompts, adjust temperature, implement validation |

## Security Considerations

- **API Key Management**: Secure storage of provider API keys
- **Token Validation**: Validate request tokens before processing
- **Request Validation**: Validate prompt content before submission
- **Content Filtering**: Filter sensitive information from prompts
- **Model Output Verification**: Validate model outputs before returning

## References

- [System Overview](../architecture/system-overview.md)
- [Communication Patterns](../architecture/communication-patterns.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Message Contracts](../message-contracts.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
