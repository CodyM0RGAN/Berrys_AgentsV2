# Getting Started with Project-based MAS Framework

This guide will help you set up and start using the Project-based Multi-Agent System Framework.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker and Docker Compose**: For containerized deployment
- **Python 3.11+**: For running Python scripts and development
- **Node.js 18+**: For the web dashboard (if developing frontend)
- **Git**: For version control

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/project-mas-framework.git
cd project-mas-framework
```

### 2. Set Up Environment Variables

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file to set your configuration:

```
# Database
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_NAME=mas_framework

# Authentication
JWT_SECRET=your_secure_jwt_secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Models
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OLLAMA_URL=http://ollama:11434

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development
```

### 3. Run the Setup Script

The setup script will create necessary directories, Docker volumes, and install dependencies:

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 4. Start the Services

Start all services using Docker Compose:

```bash
docker-compose up -d
```

This will start the following services:
- PostgreSQL database
- Redis for messaging
- Ollama for local AI models
- API Gateway
- Agent Orchestrator
- Planning System
- Model Orchestration
- Tool Integration
- Project Coordinator
- Web Dashboard

### 5. Access the Web Dashboard

Once all services are running, you can access the web dashboard at:

```
http://localhost:3000
```

Log in with the default admin credentials:
- Username: `admin`
- Password: `admin`

**Important**: Change the default password after your first login.

## Basic Usage

### Creating a Project

1. Log in to the web dashboard
2. Click on "New Project"
3. Fill in the project details:
   - Name
   - Description
   - Any additional metadata
4. Click "Create Project"

### Generating Agents

1. Navigate to your project
2. Click on "Generate Agents"
3. Provide a detailed description of your project requirements
4. Click "Generate"
5. Review the generated agents and their configurations
6. Make any necessary adjustments
7. Click "Save Agents"

### Planning a Project

1. Navigate to your project
2. Click on "Create Plan"
3. The Planning Agent Team will analyze your project and agents
4. Review the generated plan, including:
   - Project phases
   - Tasks
   - Dependencies
   - Timeline
5. Make any necessary adjustments
6. Click "Approve Plan"

### Deploying a Project

1. Navigate to your project
2. Click on "Deploy"
3. Review the deployment configuration
4. Click "Start Deployment"
5. Monitor the deployment progress
6. Respond to any human-in-the-loop requests as needed

## Development Setup

If you want to develop or extend the framework, follow these additional steps:

### 1. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Frontend Development Environment

```bash
cd services/web-dashboard
npm install
```

### 3. Run Services Individually

For API Gateway:
```bash
cd services/api-gateway
uvicorn src.main:app --reload
```

For Web Dashboard:
```bash
cd services/web-dashboard
npm run dev
```

## Extending the Framework

### Adding a New Agent Type

1. Define the agent type in `shared/models/src/agent.py`
2. Create a template in the Agent Template Engine
3. Implement the agent's behavior in the Agent Orchestrator

### Adding a New Tool

1. Define the tool in `shared/models/src/tool.py`
2. Implement the tool integration in the Tool Integration service
3. Register the tool in the Tool Registry

### Adding a New Model Provider

1. Define the model provider in `shared/models/src/model.py`
2. Implement the adapter in the Model Orchestration service
3. Update the Model Decision Maker to consider the new provider

## Troubleshooting

### Services Not Starting

Check the logs for each service:

```bash
docker-compose logs api-gateway
docker-compose logs postgres
# etc.
```

### Database Connection Issues

Ensure PostgreSQL is running and accessible:

```bash
docker-compose exec postgres psql -U postgres -d mas_framework -c "SELECT 1"
```

### Model API Issues

Check your API keys in the `.env` file and ensure they are correctly set in the environment.

## Next Steps

- Read the [Architecture Documentation](architecture.md) for a deeper understanding of the system
- Explore the [API Documentation](api.md) for details on available endpoints
- Join our community for support and discussions
