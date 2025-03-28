# Berry's Agents Web Dashboard

A dynamic Flask web dashboard for monitoring and managing the Multi-Agent System (MAS) Framework. This dashboard provides a comprehensive UI for interacting with the REST API Gateway and visualizing system activity.

## Features

- **Dynamic UI**: Responsive interface that adapts to system activities
- **Customizable Dashboard**: Users can configure what information to display
- **Real-Time Chat Interface**: Interactive chatbot for submitting new project requests
- **Project Management**: Track and manage ongoing projects
- **Human-in-the-Loop**: Interface for human interaction with agents
- **Route-Based Architecture**: Direct route registration for simplified URL management

## Architecture

The web dashboard follows a modular architecture:

- **Routes**: Feature-specific route modules with direct registration
- **API Clients**: Client services for interacting with the REST API Gateway
- **Templates**: Jinja2 templates for rendering HTML
- **Static Files**: CSS, JavaScript and image assets

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Access to the REST API Gateway
- Redis (optional, for production caching and sessions)

### Installation

1. Clone the repository
2. Navigate to the web dashboard directory
```bash
cd services/web-dashboard
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4. Set up environment variables (or create a `.env` file)
```
FLASK_APP=run.py
FLASK_CONFIG=development
AGENT_ORCHESTRATOR_API_URL=http://localhost:8001
PROJECT_COORDINATOR_API_URL=http://localhost:8002
MODEL_ORCHESTRATION_API_URL=http://localhost:8003
```

### Running for Development

Start the development server:
```bash
flask run --debug
```

Or with Python directly:
```bash
python run.py
```

The dashboard will be available at `http://localhost:5000`

### Production Deployment

For production deployment, use Gunicorn:
```bash
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 4 "run:app"
```

## Configuration

The dashboard can be configured through the following environment variables:

- `FLASK_CONFIG`: Configuration environment (development, testing, production)
- `SECRET_KEY`: Secret key for session security
- `AGENT_ORCHESTRATOR_API_URL`: URL of the Agent Orchestrator API
- `PROJECT_COORDINATOR_API_URL`: URL of the Project Coordinator API
- `MODEL_ORCHESTRATION_API_URL`: URL of the Model Orchestration API
- `DATABASE_URL`: Database URL (SQLite by default)
- `REDIS_URL`: Redis URL for caching and sessions (production only)
- `ENABLE_WEBSOCKETS`: Enable/disable WebSocket support (default: True)

## Project Structure

```
services/web-dashboard/
├── app/                      # Application package
│   ├── api/                  # API client and services
│   │   ├── base.py           # Base API client
│   │   ├── clients.py        # Client initialization
│   │   ├── agent_orchestrator.py  # Agent Orchestrator client
│   │   └── project_coordinator.py # Project Coordinator client
│   ├── routes/               # Route modules
│   │   ├── main.py           # Main routes (home, dashboard)
│   │   ├── projects.py       # Projects routes
│   │   ├── chat.py           # Chat routes
│   │   ├── settings.py       # Settings routes
│   │   ├── auth.py           # Authentication routes
│   │   └── errors.py         # Error handlers
│   ├── static/               # Static files (CSS, JS, images)
│   │   ├── css/              # CSS files
│   │   ├── js/               # JavaScript files
│   │   └── img/              # Image files
│   ├── templates/            # HTML templates
│   │   ├── main/             # Main templates
│   │   ├── projects/         # Projects templates
│   │   ├── chat/             # Chat templates
│   │   ├── settings/         # Settings templates
│   │   └── errors/           # Error templates
│   └── __init__.py           # Application factory
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── README.md                 # This file
```

## Development Guidelines

- **Route-Based Pattern**: Each major feature has its own route module
- **Service Layer**: API communication is abstracted in client classes
- **Model-View-Template**: Separation of concerns between data, logic, and presentation
- **Responsive Design**: Mobile-first approach with Bootstrap
- **Real-Time Updates**: WebSocket integration for live data (planned)

## Contributing

Follow these steps to add a new feature:

1. Create a new route module in the `app/routes/` directory
2. Implement necessary API clients in `app/api/` if needed
3. Create templates in `app/templates/`
4. Register the routes in `app/routes/__init__.py`
5. Update the application factory in `app/__init__.py` if necessary

## Testing

Run tests with pytest:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=app
