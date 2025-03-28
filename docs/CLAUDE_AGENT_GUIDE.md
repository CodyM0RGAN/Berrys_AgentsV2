# Claude Agent Onboarding Guide

> **Note**: This guide is specifically designed for Claude agents working on the Berrys_AgentsV2 project. It provides a structured approach to understanding the project, common workflows, and best practices for effective collaboration.

## Getting Started

As a Claude agent working on this project, your first step should be to build a comprehensive mental model of the system. Follow this sequence to efficiently onboard:

1. **Read the Project Overview**
   - Start with [docs/README.md](README.md) for a comprehensive overview

2. **Understand the Architecture**
   - Review [System Overview](architecture/system-overview.md)
   - Study the service interactions in [Architecture Index](architecture/index.md)

3. **Explore the Model and Service Standardization**
   - Review [Model Standardization Progress](developer-guides/service-development/model-standardization-progress.md)
   - Understand the [Service Standardization Guide](developer-guides/service-development/service-standardization-guide.md)
   - Review the [Service Migration History](developer-guides/service-development/service-migration-history.md)

## Draft-of-Thought Documentation Approach

This project uses a "draft-of-thought" documentation approach for Claude agents. This means:

1. **Concise Notes**: Keep documentation concise and focused on key concepts
2. **Mental Model Building**: Document to build a comprehensive mental model
3. **Lessons Learned**: Document issues, solutions, and insights
4. **State Maintenance**: Ensure documentation helps maintain the same state-of-mind when returning to the project

## Common Workflows

### 1. Adding a New Feature Across Services

1. **Identify Affected Services**
   - Determine which services need modification
   - Understand the data flow between these services

2. **Update Models**
   - Start with shared models in `shared/models/src/`
   - Ensure proper adapter implementations for cross-service communication

3. **Implement Service-Specific Logic**
   - Follow the service structure in each affected service
   - Implement endpoints, services, and messaging components

4. **Test Cross-Service Integration**
   - Write integration tests that verify the end-to-end flow
   - Test boundary transformations using adapters

### 2. Debugging Cross-Service Issues

1. **Trace the Request Flow**
   - Start at the entry point (usually API Gateway or Web Dashboard)
   - Follow the request through each service boundary

2. **Check Adapter Transformations**
   - Verify that entity transformations are correct
   - Look for missing fields or incorrect types

3. **Examine Database State**
   - Check that database records match expected state
   - Verify foreign key relationships

4. **Review Service Logs**
   - Check logs for each service in the request path
   - Look for errors or unexpected behavior

5. **Test Service Endpoints Directly**
   - Use tools like curl or Postman to test service endpoints directly
   - Isolate which specific service or boundary is causing the issue

### 3. Implementing Model Changes

1. **Update Shared Models**
   - Modify the appropriate files in `shared/models/src/`
   - Ensure enum values are defined in `shared/models/src/enums.py`

2. **Update Adapters**
   - Modify adapters to handle the new fields or types
   - Add tests for the adapter changes

3. **Create Database Migrations**
   - Create migration scripts for each affected service
   - Test migrations on a development database

4. **Update API Models**
   - Update Pydantic models for API requests/responses
   - Ensure validation rules are appropriate

5. **Update Documentation**
   - Document the model changes in the appropriate files

## Current Implementation Focus

The implementation plan has been revised to prioritize core service workflows before extensive testing. The key areas of focus are:

1. **Planning System Enhancement**
   - High-level planning capabilities have been implemented
   - The service has been refactored into smaller, more manageable modules
   - Template-based planning, methodology-driven planning, and AI-assisted plan generation are now available
   - Timeline forecasting and bottleneck analysis have been implemented
   - See [Planning System Enhancement Plan](developer-guides/service-development/planning-system-enhancement-plan.md) and [Planning System High-Level Capabilities Implementation](developer-guides/service-development/planning-system-high-level-capabilities-implementation.md) for details

2. **Agent Generation Engine Enhancement**
   - See [Agent Generation Engine Enhancement Plan](developer-guides/service-development/agent-generation-engine-enhancement-plan.md) for details

3. **Project Dashboard Enhancement**
   - Implementing additional dashboard widgets
   - Adding customizable dashboard layout

4. **Documentation Maintenance**
   - Implementing the Documentation Maintenance Plan
   - Consolidating migration implementation documents

## Key Project Areas

### 1. Agent Communication Hub

The Agent Communication Hub facilitates communication between agents with advanced capabilities:

- **Enhanced Routing**: Topic-based, content-based, and rule-based routing
- **Priority Queue System**: Message prioritization with fairness mechanisms
- **Advanced Communication Patterns**: Publish-subscribe, request-reply, and broadcast messaging
- **Monitoring and Analytics**: Message flow tracking and performance metrics

See the comprehensive [Agent Communication Hub Guide](developer-guides/service-development/agent-communication-hub-guide.md) for details.

### 2. Service Boundaries

Understanding service boundaries is essential for effective development:

- **Web Dashboard → Project Coordinator**: Uses `WebToCoordinatorAdapter`
- **Project Coordinator → Agent Orchestrator**: Uses `CoordinatorToAgentAdapter`
- **Agent Orchestrator → Model Orchestration**: Uses `AgentToModelAdapter`
- **Planning System → Agent Orchestrator**: Uses `PlanningToAgentAdapter`

Each boundary has specific transformation rules documented in [Entity Representation Alignment](docs/developer-guides/service-development/entity-representation-alignment.md).

### 3. Planning System

The Planning System has been enhanced with high-level planning capabilities:

- **Planning Strategist**: Generates strategic plans using templates and methodologies
- **Planning Tactician**: Breaks down plans into executable tasks
- **Project Forecaster**: Predicts timelines and identifies bottlenecks

The service has been refactored into smaller, more manageable modules following the Single Responsibility Principle:

```
services/planning-system/src/services/
├── strategic_planning_service.py  # Main service facade
├── plan_template_service.py       # Template management
├── planning_methodology_service.py # Methodology management
├── strategic_planning/            # Specialized planning services
│   ├── __init__.py
│   ├── helper_service.py          # Common helper methods
│   ├── plan_creation_service.py   # Plan creation methods
│   ├── plan_generation_service.py # AI-assisted plan generation
│   ├── plan_optimization_service.py # Plan optimization
│   ├── plan_forecasting_service.py # Timeline forecasting and bottleneck analysis
│   └── methodology_application_service.py # Methodology application
```

See [Planning System High-Level Capabilities Implementation](developer-guides/service-development/planning-system-high-level-capabilities-implementation.md) for details.

## Best Practices for Claude Agents

### 1. Cross-Service Communication

- Use standardized error handling patterns
- Implement retry mechanisms for transient failures
- Add fallback mechanisms for service unavailability
- Validate all input at service boundaries using cross-service validation utilities

See [Error Handling Best Practices](docs/developer-guides/service-development/error-handling-best-practices.md) and [Cross-Service Validation Guide](docs/developer-guides/service-development/cross-service-validation-guide.md) for details.

### 2. Documentation Updates

- Update relevant documentation files
- Use the draft-of-thought approach
- Add troubleshooting notes for any complex issues

### 3. Error Handling

- Use appropriate exception types
- Provide detailed error messages
- Log errors with context
- Document common errors and solutions

### 4. Testing

- Unit tests for individual components
- Integration tests for cross-service flows
- Test boundary transformations
- Test error handling

## Common Pitfalls

1. **SQLAlchemy Reserved Names**
   - Never use `metadata` as a column name
   - Use entity-specific prefixes for metadata columns (e.g., `project_metadata`)

2. **Table Naming Conventions**
   - Use singular table names throughout the project
   - Be consistent with foreign key references

3. **Enum Handling**
   - Use string columns with validation in SQLAlchemy models
   - Use Enum classes in Pydantic models
   - Always use uppercase values for enum strings (e.g., "PLANNING" not "planning")
   - Define all enums in `shared/models/src/enums.py` for consistency

4. **Service Boundary Transformations**
   - Be aware of field name differences between services
   - Handle metadata fields appropriately
   - Validate input before transformation

5. **Model Mismatches Between Services**
   - Web Dashboard might include fields not expected by Project Coordinator
   - Different services might have different validation rules for the same fields
   - Pay attention to optional vs. required fields across service boundaries

## Troubleshooting Resources

If you encounter issues, consult these resources:

- [Troubleshooting Guide](docs/developer-guides/service-development/troubleshooting-guide.md)
- [Service Startup Troubleshooting Guide](docs/developer-guides/service-development/service-startup-troubleshooting.md)
- [Model Standardization History](docs/developer-guides/service-development/model-standardization-history.md)
- [Entity Representation Alignment](docs/developer-guides/service-development/entity-representation-alignment.md)

## Collaboration Guidelines

When working as part of a team of Claude agents:

1. **Maintain Consistent Mental Models**
   - Use the draft-of-thought documentation to ensure all agents have the same understanding
   - Document key insights and decisions

2. **Divide Work by Service Boundaries**
   - Assign different services to different agents
   - Coordinate at service boundaries

3. **Document Cross-Service Changes**
   - Clearly document changes that affect multiple services
   - Update adapter documentation when changing entity representations

4. **Share Troubleshooting Insights**
   - Document solutions to complex problems
   - Update the troubleshooting guide with new issues and solutions
