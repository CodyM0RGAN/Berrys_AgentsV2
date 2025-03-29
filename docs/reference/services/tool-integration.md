# Tool Integration Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Tool Integration service enables agents to interact with external tools and APIs in the Berrys_AgentsV2 platform. It manages tool discovery, selection, execution, and result processing to provide agents with access to a wide range of capabilities beyond their core functionality.

## Service Responsibilities

- **Tool Registration**: Registering and managing tools in the platform
- **Tool Discovery**: Enabling agents to discover available tools
- **Tool Selection**: Assisting agents in selecting appropriate tools
- **Tool Execution**: Executing tools on behalf of agents
- **Result Processing**: Processing and returning tool execution results
- **Credential Management**: Securely managing credentials for external tools
- **Access Control**: Enforcing access policies for tool usage

## Service Architecture

The Tool Integration service is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        API[API Controllers]
    end
    
    subgraph "Service Layer"
        TRS[Tool Registry Service]
        TES[Tool Execution Service]
        TDS[Tool Discovery Service]
        CMS[Credential Management Service]
        ACS[Access Control Service]
        TLS[Tool Logging Service]
    end
    
    subgraph "Repository Layer"
        TR[Tool Repository]
        ER[Execution Repository]
        CR[Credential Repository]
        PR[Policy Repository]
    end
    
    subgraph "External Interfaces"
        ET1[External APIs]
        ET2[Cloud Services]
        ET3[Local Tools]
        AO[Agent Orchestrator]
        MO[Model Orchestration]
    end
    
    API --> TRS
    API --> TES
    API --> TDS
    API --> CMS
    API --> ACS
    API --> TLS
    
    TRS --> TR
    TES --> ER
    CMS --> CR
    ACS --> PR
    
    TES --> ET1
    TES --> ET2
    TES --> ET3
    
    AO --> API
    MO --> API
    
    style API fill:#d0e0ff,stroke:#0066cc
    style TRS fill:#ffe0d0,stroke:#cc6600
    style TES fill:#ffe0d0,stroke:#cc6600
    style TDS fill:#ffe0d0,stroke:#cc6600
    style CMS fill:#ffe0d0,stroke:#cc6600
    style ACS fill:#ffe0d0,stroke:#cc6600
    style TLS fill:#ffe0d0,stroke:#cc6600
    style TR fill:#d0ffd0,stroke:#00cc00
    style ER fill:#d0ffd0,stroke:#00cc00
    style CR fill:#d0ffd0,stroke:#00cc00
    style PR fill:#d0ffd0,stroke:#00cc00
    style ET1 fill:#d0e0ff,stroke:#0066cc
    style ET2 fill:#d0e0ff,stroke:#0066cc
    style ET3 fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
    style MO fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    Tool ||--o{ ToolVersion : has
    Tool ||--o{ ToolExecution : used_in
    ToolVersion ||--o{ ToolParameter : defines
    ToolExecution ||--o{ ParameterValue : contains
    ToolExecution ||--|| ExecutionResult : produces
    Agent ||--o{ ToolExecution : initiates
    Tool ||--o{ ToolCredential : uses
    
    Tool {
        UUID id
        string name
        string description
        string type
        string category
        jsonb capabilities
        jsonb metadata
        boolean active
        timestamp created_at
        timestamp updated_at
    }
    
    ToolVersion {
        UUID id
        UUID tool_id
        string version
        jsonb schema
        string implementation
        jsonb configuration
        boolean active
        timestamp created_at
    }
    
    ToolParameter {
        UUID id
        UUID tool_version_id
        string name
        string description
        string type
        boolean required
        jsonb schema
        jsonb default_value
    }
    
    ToolExecution {
        UUID id
        UUID tool_id
        UUID tool_version_id
        UUID agent_id
        UUID task_id
        string status
        timestamp created_at
        timestamp started_at
        timestamp completed_at
    }
    
    ParameterValue {
        UUID id
        UUID execution_id
        UUID parameter_id
        jsonb value
    }
    
    ExecutionResult {
        UUID id
        UUID execution_id
        string status
        jsonb result
        jsonb error
        float duration_ms
        jsonb metadata
        timestamp created_at
    }
    
    ToolCredential {
        UUID id
        UUID tool_id
        string name
        string type
        jsonb credentials
        boolean active
        timestamp created_at
        timestamp updated_at
    }
```

## API Endpoints

### Tool Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /tools | List available tools |
| GET | /tools/{tool_id} | Get tool details |
| POST | /tools | Register new tool |
| PUT | /tools/{tool_id} | Update tool |
| DELETE | /tools/{tool_id} | Deactivate tool |
| GET | /tools/{tool_id}/versions | List tool versions |
| POST | /tools/{tool_id}/versions | Add new tool version |
| GET | /tools/{tool_id}/parameters | Get tool parameters |
| GET | /tools/categories | List tool categories |

### Tool Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /discovery | Discover tools based on criteria |
| GET | /discovery/capabilities | List all tool capabilities |
| GET | /discovery/similar/{tool_id} | Find similar tools |
| GET | /discovery/recommended | Get recommended tools |
| POST | /discovery/search | Search for tools |

### Tool Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /execute | Execute tool |
| POST | /execute/batch | Execute multiple tools |
| GET | /executions | List executions |
| GET | /executions/{execution_id} | Get execution details |
| GET | /executions/{execution_id}/result | Get execution result |
| DELETE | /executions/{execution_id} | Cancel execution |
| POST | /executions/{execution_id}/retry | Retry execution |

### Credential Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /credentials | List credentials |
| GET | /credentials/{credential_id} | Get credential details |
| POST | /credentials | Create credential |
| PUT | /credentials/{credential_id} | Update credential |
| DELETE | /credentials/{credential_id} | Delete credential |
| POST | /credentials/verify | Verify credential |

## Request/Response Examples

### Execute Tool

Request:

```http
POST /execute HTTP/1.1
Content-Type: application/json

{
  "tool_id": "j1k2l3m4-5n6o-7p8q-9r0s-1t2u3v4w5x6y",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "parameters": {
    "query": "Latest technology trends in artificial intelligence",
    "sources": ["academic", "news", "blogs"],
    "result_count": 5,
    "include_summaries": true
  }
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "execution_id": "k1l2m3n4-5o6p-7q8r-9s0t-1u2v3w4x5y6z",
  "tool_id": "j1k2l3m4-5n6o-7p8q-9r0s-1t2u3v4w5x6y",
  "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
  "status": "completed",
  "created_at": "2025-03-29T07:00:00.123456Z",
  "started_at": "2025-03-29T07:00:00.234567Z",
  "completed_at": "2025-03-29T07:00:03.345678Z",
  "result": {
    "articles": [
      {
        "title": "Advances in Multimodal AI Models: Breaking New Ground",
        "source": "AI Research Journal",
        "url": "https://example.com/article1",
        "published_date": "2025-03-15T00:00:00Z",
        "summary": "Recent advances in multimodal AI models have shown significant improvements in understanding and generating content across text, image, and audio domains."
      },
      {
        "title": "AI Regulation Framework Proposed by International Coalition",
        "source": "Tech Policy News",
        "url": "https://example.com/article2",
        "published_date": "2025-03-20T00:00:00Z",
        "summary": "A coalition of 15 countries has proposed a new framework for regulating artificial intelligence technologies with a focus on safety and ethics."
      },
      // Additional results omitted for brevity
    ],
    "metadata": {
      "search_time_ms": 2500,
      "total_results_available": 128,
      "result_freshness": "high"
    }
  },
  "duration_ms": 3111
}
```

### Discover Tools

Request:

```http
POST /discovery/search HTTP/1.1
Content-Type: application/json

{
  "capabilities": ["data_analysis", "visualization"],
  "input_types": ["csv", "json"],
  "output_types": ["chart", "dashboard"],
  "keywords": ["customer", "segmentation"]
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "tools": [
    {
      "id": "l1m2n3o4-5p6q-7r8s-9t0u-1v2w3x4y5z6a",
      "name": "Customer Segmentation Analyzer",
      "description": "Analyzes customer data to identify segments based on behavior and demographics",
      "category": "data_analysis",
      "capabilities": ["data_analysis", "segmentation", "clustering"],
      "input_types": ["csv", "json", "excel"],
      "output_types": ["json", "chart", "report"],
      "version": "2.1.0",
      "popularity": 4.8,
      "execution_count": 1245
    },
    {
      "id": "m2n3o4p5-6q7r-8s9t-0u1v-2w3x4y5z6a7b",
      "name": "Customer Visualization Dashboard",
      "description": "Creates interactive dashboards for visualizing customer data patterns",
      "category": "visualization",
      "capabilities": ["visualization", "dashboard", "interactive_charts"],
      "input_types": ["csv", "json"],
      "output_types": ["dashboard", "chart", "html"],
      "version": "1.5.2",
      "popularity": 4.6,
      "execution_count": 987
    },
    // Additional tools omitted for brevity
  ],
  "total": 8,
  "recommendation": "l1m2n3o4-5p6q-7r8s-9t0u-1v2w3x4y5z6a",
  "metadata": {
    "search_time_ms": 105
  }
}
```

## Event Publishing

The Tool Integration service publishes events to the message queue:

| Event Type | Description | Triggered By |
|------------|-------------|--------------|
| tool.registered | New tool registered | Tool registration |
| tool.updated | Tool updated | Tool update |
| tool.deactivated | Tool deactivated | Tool deactivation |
| tool.execution_requested | Tool execution requested | Execution request |
| tool.execution_started | Tool execution started | Execution start |
| tool.execution_completed | Tool execution completed | Execution completion |
| tool.execution_failed | Tool execution failed | Execution failure |
| tool.credential_created | Credential created | Credential creation |
| tool.credential_updated | Credential updated | Credential update |

Example event:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440025",
  "type": "tool.execution_completed",
  "source": "tool-integration",
  "timestamp": "2025-03-29T07:00:03.345678Z",
  "correlation_id": "5d976e66-8c32-483f-a9d1-8feaade0e1e0",
  "data": {
    "execution_id": "k1l2m3n4-5o6p-7q8r-9s0t-1u2v3w4x5y6z",
    "tool_id": "j1k2l3m4-5n6o-7p8q-9r0s-1t2u3v4w5x6y",
    "agent_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "task_id": "a8b7c6d5-e4f3-4a2b-8c7d-6e5f4a3b2c1d",
    "status": "completed",
    "duration_ms": 3111,
    "result_summary": {
      "result_type": "article_collection",
      "result_count": 5
    }
  }
}
```

## Integration Points

### Agent Orchestrator

- **Tool Usage**: Process tool usage requests from agents
- **Tool Results**: Deliver tool execution results to agents
- **Tool Capabilities**: Share tool capabilities for agent specialization
- **Access Control**: Enforce agent access policies for tools

### Model Orchestration

- **Result Processing**: Process tool results for model context
- **Query Enhancement**: Use tools to enhance model queries
- **Tool Selection**: Use models to assist in tool selection
- **Parameter Generation**: Generate tool parameters based on model outputs

### Service Integration

- **Workflow Integration**: Integrate tool execution into workflows
- **Complex Tool Chains**: Create chains of tool executions
- **Error Handling**: Coordinate error handling for tool failures
- **State Management**: Manage tool execution state in workflows

## Tool Categories

The service supports various tool categories:

| Category | Description | Examples |
|----------|-------------|----------|
| Data Processing | Tools for processing and transforming data | CSV Parser, JSON Transformer, Data Cleaner |
| Data Analysis | Tools for analyzing data and extracting insights | Statistical Analyzer, Pattern Detector, Cluster Analyzer |
| Visualization | Tools for creating visual representations of data | Chart Generator, Dashboard Creator, Graph Visualizer |
| Search | Tools for searching and retrieving information | Web Search, Document Search, Knowledge Base Query |
| Communication | Tools for communication and messaging | Email Sender, Message Notifier, Slack Poster |
| Content Generation | Tools for generating content | Document Generator, Code Generator, Image Creator |
| Content Analysis | Tools for analyzing content | Text Analyzer, Sentiment Analyzer, Image Recognizer |
| Integration | Tools for integrating with external systems | API Connector, Database Connector, File System Connector |
| Utility | Utility tools for common operations | Date/Time Formatter, Currency Converter, Unit Converter |

## Tool Implementation Types

The service supports several implementation types:

1. **HTTP API**: Tools that interact with external HTTP APIs
2. **SDK Integration**: Tools that use external SDKs or libraries
3. **Container Execution**: Tools that run in isolated containers
4. **JavaScript Function**: Tools implemented as JavaScript functions
5. **Python Function**: Tools implemented as Python functions
6. **Shell Command**: Tools implemented as shell commands
7. **WebAssembly**: Tools implemented as WebAssembly modules

### Implementation Example (HTTP API)

```json
{
  "implementation": {
    "type": "http_api",
    "method": "POST",
    "url": "https://api.example.com/search",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer ${credentials.api_key}"
    },
    "body_template": {
      "query": "${parameters.query}",
      "filters": "${parameters.filters}",
      "limit": "${parameters.limit}"
    },
    "response_mapping": {
      "results": "$.data.items",
      "total": "$.data.total",
      "next_page": "$.data.pagination.next"
    }
  }
}
```

### Implementation Example (Python Function)

```json
{
  "implementation": {
    "type": "python_function",
    "module": "customer_segmentation",
    "function": "analyze_segments",
    "environment": {
      "python_version": "3.10",
      "requirements": [
        "pandas==1.5.3",
        "scikit-learn==1.2.2",
        "numpy==1.24.3"
      ]
    },
    "timeout_seconds": 300,
    "memory_limit_mb": 1024
  }
}
```

## Credential Management

The service securely manages credentials with these features:

- **Encrypted Storage**: Credentials are encrypted at rest
- **Scoped Access**: Credentials are scoped to specific tools
- **Version Control**: Credential versions are tracked
- **Rotation Support**: Credentials can be rotated automatically
- **Access Auditing**: Credential usage is audited
- **Secret References**: Credentials are referenced indirectly

### Credential Types

| Type | Description | Example |
|------|-------------|---------|
| API Key | Simple API key | `{"api_key": "sk_test_12345..."}`|
| Basic Auth | Username/password authentication | `{"username": "user", "password": "pass"}` |
| OAuth2 | OAuth 2.0 authentication | `{"client_id": "id", "client_secret": "secret", "refresh_token": "token"}` |
| Bearer Token | Bearer token authentication | `{"token": "eyJhbGciOiJIUzI1NiIsInR5c..."}` |
| AWS | AWS authentication | `{"access_key": "AKIA...", "secret_key": "abcd..."}` |
| Certificate | Certificate-based authentication | `{"cert": "-----BEGIN CERTIFICATE-----..."}` |

## Tool Parameters

Tool parameters are defined using JSON Schema:

```json
{
  "parameters": {
    "type": "object",
    "required": ["query"],
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query",
        "minLength": 3,
        "maxLength": 100
      },
      "filters": {
        "type": "object",
        "description": "Optional filters to apply to the search",
        "properties": {
          "date_range": {
            "type": "object",
            "properties": {
              "start": {
                "type": "string",
                "format": "date"
              },
              "end": {
                "type": "string",
                "format": "date"
              }
            }
          },
          "categories": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["news", "academic", "blogs"]
            }
          }
        }
      },
      "limit": {
        "type": "integer",
        "description": "Number of results to return",
        "default": 10,
        "minimum": 1,
        "maximum": 100
      }
    }
  }
}
```

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/tool_integration
REDIS_URL=redis://localhost:6379
ENCRYPTION_KEY=base64:abcdefg123456==
AGENT_ORCHESTRATOR_URL=http://agent-orchestrator:8080
MODEL_ORCHESTRATION_URL=http://model-orchestration:8080
SERVICE_INTEGRATION_URL=http://service-integration:8080
CONTAINER_ENGINE_URL=http://container-engine:8080
FUNCTION_RUNTIME_URL=http://function-runtime:8080
LOG_LEVEL=INFO
```

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

- **tool_count**: Total number of registered tools
- **tool_execution_count**: Count of tool executions
- **tool_execution_duration_seconds**: Tool execution time histogram
- **tool_error_rate**: Error rate by tool
- **tool_popularity**: Execution count by tool
- **credential_usage_count**: Credential usage count
- **api_request_duration_seconds**: API endpoint response times
- **api_request_count**: Count of API requests by endpoint and status

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Tool execution failures | Invalid parameters, service unavailability | Validate parameters, check tool health |
| Credential issues | Expired credentials, insufficient permissions | Update credentials, check permissions |
| Performance bottlenecks | Resource-intensive tools, high concurrency | Optimize tool implementations, implement rate limiting |
| Integration failures | API changes, incompatible data formats | Update tool implementations, add data transformations |
| Container failures | Resource limits, image issues | Adjust resource limits, update container images |

## Security Considerations

- **Input Validation**: All tool parameters are validated
- **Output Sanitization**: Tool outputs are sanitized
- **Access Control**: Tool access is controlled by policies
- **Credential Protection**: Credentials are securely stored
- **Execution Isolation**: Tool executions are isolated
- **Rate Limiting**: Tool executions are rate limited
- **Audit Logging**: All tool operations are logged

## References

- [System Overview](../architecture/system-overview.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [Service Integration Service](service-integration.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
- [Model Orchestration Service](model-orchestration.md)
