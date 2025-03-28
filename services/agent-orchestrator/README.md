# Agent Orchestrator Service

The Agent Orchestrator Service is responsible for managing the lifecycle, state, and communication of agents within the Berrys_AgentsV2 platform. It provides a robust framework for agent creation, configuration, state management, and inter-agent communication.

## Features

- **Agent Lifecycle Management**: Create, initialize, activate, pause, and terminate agents using a state machine
- **Agent State Management**: Maintain and persist agent state with checkpointing for reliability and recovery
- **Agent Configuration Templating**: Create and manage reusable agent templates with validation
- **Agent Communication**: Enable inter-agent messaging and coordination
- **Command Handling**: Process and execute commands for agents through a message bus
- **Background Task Management**: Handle long-running agent operations asynchronously

## Architecture

The service follows a clean architecture pattern with the following components:

- **API Layer**: FastAPI routes and endpoints for service interaction
- **Service Layer**: Business logic and orchestration of agent operations
- **Data Layer**: SQLAlchemy models and PostgreSQL database persistence
- **Messaging Layer**: Event and command handling via Redis message bus

### Key Components

1. **Agent Lifecycle Manager**
   - Implements the agent state machine (CREATED → INITIALIZING → READY → ACTIVE → PAUSED → TERMINATED)
   - Manages state transitions with validation
   - Handles background tasks for agent operations
   - Provides recovery from failures

2. **State Manager**
   - Persists agent runtime state
   - Creates and restores checkpoints
   - Merges state updates efficiently
   - Provides recovery points for agent operations

3. **Template Service**
   - Manages reusable agent configurations
   - Validates template schemas
   - Applies templates to new agents
   - Handles template versioning

4. **Communication Service**
   - Facilitates inter-agent messaging
   - Ensures reliable message delivery
   - Tracks message history
   - Supports different communication patterns

## API Endpoints

### Agents

- `POST /api/agents`: Create a new agent
- `GET /api/agents`: List agents
- `GET /api/agents/{agent_id}`: Get agent details
- `PUT /api/agents/{agent_id}`: Update agent
- `DELETE /api/agents/{agent_id}`: Delete agent
- `POST /api/agents/{agent_id}/execute`: Execute agent on a task

### Lifecycle

- `POST /api/agents/{agent_id}/status`: Change agent status
- `POST /api/agents/{agent_id}/initialize`: Initialize agent
- `POST /api/agents/{agent_id}/activate`: Activate agent
- `POST /api/agents/{agent_id}/pause`: Pause agent
- `POST /api/agents/{agent_id}/terminate`: Terminate agent
- `GET /api/agents/{agent_id}/history`: Get agent state history

### State

- `GET /api/agents/{agent_id}/state`: Get agent state
- `PUT /api/agents/{agent_id}/state`: Update agent state
- `POST /api/agents/{agent_id}/checkpoint`: Create checkpoint
- `DELETE /api/agents/{agent_id}/checkpoint`: Delete checkpoint
- `POST /api/agents/{agent_id}/schedule-checkpoint`: Schedule checkpoint

### Templates

- `POST /api/templates`: Create a new template
- `GET /api/templates`: List templates
- `GET /api/templates/{template_id}`: Get template details
- `PUT /api/templates/{template_id}`: Update template
- `DELETE /api/templates/{template_id}`: Delete template

### Communications

- `POST /api/agents/{agent_id}/send`: Send communication
- `POST /api/communications/{communication_id}/delivered`: Mark as delivered
- `GET /api/agents/{agent_id}/communications`: Get communications
- `GET /api/communications/{communication_id}`: Get communication details

## Development

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file):
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/agent_orchestrator
   REDIS_URL=redis://localhost:6379/0
   JWT_SECRET=your_secret_key
   ```

4. Run the service:
   ```bash
   uvicorn src.main:app --reload
   ```

### Docker

Build and run with Docker:

```bash
docker build -t agent-orchestrator .
docker run -p 8000:8000 --env-file .env agent-orchestrator
```

## Testing

Run tests with pytest:

```bash
pytest
```

## Integration with Other Services

The Agent Orchestrator Service integrates with:

- **Model Orchestration Service**: For agent model inference
- **Project Coordinator Service**: For project-level coordination
- **Tool Integration Service**: For agent tool access
- **Planning System Service**: For task planning and decomposition

## License

See the project LICENSE file for details.
