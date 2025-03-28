# Web Dashboard Workflows

**Status**: Current  
**Last Updated**: March 27, 2025  
**Categories**: development, web-dashboard  
**Services**: web-dashboard, project-coordinator, planning-system  
**Priority**: High  

> **Navigation**: [Root](/docs) > [Developer Guides](/docs/developer-guides) > [Service Development](/docs/developer-guides/service-development) > Web Dashboard Workflows

This document describes the workflows for submitting, initiating, planning, and deploying projects in the Berry's Agents Web Dashboard. These workflows are critical for enabling the core service interactions in the Berrys_AgentsV2 framework.

## Table of Contents

- [Overview](#overview)
- [Workflow Descriptions](#workflow-descriptions)
  - [Submission Workflow](#submission-workflow)
  - [Initiation Workflow](#initiation-workflow)
  - [Planning Workflow](#planning-workflow)
  - [Deployment Workflow](#deployment-workflow)
- [Implementation Details](#implementation-details)
- [Integration Points](#integration-points)
- [Related Documents](#related-documents)

## Overview

The Web Dashboard provides a user interface for interacting with the Berry's Agents framework. It enables users to submit project requests, initiate projects, create and manage project plans, and deploy projects. These workflows are implemented through a set of routes and templates in the Web Dashboard, which communicate with the Project Coordinator and Planning System services.

## Workflow Descriptions

### Submission Workflow

The submission workflow allows users to submit new project requests through the Web Dashboard.

1. User navigates to the "Projects" page and clicks "New Project"
2. User fills out the project request form, including:
   - Project Name
   - Description
   - Project Type
   - Goals
   - Constraints
   - Requirements
3. User submits the form
4. Web Dashboard sends a request to the Project Coordinator service to create a new project
5. Project Coordinator creates the project and returns the project details
6. Web Dashboard displays the project details to the user

### Initiation Workflow

The initiation workflow allows users to initiate a project, which starts the process of creating and assigning agents.

1. User navigates to the project detail page
2. User clicks the "Initiate" button
3. Web Dashboard sends a request to the Project Coordinator service to update the project status to "In Progress"
4. Project Coordinator updates the project status and triggers the creation of a strategic plan
5. Planning System creates a strategic plan for the project
6. Agent Orchestrator creates and assigns agents based on the project requirements
7. Web Dashboard displays the updated project status and agent details to the user

### Planning Workflow

The planning workflow allows users to create and manage project plans, tasks, and dependencies.

1. User navigates to the project detail page and clicks "Create Plan" or to the "Plans" page and clicks "New Plan"
2. User fills out the plan form, including:
   - Plan Name
   - Description
   - Project (if not already selected)
   - Status
   - Project Type
   - Goals
   - Constraints
3. User submits the form
4. Web Dashboard sends a request to the Planning System service to create a new plan
5. Planning System creates the plan and returns the plan details
6. Web Dashboard displays the plan details to the user
7. User can then:
   - Add tasks to the plan
   - Define dependencies between tasks
   - Generate timeline forecasts
   - Analyze bottlenecks
   - View the critical path

### Deployment Workflow

The deployment workflow allows users to deploy a project, which makes it available for use.

1. User navigates to the project detail page
2. User clicks the "Deploy" button
3. Web Dashboard sends a request to the Project Coordinator service to update the project status to "Deployed"
4. Project Coordinator updates the project status and triggers the deployment process
5. Web Dashboard displays the updated project status to the user

## Implementation Details

The workflows are implemented through a set of routes and templates in the Web Dashboard:

- **Routes**:
  - `projects.py`: Handles project-related routes, including project submission, initiation, and deployment
  - `plans.py`: Handles plan-related routes, including plan creation, task management, and forecasting

- **Templates**:
  - `new_project_request.html`: Form for submitting project requests
  - `detail.html`: Project detail page with buttons for initiating and deploying projects
  - `plan.html`: Plan detail page with sections for tasks, timeline forecasts, and bottleneck analysis
  - `new_plan.html`: Form for creating new plans
  - `edit_plan.html`: Form for editing plans
  - `plans_list.html`: List of all plans
  - `task_form.html`: Form for creating and editing tasks

## Integration Points

### Project Coordinator Integration

- **Project Creation**: Web Dashboard sends project details to the Project Coordinator service
- **Project Initiation**: Web Dashboard sends a request to update the project status to "In Progress"
- **Project Deployment**: Web Dashboard sends a request to update the project status to "Deployed"

### Planning System Integration

- **Plan Creation**: Web Dashboard sends plan details to the Planning System service
- **Task Management**: Web Dashboard sends task details to the Planning System service
- **Forecasting**: Web Dashboard requests timeline forecasts from the Planning System service
- **Bottleneck Analysis**: Web Dashboard requests bottleneck analysis from the Planning System service

### Agent Orchestrator Integration

- **Agent Creation**: Project Coordinator triggers agent creation through the Agent Orchestrator service
- **Agent Assignment**: Planning System assigns tasks to agents through the Agent Orchestrator service

## Related Documents

### Prerequisites
- [Web Dashboard Implementation Guide](/services/web-dashboard/IMPLEMENTATION.md) - Technical details about the Web Dashboard implementation
- [Planning System Enhancement Plan](/docs/developer-guides/service-development/planning-system-enhancement-plan.md) - Plan for enhancing the Planning System
- [Agent Generation Engine Enhancement Plan](/docs/developer-guides/service-development/agent-generation-engine-enhancement-plan.md) - Plan for enhancing the Agent Generation Engine

### Reference
- [Project Coordinator API Reference](/docs/reference/api.md#project-coordinator) - API reference for the Project Coordinator service
- [Planning System API Reference](/docs/reference/api.md#planning-system) - API reference for the Planning System service
- [Agent Orchestrator API Reference](/docs/reference/api.md#agent-orchestrator) - API reference for the Agent Orchestrator service
