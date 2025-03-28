# Model Orchestration Service Interface

## Overview
The Model Orchestration service manages interaction with AI models from various providers, offering a unified interface for model selection, request routing, and response processing. The service now includes a performance evaluation system that tracks model quality metrics and uses them to make intelligent model selection decisions.

## Endpoints

### `POST /api/models/completion`
Generate completions from text prompts.

#### Request:
```json
{
  "prompt": "string (required) - The text prompt",
  "model_id": "string (optional) - Specific model identifier",
  "max_tokens": "integer (optional) - Maximum tokens to generate",
  "temperature": "float (optional) - 0.0-2.0, higher is more creative",
  "task_type": "string (optional) - e.g., 'code_generation', 'reasoning', 'creative'",
  "requirements": {
    "reliability": "float (optional) - 0.0-1.0, higher for more predictable responses",
    "creativity": "float (optional) - 0.0-1.0, higher for more creative responses",
    "capabilities": ["string (optional) - e.g., 'code', 'planning', 'reasoning'"],
    "min_quality_score": "float (optional) - 0.0-1.0, minimum quality score for model selection"
  },
  "context": [
    {
      "type": "string (e.g., 'text', 'code', 'file')",
      "content": "string - The context content",
      "metadata": {
        "key": "value (additional context-specific metadata)"
      }
    }
  ],
  "metadata": {
    "user_id": "string (optional) - User identifier for tracking",
    "project_id": "string (optional) - Project identifier",
    "task_id": "string (optional) - Task identifier"
  }
}
```

#### Response:
```json
{
  "completion_id": "string - Unique identifier for the completion",
  "created_at": "string - ISO timestamp",
  "model": {
    "id": "string - Model identifier used",
    "provider": "string - Model provider (e.g., 'openai', 'anthropic', 'ollama')"
  },
  "content": "string - The generated completion text",
  "usage": {
    "prompt_tokens": "integer - Number of tokens in the prompt",
    "completion_tokens": "integer - Number of tokens in the completion",
    "total_tokens": "integer - Total tokens used",
    "estimated_cost": "float - Estimated cost in USD"
  },
  "performance": {
    "quality_score": "float - Overall quality score (0.0-1.0)",
    "success_rate": "float - Historical success rate for this task type",
    "confidence": "float - Model's confidence in this response"
  },
  "metadata": {
    "finish_reason": "string (e.g., 'stop', 'length', 'content_filter')",
    "model_specific": {
      "key": "value (model-specific metadata)"
    }
  }
}
```

### `POST /api/models/chat`
Generate responses in a chat conversation.

#### Request:
```json
{
  "messages": [
    {
      "role": "string (e.g., 'system', 'user', 'assistant')",
      "content": "string - The message content"
    }
  ],
  "model_id": "string (optional)",
  "max_tokens": "integer (optional)",
  "temperature": "float (optional)",
  "requirements": { /* same as completion */ },
  "context": [ /* same as completion */ ],
  "metadata": { /* same as completion */ }
}
```

#### Response:
Same format as completion response.

### `GET /api/models`
List available models and their capabilities.

#### Response:
```json
{
  "models": [
    {
      "id": "string - Model identifier",
      "provider": "string - Model provider",
      "capabilities": ["string - e.g., 'chat', 'completion', 'embedding'"],
      "properties": {
        "context_length": "integer - Maximum context length",
        "token_limit": "integer - Token limit per request",
        "pricing": {
          "input": "float - Cost per 1K input tokens in USD",
          "output": "float - Cost per 1K output tokens in USD"
        }
      },
      "metadata": {
        "version": "string - Model version",
        "description": "string - Model description"
      }
    }
  ]
}
```

### `POST /api/models/embeddings`
Generate vector embeddings from text.

#### Request:
```json
{
  "texts": ["string - Text to embed"],
  "model_id": "string (optional) - Embedding model to use",
  "dimensions": "integer (optional) - Desired embedding dimensions"
}
```

#### Response:
```json
{
  "embeddings": [
    [0.123, 0.456, ...] // Vector of floats
  ],
  "model": {
    "id": "string - Model identifier used",
    "provider": "string - Model provider"
  },
  "usage": {
    "total_tokens": "integer - Total tokens used",
    "estimated_cost": "float - Estimated cost in USD"
  }
}
```

### `POST /api/models/feedback`
Submit feedback on a model response.

#### Request:
```json
{
  "request_id": "string (required) - The original request ID",
  "quality_rating": "float (optional) - 0.0-1.0 quality rating",
  "success": "boolean (required) - Whether the response was successful",
  "feedback": "string (optional) - Textual feedback",
  "corrections": {
    "original": "string (optional) - Original content",
    "corrected": "string (optional) - Corrected content"
  },
  "metadata": {
    "user_id": "string (optional) - User providing feedback",
    "task_id": "string (optional) - Associated task"
  }
}
```

#### Response:
```json
{
  "feedback_id": "string - Unique identifier for the feedback",
  "created_at": "string - ISO timestamp",
  "status": "string - 'accepted'",
  "updated_metrics": {
    "quality_score": "float - Updated quality score",
    "success_rate": "float - Updated success rate"
  }
}
```

### `GET /api/models/performance`
Get performance metrics for models.

#### Query Parameters:
- `model_id` (optional): Filter by specific model
- `task_type` (optional): Filter by task type
- `time_range` (optional): Time range for metrics (e.g., '7d', '30d')

#### Response:
```json
{
  "models": [
    {
      "model_id": "string - Model identifier",
      "provider": "string - Model provider",
      "metrics": {
        "overall_quality": "float - Overall quality score (0.0-1.0)",
        "success_rate": "float - Success rate",
        "task_specific": {
          "code_generation": {
            "quality_score": "float - Quality score for this task",
            "success_rate": "float - Success rate for this task",
            "sample_count": "integer - Number of samples"
          },
          "reasoning": {
            "quality_score": "float - Quality score for this task",
            "success_rate": "float - Success rate for this task",
            "sample_count": "integer - Number of samples"
          }
        }
      },
      "trends": {
        "quality_trend": [0.92, 0.93, 0.95], // Last n periods
        "success_trend": [0.98, 0.97, 0.99]  // Last n periods
      }
    }
  ]
}
```

## Events Published

### `model.request.completed`
Published when a model request is successfully completed.

```json
{
  "request_id": "string - The original request ID",
  "model_id": "string - The model used",
  "user_id": "string (optional) - The user who made the request",
  "project_id": "string (optional) - Associated project",
  "task_id": "string (optional) - Associated task",
  "task_type": "string (optional) - Type of task",
  "timestamp": "string - ISO timestamp",
  "metrics": {
    "latency_ms": "integer - Request latency in milliseconds",
    "tokens": {
      "prompt": "integer - Prompt tokens",
      "completion": "integer - Completion tokens",
      "total": "integer - Total tokens"
    },
    "cost": "float - Cost in USD",
    "performance": {
      "quality_score": "float - Quality score",
      "confidence": "float - Model confidence"
    }
  }
}
```

### `model.feedback.received`
Published when feedback is received for a model response.

```json
{
  "feedback_id": "string - Feedback identifier",
  "request_id": "string - The original request ID",
  "model_id": "string - The model used",
  "task_type": "string (optional) - Type of task",
  "timestamp": "string - ISO timestamp",
  "feedback": {
    "quality_rating": "float - User-provided quality rating",
    "success": "boolean - Whether the response was successful",
    "has_corrections": "boolean - Whether corrections were provided"
  }
}
```

### `model.request.failed`
Published when a model request fails.

```json
{
  "request_id": "string - The original request ID",
  "model_id": "string - The model attempted",
  "error": {
    "code": "string - Error code",
    "message": "string - Error message",
    "details": "object - Error details"
  },
  "fallback_attempted": "boolean - Whether fallback was attempted",
  "fallback_succeeded": "boolean - Whether fallback succeeded"
}
```

## Commands Handled

### `model.register`
Register a new model with the service.

```json
{
  "model_id": "string - Unique model identifier",
  "provider": "string - Model provider",
  "capabilities": ["string - e.g., 'chat', 'completion'"],
  "performance_baseline": {
    "quality_score": "float (optional) - Initial quality score",
    "task_specific": {
      "code_generation": "float (optional) - Initial score for code tasks",
      "reasoning": "float (optional) - Initial score for reasoning tasks"
    }
  },
  "configuration": {
    "api_key": "string (optional) - Provider API key",
    "api_url": "string (optional) - Provider API URL",
    "options": {
      "key": "value - Provider-specific options"
    }
  }
}
```

### `model.performance.reset`
Reset performance metrics for a model.

```json
{
  "model_id": "string - The model ID to reset metrics for",
  "task_types": ["string (optional) - Specific task types to reset, or all if omitted"]
}
```

### `model.request.cancel`
Cancel an in-progress model request.

```json
{
  "request_id": "string - The request ID to cancel"
}
```

## Performance Tracking System

The Model Orchestration service includes a robust performance tracking system that:

1. **Records Request Results**: Automatically tracks success rates and quality scores for each model and task type combination.

2. **Processes User Feedback**: Collects and processes user feedback with weighted importance (user feedback counts more than automatic metrics).

3. **Maintains Historical Data**: Stores performance metrics over time (daily, weekly, monthly) to enable trend analysis.

4. **Enables Quality-Based Selection**: Provides APIs to select the best model for a given task based on historical performance.

5. **Handles Edge Cases**: Includes robust error handling for all operations, including safe handling of null or invalid inputs.

The performance tracking system has been fully tested and optimized for reliability. It provides the foundation for intelligent model selection based on past performance, allowing the system to automatically route requests to the most effective model for each task type.
