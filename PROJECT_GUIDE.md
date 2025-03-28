# Berrys_AgentsV2 Project Guide

This guide provides a quick overview of the Berrys_AgentsV2 project structure and points to the comprehensive documentation.

## Project Overview

Berrys_AgentsV2 is a comprehensive framework for creating, managing, and deploying project-based multi-agent systems with autonomous agent generation, specialized tool integration, strategic planning, and deployment automation.

## Project Structure

```
Berrys_AgentsV2/
├── docs/                 # Comprehensive documentation
├── services/             # Microservices that make up the system
│   ├── api-gateway/      # Entry point for all API requests
│   ├── agent-orchestrator/ # Manages agent lifecycle
│   ├── model-orchestration/ # Routes requests to AI models
│   ├── planning-system/  # Handles project planning
│   ├── project-coordinator/ # Manages project lifecycle
│   ├── service-integration/ # Integrates with external services
│   ├── tool-integration/ # Integrates with external tools
│   └── web-dashboard/    # User interface
├── shared/               # Shared code used by multiple services
│   ├── database/         # Database scripts and utilities
│   ├── models/           # Shared data models
│   └── utils/            # Shared utilities
├── scripts/              # Utility scripts
├── backups/              # Database backups
└── logs/                 # Log files
```

## Key Components

- **API Gateway**: Entry point for web dashboard and external API requests
- **Agent Orchestrator**: Manages agent lifecycle and coordination
- **Planning System**: Handles project planning and task breakdown
- **Model Orchestration**: Intelligently routes requests to the most appropriate AI model
- **Tool Integration**: Discovers, evaluates, and integrates external tools
- **Project Coordinator**: Manages project lifecycle and coordination

## Current Focus

The project is currently focused on:

1. **Service Standardization Initiative**: Standardizing service implementations and centralizing redundant code
2. **Model Standardization Phase 10**: Service standardization and centralization
3. **Agent Communication Hub Enhancement**: Improving message routing between agents

## Comprehensive Documentation

For detailed documentation, please refer to the [docs/README.md](docs/README.md) file, which serves as the entry point to the comprehensive documentation. It includes:

- Project status dashboard
- Documentation roadmap
- Current milestones and next phases
- Architecture reference
- Development workflows
- Troubleshooting guide

## Getting Started

1. Review the [docs/README.md](docs/README.md) file for a comprehensive overview
2. Explore the [System Overview](docs/architecture/system-overview.md) for architecture details
3. Check the [Model Standardization Progress](docs/developer-guides/service-development/model-standardization-progress.md) for current implementation status

## For Claude Agents

When working on this project, always start by reading the [Claude Agent Guide](docs/CLAUDE_AGENT_GUIDE.md), which provides a structured onboarding guide specifically designed for Claude agents. This guide includes:

- A recommended sequence for exploring the documentation
- Common workflows for development tasks
- Best practices for Claude agents
- Collaboration guidelines for teams of Claude agents

For more detailed information, refer to [docs/README.md](docs/README.md), which contains additional notes for Claude agents and provides a comprehensive mental model of the system.
