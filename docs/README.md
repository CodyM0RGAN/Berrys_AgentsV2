# Berrys_AgentsV2 Documentation

> **Note for Claude**: This documentation serves as your internal knowledge base for the Berrys_AgentsV2 project. Use draft-of-thought techniques to keep notes concise and organized, ensuring you maintain the same state-of-mind when returning to this project in the future.
>
> **Important**: For a structured onboarding guide specifically designed for Claude agents, please refer to the [Claude Agent Guide](./CLAUDE_AGENT_GUIDE.md).
>
> **Recent Updates (2025-03-28)**:
>
> 1. **Agent Specialization System Implementation (March 28, 2025)**
>    - Implemented database-driven agent specializations
>    - Created API endpoints for managing agent specializations
>    - Integrated with requirement analysis service
>    - Added migration scripts for database setup
>    - See [Agent Specialization Guide](developer-guides/service-development/agent-specialization-guide.md) and [Agent Specialization Implementation](developer-guides/service-development/agent-specialization-implementation.md) for details
>
> 2. **Planning System Enhancement Implementation (March 28, 2025)**
>    - Implemented task templates for standardized planning
>    - Added dependency type management and validation
>    - Implemented what-if analysis for scenario-based planning
>    - Created comprehensive API endpoints for all new features
>    - See [Planning System Enhancement Implementation](developer-guides/service-development/planning-system-enhancement-implementation.md) for details
>
> 2. **Resource Allocation Planning Implementation (March 28, 2025)**
>    - Implemented resource modeling with skills, availability, and constraints
>    - Added resource allocation algorithms with overallocation detection
>    - Created API endpoints for resource management and allocation
>    - Implemented resource utilization analysis
>    - See [Resource Allocation Planning Implementation](developer-guides/service-development/resource-allocation-planning-implementation.md) for details
>
> 2. **Service Startup Issues Fixed (March 28, 2025)**
>    - Fixed all service startup issues across the system
>    - Resolved async/sync mismatch in Web Dashboard
>    - Fixed PostgreSQL authentication for pgvector
>    - Fixed import path issues for FastAPI/Starlette middleware
>    - Fixed reserved attribute names in SQLAlchemy models
>    - Updated Redis client code to use redis.asyncio
>    - Added missing exception classes
>    - Resolved circular import issues in Web Dashboard
>    - See [Service Startup Troubleshooting Guide](developer-guides/service-development/service-startup-troubleshooting.md) for details
>
> 2. **Documentation Consolidation (March 27, 2025)**
>    - Consolidated multiple documentation files to make the documentation more concise while preserving knowledge
>    - Created [Agent Communication Hub Guide](developer-guides/service-development/agent-communication-hub-guide.md) that consolidates 8 separate files
>    - Created [Service Migration History](developer-guides/service-development/service-migration-history.md) that consolidates 6 service migration implementation documents
>    - Created [Service Standardization Guide](developer-guides/service-development/service-standardization-guide.md) that consolidates service standardization plan and summary
>    - Shortened CLAUDE_AGENT_GUIDE.md and README.md to remove redundant information
>
> 3. **Web Dashboard Workflows Implementation (March 27, 2025)**
>    - Implemented workflows for submitting, initiating, planning, and deploying projects in the Web Dashboard
>    - Created comprehensive documentation in [Web Dashboard Workflows](developer-guides/service-development/web-dashboard-workflows.md)
>
> 4. **Revised Implementation Plan (March 27, 2025)**
>    - Revised the implementation plan to prioritize core service workflows before extensive testing
>    - New focus on implementing Planning System and Agent Generation Engine services
>
> 5. **Cross-Service Communication Improvements (March 27, 2025)**
>    - Implemented retry mechanisms with exponential backoff in all service clients
>    - See [Cross-Service Communication Improvements](developer-guides/service-development/cross-service-communication-improvements.md) for details
>
> 6. **Planning System High-Level Capabilities Implementation (March 27, 2025)**
>    - Implemented high-level planning capabilities in the Planning System
>    - Refactored the service into smaller, more manageable modules
>    - Added template-based planning, methodology-driven planning, and AI-assisted plan generation
>    - Implemented timeline forecasting and bottleneck analysis
>    - See [Planning System High-Level Capabilities Implementation](developer-guides/service-development/planning-system-high-level-capabilities-implementation.md) for details
>    - Updated [Planning System Enhancement Plan](developer-guides/service-development/planning-system-enhancement-plan.md) with current progress and next steps

## Executive Summary

Berrys_AgentsV2 is a framework for creating, managing, and deploying project-based multi-agent systems. The system transforms high-level project descriptions into specialized AI agents that work together to accomplish complex tasks. Built on a microservices architecture with PostgreSQL database, Redis messaging, and support for multiple AI model providers.

## Project Status Dashboard

| Component | Status | Implementation | Notes |
|-----------|--------|----------------|-------|
| **User Interface Layer** |  |  |  |
| Web Dashboard | ✅ Implemented | 95% | React-based frontend with project workflows |
| REST API Gateway | ✅ Implemented | 80% | FastAPI-based gateway with core routing |
| **Framework Core** |  |  |  |
| Project Coordinator | ✅ Implemented | 85% | Core project management functionality |
| Agent Orchestrator | ✅ Implemented | 80% | Agent lifecycle management |
| **Autonomous Agent System** |  |  |  |
| Agent Generation Engine | ✅ Completed | 100% | Enhanced agent generation capabilities with collaboration patterns |
| Agent Template Engine | 🔄 In Progress | 70% | Template management system |
| Agent Specialization System | ✅ Completed | 100% | Database-driven agent specializations |
| Agent Communication Hub | ✅ Implemented | 100% | Enhanced routing, priority queuing, pub/sub patterns |
| **Planning System** |  |  |  |
| Planning Strategist | ✅ Completed | 100% | Enhanced strategic planning capabilities |
| Planning Tactician | ✅ Completed | 100% | Improved task breakdown functionality |
| Project Forecaster | ✅ Completed | 100% | Implementation of forecasting features |
| Resource Allocation | ✅ Implemented | 100% | Resource management and allocation |
| Task Templates | ✅ Implemented | 100% | Standardized task templates |
| Dependency Management | ✅ Implemented | 100% | Enhanced dependency type management |
| What-If Analysis | ✅ Implemented | 100% | Scenario-based planning analysis |
| **Tool Integration** |  |  |  |
| MCP Integration Hub | ✅ Implemented | 75% | Core MCP server integration |
| Tool Curator | 🔄 In Progress | 40% | Basic tool discovery |
| Tool Registry | ✅ Implemented | 80% | Tool metadata storage |
| **Service Standardization** |  |  |  |
| All Services | ✅ Completed | 100% | Standardized models, enums, and database schema |

## Documentation Organization

The Berrys_AgentsV2 documentation follows a structured organization designed to help you find the information you need quickly and build a comprehensive mental model of the system.

### 1. Core Documentation
- **README.md**: This document, providing an overview of the project
- **[CLAUDE_AGENT_GUIDE.md](./CLAUDE_AGENT_GUIDE.md)**: Specific guidance for Claude agents working on the project
- **[Documentation Maintenance Plan](./documentation-maintenance-plan.md)**: Guidelines for keeping documentation organized

### 2. Hierarchical Structure
- **User Guides**: End-user focused documentation
- **Architecture**: System design and component interaction documentation
- **Developer Guides**: Technical documentation for developers
- **Best Practices**: Guidelines for working with specific technologies
- **Reference**: Detailed technical specifications

## Documentation Roadmap

For a comprehensive understanding of the project, follow this guided tour:

### 1. System Architecture (Start Here)
- [System Overview](architecture/system-overview.md) - High-level architecture and component interactions
- [Architecture](architecture/index.md) - Detailed service design

### 2. Model and Service Standardization
- [Model Standardization Progress](developer-guides/service-development/model-standardization-progress.md)
- [Model Mapping System](developer-guides/service-development/model-mapping-system.md)
- [Entity Representation Alignment](developer-guides/service-development/entity-representation-alignment.md)
- [Service Standardization Guide](developer-guides/service-development/service-standardization-guide.md)
- [Service Migration History](developer-guides/service-development/service-migration-history.md)

### 3. Service Integration and Troubleshooting
- [Web Dashboard Workflows](developer-guides/service-development/web-dashboard-workflows.md)
- [Agent Communication Hub Guide](developer-guides/service-development/agent-communication-hub-guide.md)
- [Troubleshooting Guide](developer-guides/service-development/troubleshooting-guide.md)

## Current Milestones and Next Phases

### Current Focus

1. **Implement Key Service Workflows**
   - ✅ Enhance Planning System with high-level planning capabilities
   - ✅ Implement Resource Allocation Planning in Planning System
   - ✅ Implement Task Templates, Dependency Management, and What-If Analysis
   - ✅ Implement Agent Specialization System for dynamic agent configuration
   - 🔄 Continue improving Agent Generation Engine
   - See [Planning System Enhancement Plan](developer-guides/service-development/planning-system-enhancement-plan.md), [Planning System High-Level Capabilities Implementation](developer-guides/service-development/planning-system-high-level-capabilities-implementation.md), [Resource Allocation Planning Implementation](developer-guides/service-development/resource-allocation-planning-implementation.md), [Planning System Enhancement Implementation](developer-guides/service-development/planning-system-enhancement-implementation.md), and [Agent Specialization Implementation](developer-guides/service-development/agent-specialization-implementation.md) for details

2. **Project Dashboard Enhancement**
   - ✅ Implement project progress visualization
   - 🔄 Implement additional dashboard widgets
   - See [Web Dashboard Workflows](developer-guides/service-development/web-dashboard-workflows.md) for details

3. **Documentation Maintenance and Enhancement**
   - ✅ Implement Documentation Maintenance Plan
   - ✅ Consolidate documentation files to improve maintainability
   - See [Documentation Maintenance Plan](documentation-maintenance-plan.md) for details

### Upcoming Phases

1. **Service Migration Verification and Testing**
   - Update tests to verify functionality of migrated services
   - Remove redundant code from migrated services

2. **Model Standardization Phase 8-9: Testing, Verification, and Documentation**
   - Create database migration tests
   - Add model unit tests
   - Create integration tests

3. **New Project Creation Automation**
   - Create script to automate new project setup
   - Implement database initialization for new projects

## Architecture Reference

### Key Components

1. **User Interface Layer**
   - Web Dashboard: React-based frontend for user interaction
   - REST API Gateway: FastAPI-based entry point for all requests

2. **Framework Core**
   - Project Coordinator: Manages project lifecycle and coordination
   - Agent Orchestrator: Manages agent lifecycle and coordination

3. **Autonomous Agent System**
   - Agent Generation Engine: Transforms requirements into specialized agents
   - Agent Template Engine: Maintains and customizes agent templates
   - Agent Communication Hub: Facilitates communication between agents

4. **Planning System**
   - Planning Strategist: Handles high-level project planning
   - Planning Tactician: Breaks down plans into executable tasks
   - Project Forecaster: Predicts timelines and identifies bottlenecks

5. **Tool Integration**
   - MCP Integration Hub: Integrates with Model Context Protocol servers
   - Tool Curator: Discovers and evaluates external tools
   - Tool Registry: Maintains a registry of available tools

### Service Boundary Adapters

The system uses adapters to convert entities between different service representations:

1. **WebToCoordinatorAdapter**: Converts between Web Dashboard and Project Coordinator
2. **CoordinatorToAgentAdapter**: Converts between Project Coordinator and Agent Orchestrator
3. **AgentToModelAdapter**: Converts between Agent Orchestrator and Model Orchestration
4. **PlanningToAgentAdapter**: Converts between Planning System and Agent Orchestrator

## Troubleshooting

### Recent Solutions

1. **Cross-Service Communication Improvements** (2025-03-27)
   - Issue: Unreliable communication between Web Dashboard and backend services
   - Solution: Implemented retry mechanisms with exponential backoff in all service clients
   - See [Cross-Service Communication Improvements](developer-guides/service-development/cross-service-communication-improvements.md) for details

2. **Task Assignment Failures** (2025-03-27)
   - Issue: Task assignments not properly propagated between Planning System and Agent Orchestrator
   - Solution: Enhanced the `PlanningToAgentAdapter` to handle field name differences
   - See [Entity Representation Alignment](developer-guides/service-development/entity-representation-alignment.md#planning-system--agent-orchestrator) for details

3. **Service Startup Issues** (2025-03-27)
   - Issue: Multiple services failing to start with various errors
   - Solution: Fixed dependencies, class definitions, and configuration issues
   - See [Service Startup Troubleshooting Guide](developer-guides/service-development/service-startup-troubleshooting.md) for details

## Quick Start

If you're new to Berrys_AgentsV2, here are some good places to start:

- [Getting Started](user-guides/getting-started.md): First steps with Berrys_AgentsV2
- [System Overview](architecture/system-overview.md): High-level overview of the system architecture
- [Service Development Guide](developer-guides/service-development/index.md): Guide for developing new services
