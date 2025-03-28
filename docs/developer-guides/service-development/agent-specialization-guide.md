# Agent Specialization Guide

This guide explains the agent specialization feature in the MAS Framework, which allows for dynamic configuration of agent specializations based on their types.

## Overview

Agent specializations define the skills, responsibilities, knowledge domains, and collaboration patterns for different types of agents. This information is used by the requirement analysis service to determine the most appropriate agent specializations for a given project.

The agent specialization feature includes:

1. Database tables to store agent specializations
2. API endpoints to manage agent specializations
3. Integration with the requirement analysis service

## Database Schema

The agent specialization feature uses two database tables:

### agent_specialization

This table stores the basic information about agent specializations:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_type | VARCHAR(50) | Agent type (e.g., COORDINATOR, DEVELOPER) |
| required_skills | JSONB | Array of skills required for this agent type |
| responsibilities | JSONB | Array of responsibilities for this agent type |
| knowledge_domains | JSONB | Array of knowledge domains for this agent type |
| specialization_metadata | JSONB | Additional metadata (optional) |
| created_at | TIMESTAMP WITH TIME ZONE | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | Last update timestamp |

### agent_collaboration_pattern

This table stores the collaboration patterns for agent specializations:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| agent_specialization_id | UUID | Foreign key to agent_specialization |
| collaborator_type | VARCHAR(50) | Type of agent to collaborate with |
| interaction_type | VARCHAR(50) | Type of interaction (e.g., ASSIGN_TASK, PROVIDE_INFORMATION) |
| description | TEXT | Description of the collaboration |
| pattern_metadata | JSONB | Additional metadata (optional) |
| created_at | TIMESTAMP WITH TIME ZONE | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | Last update timestamp |

## API Endpoints

The agent specialization feature provides the following API endpoints:

### List Agent Specializations

```
GET /api/specializations
```

Returns a list of all agent specializations.

### Get Agent Specialization

```
GET /api/specializations/{agent_type}
```

Returns the agent specialization for the specified agent type.

### Create Agent Specialization

```
POST /api/specializations
```

Creates a new agent specialization. Requires admin privileges.

Example request body:

```json
{
  "agent_type": "DEVELOPER",
  "required_skills": ["Programming", "Software Design", "Testing"],
  "responsibilities": ["Implement features", "Fix bugs", "Write tests"],
  "knowledge_domains": ["Software Development", "Programming Languages"],
  "collaboration_patterns": [
    {
      "collaborator_type": "DESIGNER",
      "interaction_type": "REQUEST_INFORMATION",
      "description": "Request design specifications"
    }
  ]
}
```

### Update Agent Specialization

```
PUT /api/specializations/{agent_type}
```

Updates an existing agent specialization. Requires admin privileges.

### Delete Agent Specialization

```
DELETE /api/specializations/{agent_type}
```

Deletes an agent specialization. Requires admin privileges.

## Integration with Requirement Analysis

The agent specialization feature is integrated with the requirement analysis service. When analyzing project requirements, the service retrieves agent specializations from the database instead of using hardcoded defaults.

The `RequirementAnalysisService` uses the `AgentSpecializationService` to retrieve agent specializations from the database. If a specialization is not found for a particular agent type, a default specialization is used.

## Setup and Migration

To set up the agent specialization feature, you need to apply the database migration script:

### Windows

```powershell
# From the project root directory
.\scripts\apply_agent_specialization_migration.ps1
```

### Linux/macOS

```bash
# From the project root directory
./scripts/apply_agent_specialization_migration.sh
```

The migration script creates the necessary database tables and populates them with default agent specializations.

## Usage Example

Here's an example of how to use the agent specialization feature in your code:

```python
from shared.models.src.enums import AgentType
from services.agent_orchestrator.src.services.agent_specialization_service import AgentSpecializationService

async def get_developer_specialization(db, event_bus, command_bus, settings):
    # Create agent specialization service
    specialization_service = AgentSpecializationService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    # Get developer specialization
    developer_specialization = await specialization_service.get_agent_specialization(
        agent_type=AgentType.DEVELOPER,
    )
    
    # Use the specialization
    required_skills = developer_specialization.required_skills
    responsibilities = developer_specialization.responsibilities
    knowledge_domains = developer_specialization.knowledge_domains
    collaboration_patterns = developer_specialization.collaboration_patterns
    
    return developer_specialization
```

## Customizing Agent Specializations

You can customize agent specializations through the API endpoints or by modifying the migration script. If you modify the migration script, you'll need to reapply it to update the database.

## Troubleshooting

If you encounter issues with the agent specialization feature, check the following:

1. Make sure the database migration has been applied successfully
2. Check the database connection settings in the `.env` file
3. Verify that the agent specialization tables exist in the database
4. Check the logs for any error messages related to agent specializations

## Future Enhancements

Planned enhancements for the agent specialization feature include:

1. Support for versioning of agent specializations
2. Integration with the agent template system
3. Machine learning-based optimization of agent specializations
4. Enhanced visualization of agent collaboration patterns
