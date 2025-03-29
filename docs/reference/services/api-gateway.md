# API Gateway Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The API Gateway service serves as the entry point for all external requests to the Berrys_AgentsV2 platform. It handles authentication, request routing, rate limiting, and response formatting, providing a unified interface for clients to interact with the platform's services.

## Service Responsibilities

- **Authentication**: Verifying client identity and access rights
- **Request Routing**: Directing requests to appropriate backend services
- **API Versioning**: Managing multiple API versions
- **Rate Limiting**: Enforcing usage limits and preventing abuse
- **Request Validation**: Validating incoming request formats
- **Response Formatting**: Standardizing response formats
- **Documentation**: Providing API documentation via OpenAPI
- **Monitoring**: Collecting API usage and performance metrics

## Service Architecture

The API Gateway is built as a FastAPI application with a layered architecture:

```mermaid
graph TD
    subgraph "API Layer"
        RE[Request Endpoints]
        OA[OpenAPI Documentation]
    end
    
    subgraph "Service Layer"
        AUS[Authentication Service]
        ROS[Routing Service]
        RLS[Rate Limiting Service]
        RVS[Request Validation Service]
        RFS[Response Formatting Service]
        MOS[Monitoring Service]
    end
    
    subgraph "Infrastructure Layer"
        CC[Configuration Client]
        SC[Service Discovery Client]
        MC[Metrics Client]
        LC[Logging Client]
    end
    
    subgraph "External Interfaces"
        WD[Web Dashboard]
        PC[Project Coordinator]
        AO[Agent Orchestrator]
        PS[Planning System]
        MO[Model Orchestration]
        TI[Tool Integration]
        SI[Service Integration]
    end
    
    RE --> AUS
    RE --> RVS
    RE --> RLS
    RE --> ROS
    RE --> RFS
    RE --> MOS
    
    AUS --> CC
    ROS --> SC
    MOS --> MC
    RVS --> CC
    RLS --> CC
    
    ROS --> PC
    ROS --> AO
    ROS --> PS
    ROS --> MO
    ROS --> TI
    ROS --> SI
    
    WD --> RE
    
    style RE fill:#d0e0ff,stroke:#0066cc
    style OA fill:#d0e0ff,stroke:#0066cc
    style AUS fill:#ffe0d0,stroke:#cc6600
    style ROS fill:#ffe0d0,stroke:#cc6600
    style RLS fill:#ffe0d0,stroke:#cc6600
    style RVS fill:#ffe0d0,stroke:#cc6600
    style RFS fill:#ffe0d0,stroke:#cc6600
    style MOS fill:#ffe0d0,stroke:#cc6600
    style CC fill:#d0ffd0,stroke:#00cc00
    style SC fill:#d0ffd0,stroke:#00cc00
    style MC fill:#d0ffd0,stroke:#00cc00
    style LC fill:#d0ffd0,stroke:#00cc00
    style WD fill:#d0e0ff,stroke:#0066cc
    style PC fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
    style PS fill:#d0e0ff,stroke:#0066cc
    style MO fill:#d0e0ff,stroke:#0066cc
    style TI fill:#d0e0ff,stroke:#0066cc
    style SI fill:#d0e0ff,stroke:#0066cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    User ||--o{ ApiKey : has
    User ||--o{ UserRole : has
    Service ||--o{ Endpoint : exposes
    Endpoint ||--o{ EndpointPermission : requires
    Role ||--o{ EndpointPermission : grants
    Role ||--o{ UserRole : assigned_to
    ApiRequest ||--|| ApiKey : authorized_by
    ApiRequest ||--|| Endpoint : targets
    
    User {
        UUID id
        string username
        string email
        string password_hash
        boolean active
        timestamp created_at
        timestamp updated_at
    }
    
    ApiKey {
        UUID id
        UUID user_id
        string key
        string name
        jsonb permissions
        timestamp expires_at
        timestamp created_at
        timestamp updated_at
    }
    
    UserRole {
        UUID id
        UUID user_id
        UUID role_id
        timestamp created_at
    }
    
    Role {
        UUID id
        string name
        string description
        timestamp created_at
        timestamp updated_at
    }
    
    Service {
        UUID id
        string name
        string version
        string base_url
        boolean active
        timestamp created_at
        timestamp updated_at
    }
    
    Endpoint {
        UUID id
        UUID service_id
        string path
        string method
        string name
        string description
        boolean public
        boolean deprecated
        string version
        timestamp created_at
        timestamp updated_at
    }
    
    EndpointPermission {
        UUID id
        UUID endpoint_id
        UUID role_id
        timestamp created_at
    }
    
    ApiRequest {
        UUID id
        UUID api_key_id
        UUID endpoint_id
        string client_ip
        string method
        string path
        int status_code
        int response_time_ms
        int request_size_bytes
        int response_size_bytes
        timestamp created_at
    }
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | User login |
| POST | /auth/logout | User logout |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/profile | Get user profile |
| PUT | /auth/profile | Update user profile |
| POST | /auth/change-password | Change password |

### API Key Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api-keys | List API keys |
| POST | /api-keys | Create API key |
| GET | /api-keys/{key_id} | Get API key details |
| PUT | /api-keys/{key_id} | Update API key |
| DELETE | /api-keys/{key_id} | Delete API key |
| POST | /api-keys/{key_id}/rotate | Rotate API key |

### Service Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /services | List registered services |
| POST | /services | Register service |
| GET | /services/{service_id} | Get service details |
| PUT | /services/{service_id} | Update service |
| DELETE | /services/{service_id} | Deregister service |
| GET | /services/{service_id}/health | Check service health |
| GET | /services/{service_id}/endpoints | List service endpoints |

### Service Proxying

The API Gateway provides dynamic routes to all backend services. For example:

- **GET /api/v1/projects** → Project Coordinator service
- **GET /api/v1/agents** → Agent Orchestrator service
- **GET /api/v1/tasks** → Planning System service
- **GET /api/v1/models** → Model Orchestration service
- **GET /api/v1/tools** → Tool Integration service
- **GET /api/v1/workflows** → Service Integration service

### Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /docs | OpenAPI documentation UI |
| GET | /openapi.json | OpenAPI specification in JSON format |
| GET | /docs/{service_id} | Service-specific documentation |
| GET | /redoc | ReDoc documentation UI |

### Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Gateway health check |
| GET | /health/services | Check all service health |
| GET | /metrics | Prometheus metrics |
| GET | /traffic | Traffic statistics |
| GET | /usage | API usage statistics |
| GET | /errors | Error statistics |

## Request/Response Examples

### Authentication

Request:

```http
POST /auth/login HTTP/1.1
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "securepassword123"
}
```

Response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "username": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user", "admin"]
  }
}
```

### API Key Creation

Request:

```http
POST /api-keys HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "name": "Development Key",
  "expires_in_days": 30,
  "permissions": ["projects.read", "projects.write", "agents.read"]
}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "key": "sak_dev_abcdefghijklmnopqrstuvwxyz",
  "name": "Development Key",
  "permissions": ["projects.read", "projects.write", "agents.read"],
  "created_at": "2025-03-29T07:15:00.123456Z",
  "expires_at": "2025-04-28T07:15:00.123456Z"
}
```

### Service Registration

Request:

```http
POST /services HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "name": "project-coordinator",
  "version": "1.0.0",
  "base_url": "http://project-coordinator:8080",
  "health_check_path": "/health",
  "endpoints": [
    {
      "path": "/projects",
      "method": "GET",
      "name": "list_projects",
      "description": "List all projects",
      "public": false,
      "required_roles": ["user", "admin"]
    },
    {
      "path": "/projects/{project_id}",
      "method": "GET",
      "name": "get_project",
      "description": "Get project details",
      "public": false,
      "required_roles": ["user", "admin"]
    }
  ]
}
```

Response:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "b2c3d4e5-f6g7-h8i9-j0k1-l2m3n4o5p6q7",
  "name": "project-coordinator",
  "version": "1.0.0",
  "base_url": "http://project-coordinator:8080",
  "health_check_path": "/health",
  "active": true,
  "endpoints": [
    {
      "id": "c3d4e5f6-g7h8-i9j0-k1l2-m3n4o5p6q7r8",
      "path": "/projects",
      "method": "GET",
      "name": "list_projects",
      "description": "List all projects",
      "public": false,
      "deprecated": false,
      "version": "1.0.0"
    },
    {
      "id": "d4e5f6g7-h8i9-j0k1-l2m3-n4o5p6q7r8s9",
      "path": "/projects/{project_id}",
      "method": "GET",
      "name": "get_project",
      "description": "Get project details",
      "public": false,
      "deprecated": false,
      "version": "1.0.0"
    }
  ],
  "created_at": "2025-03-29T07:30:00.123456Z",
  "updated_at": "2025-03-29T07:30:00.123456Z"
}
```

## Authentication Methods

The API Gateway supports multiple authentication methods:

### JWT Authentication

- **Access Token**: Short-lived token for API access
- **Refresh Token**: Long-lived token for access token renewal
- **Token Validation**: Signature and claims validation
- **Token Revocation**: Support for token revocation
- **Claims-Based Authorization**: Role and permission claims

### API Key Authentication

- **Key Generation**: Secure API key generation
- **Key Validation**: API key validation and permission checking
- **Scoped Keys**: Keys with limited permissions
- **Key Rotation**: Support for API key rotation
- **Key Expiration**: Automatic key expiration

### OAuth 2.0

- **Authorization Code Flow**: For web applications
- **Implicit Flow**: For SPA applications
- **Client Credentials Flow**: For service-to-service authentication
- **Resource Owner Password Flow**: For trusted applications
- **Refresh Token Flow**: For token renewal

## Request Routing

The API Gateway uses dynamic routing to direct requests to the appropriate service:

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Auth as Authentication Service
    participant SD as Service Discovery
    participant Service as Backend Service
    
    Client->>Gateway: Request
    Gateway->>Auth: Authenticate Request
    Auth->>Gateway: Authentication Result
    
    alt Authentication Failed
        Gateway->>Client: 401 Unauthorized
    else Authentication Successful
        Gateway->>SD: Discover Service
        SD->>Gateway: Service Location
        
        alt Service Not Found
            Gateway->>Client: 404 Not Found
        else Service Found
            Gateway->>Service: Forward Request
            Service->>Gateway: Response
            Gateway->>Client: Formatted Response
        end
    end
```

## Rate Limiting

The service implements flexible rate limiting:

- **Global Limits**: Platform-wide request limits
- **Service Limits**: Limits per service
- **Endpoint Limits**: Limits per endpoint
- **User Limits**: Limits per user or API key
- **Dynamic Limits**: Adjustable limits based on user tier
- **Burst Handling**: Accommodation for traffic spikes
- **Rate Limit Headers**: Standard rate limit headers

Example rate limit configuration:

```json
{
  "global": {
    "requests_per_second": 1000,
    "burst": 2000
  },
  "services": {
    "model-orchestration": {
      "requests_per_second": 200,
      "burst": 400
    }
  },
  "endpoints": {
    "model-orchestration.execute": {
      "requests_per_second": 50,
      "burst": 100
    }
  },
  "user_tiers": {
    "free": {
      "requests_per_second": 5,
      "burst": 10,
      "daily_limit": 1000
    },
    "pro": {
      "requests_per_second": 20,
      "burst": 40,
      "daily_limit": 10000
    },
    "enterprise": {
      "requests_per_second": 100,
      "burst": 200,
      "daily_limit": null
    }
  }
}
```

## API Versioning

The service supports multiple versioning strategies:

- **URL Versioning**: `/api/v1/resource`
- **Header Versioning**: `Accept: application/vnd.berrys.v1+json`
- **Query Parameter Versioning**: `/api/resource?version=1`
- **Backward Compatibility**: Maintaining compatibility across versions
- **Version Negotiation**: Content negotiation for preferred version
- **Version Deprecation**: Graceful deprecation of older versions

## Response Formatting

The service standardizes response formats:

```json
{
  "data": {
    // Response data
  },
  "meta": {
    "version": "1.0.0",
    "timestamp": "2025-03-29T07:45:00.123456Z",
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 42,
      "pages": 5
    }
  },
  "links": {
    "self": "https://api.example.com/resources?page=1&per_page=10",
    "next": "https://api.example.com/resources?page=2&per_page=10",
    "prev": null,
    "first": "https://api.example.com/resources?page=1&per_page=10",
    "last": "https://api.example.com/resources?page=5&per_page=10"
  }
}
```

## Error Handling

The service implements standardized error responses:

```json
{
  "error": {
    "code": "authentication_failed",
    "message": "Invalid credentials provided.",
    "details": "The provided API key is not valid.",
    "status": 401,
    "request_id": "req_abcdefghijklmnopqrstuvwxyz",
    "timestamp": "2025-03-29T07:50:00.123456Z"
  }
}
```

Common error codes:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| authentication_required | 401 | Authentication is required |
| authentication_failed | 401 | Authentication failed |
| invalid_credentials | 401 | Invalid credentials provided |
| expired_token | 401 | Token has expired |
| insufficient_permissions | 403 | Insufficient permissions |
| not_found | 404 | Resource not found |
| method_not_allowed | 405 | Method not allowed |
| rate_limit_exceeded | 429 | Rate limit exceeded |
| validation_error | 422 | Validation error |
| service_unavailable | 503 | Service unavailable |
| internal_error | 500 | Internal server error |

## Integration Points

### Web Dashboard

- **Authentication**: Handle user authentication
- **API Access**: Provide API access for the dashboard
- **Documentation**: Serve API documentation
- **Usage Analytics**: Provide API usage analytics

### Service Discovery

- **Service Registration**: Register services
- **Service Health Checking**: Check service health
- **Service Selection**: Select appropriate service instance
- **Load Balancing**: Distribute traffic across service instances

### Backend Services

- **Request Forwarding**: Forward requests to backend services
- **Response Handling**: Process responses from backend services
- **Error Handling**: Handle service errors
- **Circuit Breaking**: Implement circuit breaking for service failures

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
DATABASE_URL=postgresql://user:password@localhost:5432/api_gateway
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30
SERVICE_DISCOVERY_URL=http://service-discovery:8080
LOG_LEVEL=INFO
CORS_ORIGINS=https://dashboard.example.com,https://admin.example.com
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

- **http_request_duration_seconds**: HTTP request duration histogram
- **http_request_count**: Count of HTTP requests by endpoint and status
- **authentication_failures**: Count of authentication failures
- **rate_limit_hits**: Count of rate limit hits
- **service_request_duration_seconds**: Service request duration histogram
- **service_request_count**: Count of requests to backend services
- **service_error_count**: Count of backend service errors

## Performance Considerations

- **Connection Pooling**: Reuse connections to backend services
- **Caching**: Cache service discovery results and frequently accessed data
- **Compression**: Compress response bodies
- **Asynchronous Processing**: Use asynchronous request handling
- **Load Shedding**: Reject requests during overload
- **Request Prioritization**: Prioritize critical requests
- **Batching**: Support batched operations
- **Response Streaming**: Stream large responses

## Security Considerations

- **TLS Termination**: Secure communication with clients
- **Authentication**: Strict authentication requirements
- **Authorization**: Fine-grained authorization checks
- **Input Validation**: Validate all request parameters
- **Rate Limiting**: Prevent abuse through rate limiting
- **IP Filtering**: Optional IP-based access control
- **Audit Logging**: Log all access attempts
- **CORS**: Configurable CORS policy
- **Security Headers**: Standard security headers

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Authentication failures | Invalid credentials, expired tokens | Check credentials, refresh tokens |
| Rate limiting issues | Excessive requests, misconfigured limits | Optimize request rate, adjust limits |
| Service unavailability | Backend service down, network issues | Check service health, implement retries |
| Performance bottlenecks | High traffic, slow backends | Optimize routing, implement caching |
| Timeout errors | Slow backend responses | Adjust timeout settings, optimize backend |
| Routing errors | Service misconfiguration, missing routes | Verify service registration, check routes |
| Certificate issues | Expired certificates, trust issues | Update certificates, verify trust chain |
| JWT validation errors | Invalid claims, signature issues | Check JWT configuration, update keys |

## References

- [System Overview](../architecture/system-overview.md)
- [Communication Patterns](../architecture/communication-patterns.md)
- [Data Flow](../architecture/data-flow.md)
- [Security Model](../architecture/security-model.md)
- [Web Dashboard Service](web-dashboard.md)
- [Project Coordinator Service](project-coordinator.md)
- [Agent Orchestrator Service](agent-orchestrator.md)
