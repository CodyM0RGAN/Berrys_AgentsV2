# Entity Representation Alignment (Phase 6)

This document outlines the plan for Phase 6 of the Model Standardization project, focusing on aligning entity representations across different services.

## Overview

Different services may represent the same entity in different ways, with variations in field names, types, and semantics. This phase aims to document these differences and implement adapters to ensure consistent data transformation when entities cross service boundaries.

## Related Documentation

- [Model Standardization Progress](./model-standardization-progress.md) - Overall progress on model standardization
- [Model Standardization History](./model-standardization-history.md) - Historical context and lessons learned
- [Model Mapping System](./model-mapping-system.md) - Details on the model mapping system
- [Adapter Usage Examples](./adapter-usage-examples.md) - Examples of how to use the adapters
- [SQLAlchemy Guide](../../best-practices/sqlalchemy-guide.md) - Best practices for SQLAlchemy models

## Goals

1. Document entity differences across services
2. Define transformation logic for each entity type
3. Implement service boundary adapters
4. Add integration tests to verify correct transformation

## Current Status

- ✅ Initial entity mapping documentation created
- ✅ Transformation approach defined
- ✅ Implementation of adapters completed
- ✅ Integration tests implemented
- ✅ Usage patterns documented
- 🔄 Ongoing maintenance and issue resolution (March 2025)
- 🔄 Cross-Service Communication Improvements (March 2025)

## Entity Mapping Documentation

### Project Entity

| Field | Web Dashboard | Project Coordinator | Agent Orchestrator | Model Orchestration |
|-------|--------------|---------------------|-------------------|---------------------|
| ID | `id` (UUID) | `id` (UUID) | `project_id` (UUID) | `project_id` (UUID) |
| Name | `name` (String) | `name` (String) | `name` (String) | `name` (String) |
| Description | `description` (Text) | `description` (Text) | `description` (Text) | N/A |
| Status | `status` (String) | `status` (Enum) | `status` (String) | `status` (String) |
| Owner | `owner_id` (UUID) | `owner_id` (UUID) | `created_by` (UUID) | N/A |
| Metadata | `project_metadata` (JSONB) | `project_metadata` (JSONB) | `metadata` (JSON) | `config` (JSON) |

**Note**: There's a mismatch in the API models for project creation. The Web Dashboard's `ProjectCoordinatorClient.create_project()` method sends a `status` field, but the Project Coordinator's `ProjectCreateRequest` model doesn't expect this field during creation. This causes 500 errors when creating projects via chat. See the [Known Issues and Workarounds](#known-issues-and-workarounds) section for details.

### Agent Entity

| Field | Web Dashboard | Project Coordinator | Agent Orchestrator | Model Orchestration |
|-------|--------------|---------------------|-------------------|---------------------|
| ID | `id` (UUID) | `id` (UUID) | `id` (UUID) | `agent_id` (UUID) |
| Name | `name` (String) | `name` (String) | `name` (String) | `name` (String) |
| Type | `type` (String) | `type` (String) | `agent_type` (Enum) | `type` (String) |
| Status | `status` (String) | `status` (String) | `status` (Enum) | `status` (String) |
| Project | `project_id` (UUID) | `project_id` (UUID) | `project_id` (UUID) | `project_id` (UUID) |
| Metadata | `agent_metadata` (JSONB) | `agent_metadata` (JSONB) | `config` (JSON) | `settings` (JSON) |

### Task Entity

| Field | Web Dashboard | Project Coordinator | Agent Orchestrator | Model Orchestration |
|-------|--------------|---------------------|-------------------|---------------------|
| ID | `id` (UUID) | `id` (UUID) | `task_id` (UUID) | N/A |
| Name | `name` (String) | `name` (String) | `name` (String) | N/A |
| Description | `description` (Text) | `description` (Text) | `description` (Text) | N/A |
| Status | `status` (String) | `status` (String) | `status` (Enum) | N/A |
| Priority | `priority` (Integer) | `priority` (Integer) | `priority` (Enum) | N/A |
| Assigned To | `assigned_to` (UUID) | `agent_id` (UUID) | `assigned_agent_id` (UUID) | N/A |
| Project | `project_id` (UUID) | `project_id` (UUID) | `project_id` (UUID) | N/A |
| Metadata | `task_metadata` (JSONB) | `task_metadata` (JSONB) | `metadata` (JSON) | N/A |

## Transformation Logic

### Project Transformation

```python
def web_to_coordinator_project(web_project):
    """Transform a web dashboard project to a project coordinator project."""
    return {
        "id": web_project.id,
        "name": web_project.name,
        "description": web_project.description,
        "status": web_project.status,
        "owner_id": web_project.owner_id,
        "project_metadata": web_project.project_metadata
    }

def coordinator_to_agent_project(coordinator_project):
    """Transform a project coordinator project to an agent orchestrator project."""
    return {
        "project_id": coordinator_project.id,
        "name": coordinator_project.name,
        "description": coordinator_project.description,
        "status": coordinator_project.status,
        "created_by": coordinator_project.owner_id,
        "metadata": coordinator_project.project_metadata
    }
```

### Agent Transformation

```python
def web_to_coordinator_agent(web_agent):
    """Transform a web dashboard agent to a project coordinator agent."""
    return {
        "id": web_agent.id,
        "name": web_agent.name,
        "type": web_agent.type,
        "status": web_agent.status,
        "project_id": web_agent.project_id,
        "agent_metadata": web_agent.agent_metadata
    }

def coordinator_to_agent_orchestrator_agent(coordinator_agent):
    """Transform a project coordinator agent to an agent orchestrator agent."""
    return {
        "id": coordinator_agent.id,
        "name": coordinator_agent.name,
        "agent_type": coordinator_agent.type,
        "status": coordinator_agent.status,
        "project_id": coordinator_agent.project_id,
        "config": coordinator_agent.agent_metadata
    }
```

## Service Boundary Adapters

### WebToCoordinator Adapter

```python
class WebToCoordinatorAdapter:
    """Adapter for converting between Web Dashboard and Project Coordinator models."""
    
    @staticmethod
    def project_to_coordinator(web_project):
        """Convert a Web Dashboard project to a Project Coordinator project."""
        return web_to_coordinator_project(web_project)
    
    @staticmethod
    def project_from_coordinator(coordinator_project):
        """Convert a Project Coordinator project to a Web Dashboard project."""
        # Implement reverse transformation
        pass
    
    @staticmethod
    def project_create_request_to_coordinator(web_request):
        """Convert a Web Dashboard project create request to a Project Coordinator request."""
        # Create a copy of the request data
        coordinator_request = web_request.copy()
        
        # Remove fields not expected by Project Coordinator
        if 'status' in coordinator_request:
            # Status field is not expected in ProjectCreateRequest
            del coordinator_request['status']
            
        return coordinator_request
    
    @staticmethod
    def agent_to_coordinator(web_agent):
        """Convert a Web Dashboard agent to a Project Coordinator agent."""
        return web_to_coordinator_agent(web_agent)
    
    @staticmethod
    def agent_from_coordinator(coordinator_agent):
        """Convert a Project Coordinator agent to a Web Dashboard agent."""
        # Implement reverse transformation
        pass
```

### CoordinatorToAgent Adapter

```python
class CoordinatorToAgentAdapter:
    """Adapter for converting between Project Coordinator and Agent Orchestrator models."""
    
    @staticmethod
    def project_to_agent(coordinator_project):
        """Convert a Project Coordinator project to an Agent Orchestrator project."""
        return coordinator_to_agent_project(coordinator_project)
    
    @staticmethod
    def project_from_agent(agent_project):
        """Convert an Agent Orchestrator project to a Project Coordinator project."""
        # Implement reverse transformation
        pass
    
    @staticmethod
    def agent_to_agent_orchestrator(coordinator_agent):
        """Convert a Project Coordinator agent to an Agent Orchestrator agent."""
        return coordinator_to_agent_orchestrator_agent(coordinator_agent)
    
    @staticmethod
    def agent_from_agent_orchestrator(agent_orchestrator_agent):
        """Convert an Agent Orchestrator agent to a Project Coordinator agent."""
        # Implement reverse transformation
        pass
```

## Integration Tests

### Project Transformation Tests

```python
def test_project_web_to_coordinator():
    """Test transforming a web dashboard project to a project coordinator project."""
    web_project = WebProject(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project",
        status="draft",
        owner_id=uuid.uuid4(),
        project_metadata={"key": "value"}
    )
    
    coordinator_project = WebToCoordinatorAdapter.project_to_coordinator(web_project)
    
    assert coordinator_project.id == web_project.id
    assert coordinator_project.name == web_project.name
    assert coordinator_project.description == web_project.description
    assert coordinator_project.status == web_project.status
    assert coordinator_project.owner_id == web_project.owner_id
    assert coordinator_project.project_metadata == web_project.project_metadata
```

## Implementation Plan

1. **Week 1: Documentation and Analysis**
   - Complete entity mapping documentation for all entities
   - Identify critical transformation requirements
   - Define adapter interfaces

2. **Week 2: Transformation Logic**
   - Implement transformation functions for each entity type
   - Create unit tests for transformation functions
   - Document edge cases and special handling

3. **Week 3: Service Boundary Adapters**
   - Implement adapter classes for each service boundary
   - Integrate adapters with service communication
   - Add logging and error handling

4. **Week 4: Testing and Verification**
   - Create integration tests for cross-service workflows
   - Verify data consistency across service boundaries
   - Document adapter usage patterns

## Current Model Mismatches

As part of the Cross-Service Communication Improvements initiative, we've identified several model mismatches between services that need to be addressed:

| Service Boundary | Entity | Issue | Impact | Status |
|------------------|--------|-------|--------|--------|
| Web Dashboard → Project Coordinator | Project | Status field in ProjectCreateRequest | 500 errors when creating projects via chat | ❌ Not Resolved |
| Project Coordinator → Agent Orchestrator | Project | Metadata field handling | Inconsistent metadata representation | ❌ Not Resolved |
| Agent Orchestrator → Model Orchestration | Agent | Agent capability representation | Capabilities not properly transferred | ❌ Not Resolved |
| Planning System → Agent Orchestrator | Task | Task structure differences | Task assignments may fail | ✅ Resolved |

### Web Dashboard → Project Coordinator

The Web Dashboard sends a `status` field in the `ProjectCreateRequest`, but the Project Coordinator doesn't expect this field during creation.

### Project Coordinator → Agent Orchestrator

The Project Coordinator uses `project_metadata` while the Agent Orchestrator uses `metadata`, leading to potential data loss during conversion.

### Agent Orchestrator → Model Orchestration

The Agent Orchestrator represents agent capabilities using the `AgentType` enum, which is mapped to a list of `ModelCapability` enums in Model Orchestration. The `AgentToModelAdapter` now transforms the `AgentType` to the corresponding `ModelCapability` list and adds detailed capability configuration for each capability type.

The adapter uses two mapping dictionaries:
1. `AGENT_TYPE_TO_CAPABILITY_MAP`: Maps each `AgentType` to a list of appropriate `ModelCapability` values
2. `CAPABILITY_CONFIG_MAP`: Maps each `ModelCapability` to its default configuration parameters

This ensures that the Model Orchestration service has all the information it needs to process requests correctly, including capability-specific parameters like token limits, temperature settings, and other model-specific configurations.

### Planning System → Agent Orchestrator

The Planning System and Agent Orchestrator have different task structures, particularly in how they represent task assignments and priorities.

The `PlanningToAgentAdapter` has been enhanced to handle the `assigned_to` field from the Planning System, mapping it to the `assigned_agent_id` field in the Agent Orchestrator's task representation. This ensures that task assignments are correctly propagated between the two services.

The adapter now includes the following logic:

```python
# Handle field name changes
if "id" in data:
    result["task_id"] = data["id"]
if "plan_id" in data:
    result["project_id"] = data["plan_id"] # Assuming plan_id in PlanningSystem corresponds to project_id in AgentOrchestrator
if "assigned_to" in data:
    result["assigned_agent_id"] = data["assigned_to"]
```

This implementation ensures that task assignments are correctly propagated between the Planning System and Agent Orchestrator services, preventing task assignment failures.

## Known Issues and Workarounds

### Project Creation Status Field Mismatch

**Issue**: When creating a project via the chat interface, the system returns a 500 Server Error.

**Root Cause**: There's a model mismatch between the Web Dashboard and Project Coordinator services:
- The Web Dashboard's `ProjectCoordinatorClient.create_project()` method in `services/web-dashboard/app/api/project_coordinator.py` sends a `status` field with default value 'PLANNING'
- The Project Coordinator's `ProjectCreateRequest` model in `services/project-coordinator/src/models/api.py` doesn't expect a `status` field during creation

**Workarounds**:

1. **Modify ProjectCreateRequest in Project Coordinator**:
   ```python
   class ProjectCreateRequest(BaseModel):
       """Request model for creating a new project."""
       name: str
       description: Optional[str] = None
       owner_id: Optional[UUID] = None
       status: Optional[ProjectStatus] = None  # Add this field
       metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
   ```

2. **Update Web Dashboard client to not send status**:
   ```python
   def create_project(
       self, 
       name: str, 
       description: str,
       metadata: Optional[Dict[str, Any]] = None
   ) -> Dict[str, Any]:
       """
       Create a new project.
       
       Args:
           name: Project name
           description: Project description
           metadata: Additional metadata
           
       Returns:
           Created project details
       """
       data = {
           'name': name,
           'description': description
       }
       
       if metadata:
           data['metadata'] = metadata
       
       return self.post('/projects', data=data)
   ```

3. **Use the WebToCoordinatorAdapter to handle the field mismatch**:
   ```python
   # In the chat route handler
   project_data = {
       'name': project_name,
       'description': project_description,
       'status': 'PLANNING'  # This would cause an error
   }
   
   # Use the adapter to transform the request
   coordinator_data = WebToCoordinatorAdapter.project_create_request_to_coordinator(project_data)
   
   # Now send the transformed data to the Project Coordinator
   project = project_coordinator_client.post('/projects', data=coordinator_data)
   ```

### Metadata Field Handling Mismatch

**Issue**: Metadata fields are inconsistently handled between Project Coordinator and Agent Orchestrator.

**Root Cause**: The Project Coordinator uses `project_metadata` while the Agent Orchestrator uses `metadata`, leading to potential data loss during conversion.

**Workarounds**:

1. **Update CoordinatorToAgentAdapter to handle metadata properly**:
   ```python
   @staticmethod
   def project_to_agent(coordinator_project):
       """Convert a Project Coordinator project to an Agent Orchestrator project."""
       result = coordinator_to_agent_project(coordinator_project)
       
       # Ensure metadata is properly transferred
       if hasattr(coordinator_project, 'project_metadata') and coordinator_project.project_metadata:
           result['metadata'] = coordinator_project.project_metadata
       
       return result
   ```

### Agent Capability Representation Mismatch

**Issue**: Agent capabilities are not properly transferred between Agent Orchestrator and Model Orchestration.

**Root Cause**: The Agent Orchestrator represents agent capabilities using the `AgentType` enum, while Model Orchestration expects a list of `ModelCapability` enums.

**Solution**:

1. **Update AgentToModelAdapter to transform capabilities**:
   The `AgentToModelAdapter` now maps the `AgentType` to the corresponding `ModelCapability` list using the `AGENT_TYPE_TO_CAPABILITY_MAP`.
   
   The `agent_to_model` method now includes the following logic:
   ```python
        if "type" in data:
            agent_type = get_enum_from_value(AgentType, data["type"])
            result["type"] = normalize_enum_value(data["type"], uppercase=True)

            # Map AgentType to ModelCapability
            if agent_type and agent_type in AGENT_TYPE_TO_CAPABILITY_MAP:
                result["capabilities"] = [capability.value for capability in AGENT_TYPE_TO_CAPABILITY_MAP[agent_type]]
            else:
                result["capabilities"] = []
   ```
   
   This ensures that the agent's capabilities are properly transferred to Model Orchestration.
   
   The `AGENT_TYPE_TO_CAPABILITY_MAP` is defined as follows:
   ```python
   AGENT_TYPE_TO_CAPABILITY_MAP = {
        AgentType.COORDINATOR: [ModelCapability.CHAT, ModelCapability.COMPLETION],
        AgentType.ASSISTANT: [ModelCapability.CHAT, ModelCapability.COMPLETION],
        AgentType.RESEARCHER: [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.EMBEDDING],
        AgentType.DEVELOPER: [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.CODE_GENERATION],
        AgentType.DESIGNER: [ModelCapability.IMAGE_GENERATION],
        AgentType.SPECIALIST: [ModelCapability.CHAT, ModelCapability.COMPLETION],
        AgentType.AUDITOR: [ModelCapability.CHAT, ModelCapability.COMPLETION],
        AgentType.CUSTOM: [ModelCapability.CHAT, ModelCapability.COMPLETION],
    }
   ```

## Next Steps

Phase 7 (Model Conversion Layer Standardization) has been completed, which focused on creating a standard conversion interface for all entities. The next steps are:

1. **Cross-Service Communication Improvements**
   - Resolve identified model mismatches
   - Enhance error handling in adapters
   - Implement fallback mechanisms
   - Improve validation for cross-service requests
   - See [Cross-Service Communication Improvements](cross-service-communication-improvements.md) for details

2. **Phase 8: Testing and Verification**
   - Create database migration tests
   - Add model unit tests
   - Create integration tests
   - Performance testing

3. **Phase 9: Documentation and Best Practices**
   - Update schema documentation
   - Create model style guide
   - Create linting/validation tools
   - Document lessons learned

4. **Ongoing Maintenance**
   - Address issues like the project creation status field mismatch
   - Improve error handling in adapters
   - Add more comprehensive validation
