# Project-based Multi-Agent System Framework

A comprehensive framework for creating, managing, and deploying project-based multi-agent systems with autonomous agent generation, specialized tool integration, strategic planning, and deployment automation.

## Features

### Core Components

- **Autonomous Agent Generation System**: Transforms project descriptions into custom agents automatically, inspired by Archon architecture.
- **Specialist MCP Agent**: Discovers and integrates external tools, connecting agent creation with the right tooling.
- **Planning Agent Team**: Breaks down research, tasks, and management into clear steps for smooth execution.
- **Deployment Agent**: Triggers the right managers or agents to launch projects precisely.

### Infrastructure & Enhancements

- **PostgreSQL Database Backbone**: Core repository for project details, agent configurations, prompts, logs, embeddings, and vector stores.
- **Auditing & Continuous Optimization**: Generates detailed audit logs and performance metrics, using similarity searches and historical data to refine prompts.
- **Human-in-the-Loop Protocol**: Determines when actions need human approval, tracked transparently.

## Architecture

The framework is built using a microservices architecture with the following components:

- **API Gateway**: Entry point for web dashboard and external API requests.
- **Agent Orchestrator**: Manages agent lifecycle and coordination.
- **Planning System**: Handles project planning and task breakdown.
- **Model Orchestration**: Intelligently routes requests to the most appropriate AI model.
- **Tool Integration**: Discovers, evaluates, and integrates external tools.
- **Project Coordinator**: Manages project lifecycle and coordination.

## Technology Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with pgvector for vector storage
- **AI Models**: Support for local Ollama models, OpenAI GPT models, and Anthropic Claude models
- **Messaging**: Redis for inter-service communication
- **Containerization**: Docker for deployment
- **Web Dashboard**: React-based interface

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+ (for web dashboard)
- PostgreSQL 15+
- Redis

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/project-mas-framework.git
   cd project-mas-framework
   ```

2. Create a `.env` file with the required environment variables:
   ```
   # Database
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=mas_framework

   # Authentication
   JWT_SECRET=your-secret-key
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # AI Models
   OPENAI_API_KEY=your-openai-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key

   # Environment
   ENVIRONMENT=development
   ```

3. Build and start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the web dashboard at http://localhost:3000

### Development Setup

1. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd services/web-dashboard
   npm install
   ```

3. Run the services individually for development:
   ```bash
   # API Gateway
   cd services/api-gateway
   uvicorn src.main:app --reload

   # Web Dashboard
   cd services/web-dashboard
   npm run dev
   ```

## Project Structure

```
project-mas-framework/
├── docker-compose.yml
├── shared/
│   ├── database/
│   ├── models/
│   └── utils/
├── services/
│   ├── api-gateway/
│   ├── agent-orchestrator/
│   ├── planning-system/
│   ├── model-orchestration/
│   ├── tool-integration/
│   ├── project-coordinator/
│   └── web-dashboard/
└── docs/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
