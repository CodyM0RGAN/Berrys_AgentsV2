# Service Integration Service

The Service Integration Service is a core component of the Berrys_AgentsV2 system that provides cross-service communication, discovery, and orchestration capabilities. It serves as the glue that binds together all the different microservices in the system.

## Core Capabilities

The Service Integration Service provides several key capabilities:

1. **Service Discovery**: Allows services to find and connect to each other dynamically
2. **Service Registry**: Enables services to register their capabilities and endpoints
3. **Cross-Service Workflows**: Coordinates operations across multiple services
4. **System Health Monitoring**: Tracks the health of all registered services
5. **Circuit Breaking**: Prevents cascading failures across the system

## Architecture

The service follows a layered architecture with clean separation of concerns:

```
┌────────────────────────────────────────────────────────────────────┐
│                              API Layer                             │
│          (FastAPI Routers for Registry, Discovery, Workflows)      │
└───────────────────────────────────┬────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                       SystemIntegrationFacade                      │
│             (Main entry point and coordination layer)              │
└─────────┬───────────────────┬─────────────────────┬───────────────┘
          │                   │                     │
          ▼                   ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ServiceDiscovery │   │ RequestMediator │   │    ServiceClient    │
│      Layer      │   │      Layer      │   │        Layer        │
└─────────────────┘   └─────────────────┘   └─────────────────────┘
          │                   │                     │
          ▼                   ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│  Redis/etcd/etc │   │Workflow Handlers│   │   CircuitBreaker    │
│(Discovery Store)│   │(Implementation) │   │     Protection      │
└─────────────────┘   └─────────────────┘   └─────────────────────┘
```

### Key Components

1. **Service Discovery**: Implements the Strategy Pattern to support multiple discovery backends (Redis, Consul, etcd)
2. **Request Mediator**: Implements the Mediator Pattern for decoupling service communication
3. **Circuit Breaker**: Implements the Circuit Breaker Pattern for resilience
4. **Workflow Implementations**: Coordinates complex operations across services
5. **Integration Facade**: Provides a simplified interface to all functionality

## Design Patterns Used

The service makes extensive use of several design patterns:

1. **Facade Pattern**: `SystemIntegrationFacade` simplifies the API for accessing integration functionality
2. **Strategy Pattern**: `ServiceDiscoveryStrategy` allows for plugging in different discovery mechanisms
3. **Mediator Pattern**: `RequestMediator` decouples request senders from handlers
4. **Factory Pattern**: `ServiceDiscoveryFactory` creates the appropriate discovery strategies
5. **Circuit Breaker Pattern**: `CircuitBreaker` prevents cascading failures
6. **Dependency Injection**: All components are wired up using FastAPI's dependency injection system

## API Endpoints

The service exposes the following API endpoints:

### Service Registry

- `POST /registry/services`: Register a service
- `DELETE /registry/services/{service_id}`: Unregister a service
- `GET /registry/services/{service_id}`: Get service information
- `POST /registry/services/{service_id}/heartbeat`: Update service heartbeat
- `PUT /registry/services/{service_id}/status`: Update service status

### Service Discovery

- `GET /discovery/services`: Find services by criteria
- `POST /discovery/services/search`: Search for services with complex criteria
- `GET /discovery/services/type/{service_type}`: Get a service by type
- `GET /discovery/health/{service_id}`: Check service health

### Workflows

- `POST /workflows/execute`: Execute a cross-service workflow
- `POST /workflows/agent-task-execution`: Execute an agent task workflow
- `POST /workflows/project-planning`: Execute a project planning workflow

### Health Checks

- `GET /health/system`: Get overall system health
- `GET /health/ready`: Readiness check
- `GET /health/alive`: Liveness check
- `GET /health/circuit-breakers`: Get circuit breaker status

## How to Build and Run

### Prerequisites

- Python 3.11 or later
- Docker (for containerized deployment)
- Redis (for service discovery)
- PostgreSQL (for persistent storage)

### Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8090
   ```

4. Access the API documentation at: http://localhost:8090/docs

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t service-integration:latest .
   ```

2. Run the container:
   ```bash
   docker run -p 8090:8090 -e REDIS_HOST=redis -e POSTGRES_HOST=postgres service-integration:latest
   ```

### Configuration

The service can be configured through environment variables:

- `SERVICE_NAME`: Name of the service (default: "service-integration")
- `SERVICE_PORT`: Port to run on (default: 8090)
- `REDIS_HOST`: Redis host (default: "localhost")
- `REDIS_PORT`: Redis port (default: 6379)
- `POSTGRES_HOST`: PostgreSQL host (default: "localhost")
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_USER`: PostgreSQL username (default: "postgres")
- `POSTGRES_PASSWORD`: PostgreSQL password (default: "postgres")
- `POSTGRES_DB`: PostgreSQL database name (default: "berrys_integration")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Contributing

1. Follow the project's coding standards (PEP 8)
2. Write tests for new functionality
3. Update documentation for any changes
4. Submit pull requests with proper descriptions

## License

See the main project repository for license information.
