# API Documentation

This document provides details about the REST API endpoints available in the Project-based Multi-Agent System Framework.

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000/api
```

## Authentication

Most API endpoints require authentication. The API uses JWT (JSON Web Token) for authentication.

### Obtaining a Token

```
POST /token
```

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header of your requests:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Projects

### List Projects

```
GET /projects
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `status` (optional): Filter by status

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Example Project",
    "status": "IN_PROGRESS",
    "created_at": "2025-03-17T10:00:00Z"
  },
  ...
]
```

### Create Project

```
POST /projects
```

**Request Body:**
```json
{
  "name": "New Project",
  "description": "This is a new project",
  "status": "DRAFT",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "New Project",
  "description": "This is a new project",
  "status": "DRAFT",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  },
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2025-03-17T10:00:00Z",
  "updated_at": "2025-03-17T10:00:00Z"
}
```

### Get Project

```
GET /projects/{project_id}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Project",
  "description": "This is an example project",
  "status": "IN_PROGRESS",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  },
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2025-03-17T10:00:00Z",
  "updated_at": "2025-03-17T10:00:00Z"
}
```

### Update Project

```
PUT /projects/{project_id}
```

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description",
  "status": "IN_PROGRESS",
  "metadata": {
    "key1": "updated_value1",
    "key2": "value2"
  }
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Updated Project Name",
  "description": "Updated description",
  "status": "IN_PROGRESS",
  "metadata": {
    "key1": "updated_value1",
    "key2": "value2"
  },
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2025-03-17T10:00:00Z",
  "updated_at": "2025-03-17T10:05:00Z"
}
```

### Delete Project

```
DELETE /projects/{project_id}
```

**Response:**
- Status: 204 No Content

### Get Project Statistics

```
GET /projects/{project_id}/stats
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Project",
  "description": "This is an example project",
  "status": "IN_PROGRESS",
  "metadata": {
    "key1": "value1",
    "key2": "value2"
  },
  "owner_id": "123e4567-e89b-12d3-a456-426614174001",
  "created_at": "2025-03-17T10:00:00Z",
  "updated_at": "2025-03-17T10:00:00Z",
  "agent_count": 5,
  "task_count": 20,
  "completed_task_count": 8,
  "progress_percentage": 40.0
}
```

## Agents

### List Agents

```
GET /agents
```

**Query Parameters:**
- `project_id` (required): Project ID
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `status` (optional): Filter by status
- `type` (optional): Filter by agent type

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "name": "Research Agent",
    "type": "RESEARCHER",
    "status": "ACTIVE",
    "project_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  ...
]
```

### Create Agent

```
POST /agents
```

**Request Body:**
```json
{
  "name": "New Agent",
  "type": "DEVELOPER",
  "configuration": {
    "key1": "value1",
    "key2": "value2"
  },
  "prompt_template": "You are a developer agent...",
  "project_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "New Agent",
  "type": "DEVELOPER",
  "configuration": {
    "key1": "value1",
    "key2": "value2"
  },
  "prompt_template": "You are a developer agent...",
  "status": "CREATED",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-03-17T10:10:00Z",
  "updated_at": "2025-03-17T10:10:00Z"
}
```

### Get Agent

```
GET /agents/{agent_id}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Developer Agent",
  "type": "DEVELOPER",
  "configuration": {
    "key1": "value1",
    "key2": "value2"
  },
  "prompt_template": "You are a developer agent...",
  "status": "ACTIVE",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-03-17T10:10:00Z",
  "updated_at": "2025-03-17T10:10:00Z"
}
```

### Update Agent

```
PUT /agents/{agent_id}
```

**Request Body:**
```json
{
  "name": "Updated Agent Name",
  "configuration": {
    "key1": "updated_value1",
    "key2": "value2"
  },
  "prompt_template": "You are an updated developer agent...",
  "status": "ACTIVE"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Updated Agent Name",
  "type": "DEVELOPER",
  "configuration": {
    "key1": "updated_value1",
    "key2": "value2"
  },
  "prompt_template": "You are an updated developer agent...",
  "status": "ACTIVE",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-03-17T10:10:00Z",
  "updated_at": "2025-03-17T10:15:00Z"
}
```

### Delete Agent

```
DELETE /agents/{agent_id}
```

**Response:**
- Status: 204 No Content

### Generate Agents

```
POST /agents/generate
```

**Request Body:**
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "project_description": "This project is about...",
  "requirements": [
    {
      "name": "Research Agent",
      "description": "Agent for researching...",
      "capabilities": ["web_search", "data_analysis"],
      "priority": 5
    },
    ...
  ]
}
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174004",
    "name": "Research Agent",
    "type": "RESEARCHER",
    "configuration": {
      "capabilities": ["web_search", "data_analysis"]
    },
    "prompt_template": "You are a research agent...",
    "status": "CREATED",
    "project_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2025-03-17T10:20:00Z",
    "updated_at": "2025-03-17T10:20:00Z"
  },
  ...
]
```

## Tasks

### List Tasks

```
GET /tasks
```

**Query Parameters:**
- `project_id` (required): Project ID
- `agent_id` (optional): Agent ID
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174005",
    "name": "Research Task",
    "status": "IN_PROGRESS",
    "priority": 4,
    "agent_id": "123e4567-e89b-12d3-a456-426614174002",
    "due_date": "2025-03-20T10:00:00Z"
  },
  ...
]
```

### Create Task

```
POST /tasks
```

**Request Body:**
```json
{
  "name": "New Task",
  "description": "This is a new task",
  "priority": 3,
  "start_date": "2025-03-18T10:00:00Z",
  "due_date": "2025-03-20T10:00:00Z",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174002"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174006",
  "name": "New Task",
  "description": "This is a new task",
  "status": "PENDING",
  "priority": 3,
  "start_date": "2025-03-18T10:00:00Z",
  "due_date": "2025-03-20T10:00:00Z",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "created_at": "2025-03-17T10:25:00Z",
  "updated_at": "2025-03-17T10:25:00Z"
}
```

### Get Task

```
GET /tasks/{task_id}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174006",
  "name": "New Task",
  "description": "This is a new task",
  "status": "PENDING",
  "priority": 3,
  "start_date": "2025-03-18T10:00:00Z",
  "due_date": "2025-03-20T10:00:00Z",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "created_at": "2025-03-17T10:25:00Z",
  "updated_at": "2025-03-17T10:25:00Z"
}
```

### Update Task

```
PUT /tasks/{task_id}
```

**Request Body:**
```json
{
  "name": "Updated Task Name",
  "description": "Updated description",
  "status": "IN_PROGRESS",
  "priority": 4,
  "start_date": "2025-03-18T10:00:00Z",
  "due_date": "2025-03-21T10:00:00Z"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174006",
  "name": "Updated Task Name",
  "description": "Updated description",
  "status": "IN_PROGRESS",
  "priority": 4,
  "start_date": "2025-03-18T10:00:00Z",
  "due_date": "2025-03-21T10:00:00Z",
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "agent_id": "123e4567-e89b-12d3-a456-426614174002",
  "created_at": "2025-03-17T10:25:00Z",
  "updated_at": "2025-03-17T10:30:00Z"
}
```

### Delete Task

```
DELETE /tasks/{task_id}
```

**Response:**
- Status: 204 No Content

### Add Task Dependency

```
POST /tasks/{task_id}/dependencies
```

**Request Body:**
```json
{
  "dependency_task_id": "123e4567-e89b-12d3-a456-426614174007",
  "dependency_type": "FINISH_TO_START"
}
```

**Response:**
```json
{
  "dependent_task_id": "123e4567-e89b-12d3-a456-426614174006",
  "dependency_task_id": "123e4567-e89b-12d3-a456-426614174007",
  "dependency_type": "FINISH_TO_START"
}
```

## Tools

### List Tools

```
GET /tools
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `capability` (optional): Filter by capability
- `source` (optional): Filter by source
- `status` (optional): Filter by status

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174008",
    "name": "Web Search Tool",
    "capability": "web_search",
    "source": "BUILT_IN",
    "status": "INTEGRATED"
  },
  ...
]
```

### Create Tool

```
POST /tools
```

**Request Body:**
```json
{
  "name": "New Tool",
  "description": "This is a new tool",
  "capability": "data_analysis",
  "source": "USER_DEFINED",
  "documentation_url": "https://example.com/docs",
  "schema": {
    "input": {
      "type": "object",
      "properties": {
        "data": {
          "type": "array",
          "items": {
            "type": "number"
          }
        }
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "result": {
          "type": "number"
        }
      }
    }
  },
  "integration_type": "API"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174009",
  "name": "New Tool",
  "description": "This is a new tool",
  "capability": "data_analysis",
  "source": "USER_DEFINED",
  "documentation_url": "https://example.com/docs",
  "schema": {
    "input": {
      "type": "object",
      "properties": {
        "data": {
          "type": "array",
          "items": {
            "type": "number"
          }
        }
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "result": {
          "type": "number"
        }
      }
    }
  },
  "integration_type": "API",
  "status": "DISCOVERED",
  "created_at": "2025-03-17T10:35:00Z",
  "updated_at": "2025-03-17T10:35:00Z"
}
```

### Get Tool

```
GET /tools/{tool_id}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174009",
  "name": "Data Analysis Tool",
  "description": "This is a data analysis tool",
  "capability": "data_analysis",
  "source": "USER_DEFINED",
  "documentation_url": "https://example.com/docs",
  "schema": {
    "input": {
      "type": "object",
      "properties": {
        "data": {
          "type": "array",
          "items": {
            "type": "number"
          }
        }
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "result": {
          "type": "number"
        }
      }
    }
  },
  "integration_type": "API",
  "status": "INTEGRATED",
  "created_at": "2025-03-17T10:35:00Z",
  "updated_at": "2025-03-17T10:40:00Z"
}
```

### Update Tool

```
PUT /tools/{tool_id}
```

**Request Body:**
```json
{
  "name": "Updated Tool Name",
  "description": "Updated description",
  "documentation_url": "https://example.com/updated-docs",
  "status": "INTEGRATED"
}
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174009",
  "name": "Updated Tool Name",
  "description": "Updated description",
  "capability": "data_analysis",
  "source": "USER_DEFINED",
  "documentation_url": "https://example.com/updated-docs",
  "schema": {
    "input": {
      "type": "object",
      "properties": {
        "data": {
          "type": "array",
          "items": {
            "type": "number"
          }
        }
      }
    },
    "output": {
      "type": "object",
      "properties": {
        "result": {
          "type": "number"
        }
      }
    }
  },
  "integration_type": "API",
  "status": "INTEGRATED",
  "created_at": "2025-03-17T10:35:00Z",
  "updated_at": "2025-03-17T10:45:00Z"
}
```

### Delete Tool

```
DELETE /tools/{tool_id}
```

**Response:**
- Status: 204 No Content

### Discover Tools

```
POST /tools/discover
```

**Request Body:**
```json
{
  "project_id": "123e4567-e89b-12d3-a456-426614174000",
  "requirements": [
    {
      "capability": "image_generation",
      "description": "Tool for generating images from text descriptions",
      "priority": 4
    },
    ...
  ],
  "context": {
    "project_type": "creative",
    "domain": "marketing"
  }
}
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174010",
    "name": "DALL-E Integration",
    "description": "OpenAI's DALL-E for generating images from text",
    "capability": "image_generation",
    "source": "DISCOVERED",
    "documentation_url": "https://platform.openai.com/docs/guides/images",
    "schema": {
      "input": {
        "type": "object",
        "properties": {
          "prompt": {
            "type": "string"
          },
          "size": {
            "type": "string",
            "enum": ["256x256", "512x512", "1024x1024"]
          }
        }
      },
      "output": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string"
          }
        }
      }
    },
    "integration_type": "API",
    "status": "DISCOVERED",
    "created_at": "2025-03-17T10:50:00Z",
    "updated_at": "2025-03-17T10:50:00Z"
  },
  ...
]
```

## Models

### List Models

```
GET /models
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)
- `provider` (optional): Filter by provider
- `is_local` (optional): Filter by local/remote status
- `status` (optional): Filter by status

**Response:**
```json
[
  {
    "id": "gpt-4o",
    "provider": "OPENAI",
    "version": "4o",
    "is_local": false,
    "status": "ACTIVE"
  },
  {
    "id": "claude-3-opus",
    "provider": "ANTHROPIC",
    "version": "3-opus",
    "is_local": false,
    "status": "ACTIVE"
  },
  {
    "id": "llama3:latest",
    "provider": "OLLAMA",
    "version": "latest",
    "is_local": true,
    "status": "ACTIVE"
  },
  ...
]
```

### Get Model

```
GET /models/{model_id}
```

**Response:**
```json
{
  "id": "gpt-4o",
  "provider": "OPENAI",
  "version": "4o",
  "capabilities": {
    "REASONING": 0.95,
    "CODE_GENERATION": 0.92,
    "CREATIVE": 0.88,
    "TOOL_USE": 0.96
  },
  "context_window": 128000,
  "cost_per_1k_input": 0.01,
  "cost_per_1k_output": 0.03,
  "is_local": false,
  "status": "ACTIVE",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-03-01T00:00:00Z"
}
```

### Create Model

```
POST /models
```

**Request Body:**
```json
{
  "id": "custom-model",
  "provider": "CUSTOM",
  "version": "1.0",
  "capabilities": {
    "REASONING": 0.8,
    "CODE_GENERATION": 0.7,
    "CREATIVE": 0.9,
    "TOOL_USE": 0.6
  },
  "context_window": 32000,
  "cost_per_1k_input": 0.005,
  "cost_per_1k_output": 0.015,
  "is_local": true
}
```

**Response:**
```json
{
  "id": "custom-model",
  "provider": "CUSTOM",
  "version": "1.0",
  "capabilities": {
    "REASONING": 0.8,
    "CODE_GENERATION": 0.7,
    "CREATIVE": 0.9,
    "TOOL_USE": 0.6
  },
  "context_window": 32000,
  "cost_per_1k_input": 0.005,
  "cost_per_1k_output": 0.015,
  "is_local": true,
  "status": "ACTIVE",
  "created_at": "2025-03-17T11:00:00Z",
  "updated_at": "2025-03-17T11:00:00Z"
}
```

### Update Model

```
PUT /models/{model_id}
```

**Request Body:**
```json
{
  "capabilities": {
    "REASONING": 0.85,
    "CODE_GENERATION": 0.75,
    "CREATIVE": 0.92,
    "TOOL_USE": 0.65
  },
  "context_window": 64000,
  "status": "ACTIVE"
}
```

**Response:**
```json
{
  "id": "custom-model",
  "provider": "CUSTOM",
  "version": "1.0",
  "capabilities": {
    "REASONING": 0.85,
    "CODE_GENERATION": 0.75,
    "CREATIVE": 0.92,
    "TOOL_USE": 0.65
  },
  "context_window": 64000,
  "cost_per_1k_input": 0.005,
  "cost_per_1k_output": 0.015,
  "is_local": true,
  "status": "ACTIVE",
  "created_at": "2025-03-17T11:00:00Z",
  "updated_at": "2025-03-17T11:05:00Z"
}
```

### Delete Model

```
DELETE /models/{model_id}
```

**Response:**
- Status: 204 No Content

## Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-03-17T11:10:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "messaging": "healthy"
  }
}
```

## Error Responses

The API uses standard HTTP status codes to indicate the success or failure of a request.

### Common Error Codes

- `400 Bad Request`: The request was invalid or cannot be served.
- `401 Unauthorized`: Authentication is required or failed.
- `403 Forbidden`: The authenticated user does not have permission to access the requested resource.
- `404 Not Found`: The requested resource does not exist.
- `409 Conflict`: The request conflicts with the current state of the server.
- `422 Unprocessable Entity`: The request was well-formed but was unable to be followed due to semantic errors.
- `500 Internal Server Error`: An error occurred on the server.

### Error Response Format

```json
{
  "detail": "Error message"
}
```

For validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
