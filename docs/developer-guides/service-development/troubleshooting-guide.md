# Comprehensive Troubleshooting Guide

**Status**: Current  
**Last Updated**: March 27, 2025  
**Categories**: troubleshooting, development, reference  
**Services**: all  
**Priority**: High  

> **Navigation**: [Root](/docs) > [Developer Guides](/docs/developer-guides) > [Service Development](/docs/developer-guides/service-development) > Comprehensive Troubleshooting Guide

This guide provides strategies and solutions for troubleshooting issues in the Berrys_AgentsV2 system. It focuses on general issues that may occur during development and operation, while service startup-specific issues are covered in the [Service Startup Troubleshooting Guide](./service-startup-troubleshooting.md).

## Table of Contents

1. [Quick Reference: Common Error Messages](#quick-reference-common-error-messages)
2. [Code and Development Issues](#code-and-development-issues)
   - [Import Errors](#import-errors)
   - [Variable Reference Errors](#variable-reference-errors)
3. [Database Issues](#database-issues)
   - [Table Naming and Foreign Key References](#table-naming-and-foreign-key-references)
   - [Reserved Column Names](#reserved-column-names)
   - [Missing Database Tables](#missing-database-tables)
   - [Inheritance Relationship Issues](#inheritance-relationship-issues)
   - [Async/Sync Database Driver Conflict](#asyncsync-database-driver-conflict)
4. [Docker Container Issues](#docker-container-issues)
   - [Missing Dependencies](#missing-dependencies)
   - [Changes Not Reflected in Running Containers](#changes-not-reflected-in-running-containers)
5. [Authentication Issues](#authentication-issues)
   - [Database Initialization](#database-initialization)
   - [Login Fails with "Invalid email or password"](#login-fails-with-invalid-email-or-password)
   - [User not found Error After Login](#user-not-found-error-after-login)
   - [CSRF Token Validation Failed](#csrf-token-validation-failed)
6. [API Integration Issues](#api-integration-issues)
   - [API Client Structure](#api-client-structure)
   - [Common API Issues](#common-api-issues)
7. [Cross-Service Communication Issues](#cross-service-communication-issues)
   - [Project Creation via Chat Fails with 500 Error](#project-creation-via-chat-fails-with-500-error)
   - [Enum Validation Warnings During Transition Period](#enum-validation-warnings-during-transition-period)
   - [Service Integration Workflow Issues](#service-integration-workflow-issues)
8. [Debugging Techniques](#debugging-techniques)
   - [Checking Service Health](#checking-service-health)
   - [Logging](#logging)
   - [Container Inspection](#container-inspection)
9. [Best Practices](#best-practices)
10. [Contributing to This Guide](#contributing-to-this-guide)

## Quick Reference: Common Error Messages

| Error Message | Category | Section Link | Brief Solution |
|---------------|----------|--------------|----------------|
| `ImportError: cannot import name X from Y` | Code | [Import Errors](#import-errors) | Add missing imports or correct import paths |
| `NameError: name 'X' is not defined` | Code | [Variable Reference Errors](#variable-reference-errors) | Ensure all variables are properly defined |
| `Foreign key associated with column X could not find table Y` | Database | [Table Naming and Foreign Key References](#table-naming-and-foreign-key-references) | Use correct table names in foreign key references |
| `AttributeError: 'MetaData' object has no attribute 'x'` | Database | [Reserved Column Names](#reserved-column-names) | Avoid using SQLAlchemy reserved names as column names |
| `relation "X" does not exist` | Database | [Missing Database Tables](#missing-database-tables) | Create and apply migrations for missing tables |
| `NoForeignKeysError: Can't find any foreign key relationships` | Database | [Inheritance Relationship Issues](#inheritance-relationship-issues) | Configure SQLAlchemy inheritance relationships correctly |
| `InvalidRequestError: The asyncio extension requires an async driver` | Database | [Async/Sync Database Driver Conflict](#asyncsync-database-driver-conflict) | Use the correct database driver for your SQLAlchemy mode |
| `executable file not found in $PATH` | Docker | [Missing Dependencies](#missing-dependencies) | Add missing dependencies to requirements.txt |
| `Invalid email or password` | Authentication | [Login Fails](#login-fails-with-invalid-email-or-password) | Check database initialization and user credentials |
| `User not found` | Authentication | [User not found Error](#user-not-found-error-after-login) | Fix user_loader function to correctly load users |
| `CSRF token validation failed` | Authentication | [CSRF Token Validation](#csrf-token-validation-failed) | Include CSRF token in all forms |
| `500 Server Error: Internal Server Error` | Cross-Service | [Project Creation via Chat](#project-creation-via-chat-fails-with-500-error) | Fix model mismatches between services |
| `DeprecationWarning: Lowercase enum value` | Cross-Service | [Enum Validation Warnings](#enum-validation-warnings-during-transition-period) | Use uppercase enum values |
| `WorkflowError: Service not found` | Cross-Service | [Service Integration Workflow Issues](#service-integration-workflow-issues) | Implement fallback mechanisms for service unavailability |

## Code and Development Issues

### Import Errors

#### Symptoms
- Error messages containing `ImportError: cannot import name X from Y`
- Service fails to start or crashes during operation
- Multiple cascading import errors after fixing the first one

#### Root Cause
- Missing or incorrect imports causing runtime errors
- Class or function not defined in the specified module
- Module structure changes without updating import statements

#### Solution
- Ensure all classes and functions used in a module are properly imported
- Pay special attention to imports when using complex class hierarchies
- When using type hints or class references, make sure the referenced classes are imported

#### Example
```python
# Missing import
from ..models.api import (
    BatchRegistrationResponse,
    # EvaluationRequest is missing but used in the code
)

# Fixed import
from ..models.api import (
    BatchRegistrationResponse,
    EvaluationRequest,  # Added the missing import
)
```

### Variable Reference Errors

#### Symptoms
- Error messages containing `NameError: name 'X' is not defined`
- Unexpected behavior in functions or methods
- Inconsistent errors that only occur in certain code paths

#### Root Cause
- Referencing undefined variables or using incorrect variable names
- Variable scope issues (e.g., trying to use a variable outside its scope)
- Typos in variable names

#### Solution
- Be careful with variable naming, especially when method parameters have similar names to local variables
- Use clear, distinct names for different variables
- Review code for any references to variables that might not be defined in all code paths

#### Example
```python
# Incorrect variable reference
def discover_tools(self, discovery_request):
    # ... code that processes discovery_request ...
    return DiscoveryResponse(
        request_id=discovery_id,
        discovered_tools=tool_summaries,
        discovery_timestamp=datetime.utcnow(),
        context=context,  # 'context' is not defined
    )

# Fixed variable reference
def discover_tools(self, discovery_request):
    # ... code that processes discovery_request ...
    return DiscoveryResponse(
        request_id=discovery_id,
        discovered_tools=tool_summaries,
        discovery_timestamp=datetime.utcnow(),
        context=discovery_request.context,  # Use the context from the request
    )
```

## Database Issues

### Table Naming and Foreign Key References

#### Symptoms
- Error messages about foreign key references not finding tables
- Database migration failures
- SQLAlchemy model initialization errors

#### Example Error
```
Foreign key associated with column 'agent_tools.agent_id' could not find table 'agents' with which to generate a foreign key to target column 'id'
```

#### Root Cause
Our `BaseModel` class uses a custom `__tablename__` method that converts CamelCase to snake_case and removes the "model" suffix, resulting in singular table names. However, in our foreign key references, we were using plural names.

#### Solution
- Ensure foreign key references match the actual table names generated by SQLAlchemy
- Be aware of how your BaseModel generates table names (e.g., singular vs. plural)
- When in doubt, explicitly set the `__tablename__` attribute

#### Example
```python
# Incorrect - Using plural name when the actual table name is singular
agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)

# Correct - Using the actual table name
agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id"), nullable=False)
```

### Reserved Column Names

#### Symptoms
- Cryptic error messages about missing attributes
- SQLAlchemy initialization failures
- Unexpected behavior in database operations

#### Example Error
```
AttributeError: 'MetaData' object has no attribute 'x'
```

#### Root Cause
SQLAlchemy uses certain names internally, such as `metadata`. When we tried to use these as column names, it caused conflicts.

#### Solution
- Avoid using SQLAlchemy reserved names like `metadata`, `query`, `session`, etc.
- Use domain-specific names for columns that might conflict with SQLAlchemy internals
- Follow the pattern of prefixing "metadata" with the entity name

#### Example
```python
# Problematic - Using a reserved name
class MyModel(BaseModel):
    metadata = Column(JSON, nullable=True)  # Conflicts with SQLAlchemy's metadata

# Fixed - Using a domain-specific name
class MyModel(BaseModel):
    content_metadata = Column(JSON, nullable=True)  # No conflict
```

#### Implementation
We've created SQL migration scripts to rename these columns in the database:

- `project.metadata` → `project.project_metadata`
- `tool.metadata` → `tool.tool_metadata`
- `chat_sessions.metadata` → `chat_sessions.session_metadata`
- `chat_messages.metadata` → `chat_messages.message_metadata`

### Missing Database Tables

#### Symptoms
- Error messages about relations not existing
- Database operation failures
- Application crashes when trying to access certain tables

#### Example Error
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "project_state" does not exist
LINE 1: INSERT INTO project_state (id, project_id, state, transition...
```

#### Root Cause
The database schema is missing tables that are referenced in the code. This can happen when:
1. New models are added to the codebase but the database hasn't been updated
2. The database initialization scripts are incomplete
3. The database migration hasn't been applied

#### Solution
1. Check if the table is defined in the SQLAlchemy models
2. Ensure the table is included in the database initialization script (`init.sql`)
3. Create and apply an Alembic migration to add the missing table
4. Update all database environments (dev, test, prod) with the new table

#### Example
```python
# Create an Alembic migration
alembic revision -m "add_missing_table"

# In the migration file
def upgrade():
    op.create_table(
        'project_state',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('transitioned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('transitioned_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('project_state')
```

### Inheritance Relationship Issues

#### Symptoms
- Error messages about missing foreign key relationships
- SQLAlchemy model initialization failures
- Unexpected behavior in polymorphic queries

#### Example Error
```
sqlalchemy.exc.NoForeignKeysError: Can't find any foreign key relationships between 'human_interaction' and 'approval_request'.
```

#### Root Cause
The issue was with how we were setting up the inheritance relationship. We were trying to use single-table inheritance but had some configuration issues.

#### Solution
Implement concrete table inheritance with explicit table names:

```python
class HumanInteractionModel(BaseModel):
    """Base class for all human interactions."""
    
    __tablename__ = 'human_interaction'
    
    # Discriminator column
    type = Column(String(50), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'HUMAN_INTERACTION'
    }
    
    # Common columns...


class ApprovalRequestModel(HumanInteractionModel):
    """Subclass for approval requests."""
    
    __tablename__ = 'approval_request'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    __mapper_args__ = {
        'polymorphic_identity': 'APPROVAL_REQUEST',
        'concrete': True
    }
    
    # Specific columns...
```

### Async/Sync Database Driver Conflict

#### Symptoms
- Error messages about async drivers
- Database connection failures
- Application crashes during startup

#### Example Error
```
sqlalchemy.exc.InvalidRequestError: The asyncio extension requires an async driver to be used. The loaded 'psycopg2' is not async.
```

#### Root Cause
The web-dashboard uses synchronous SQLAlchemy with Flask, but the shared utilities in the project use asynchronous SQLAlchemy. When the web-dashboard imports modules from the shared directory, it tries to create an async database engine but finds the synchronous `psycopg2` driver instead of the async `asyncpg` driver it expects.

#### Solution
Add asyncpg to requirements.txt and update the database connection string to use the async driver:

```
# Add to requirements.txt
asyncpg==0.29.0  # Required for async PostgreSQL connections
```

```yaml
# Update in docker-compose.yml
- SQLALCHEMY_DATABASE_URI=postgresql+asyncpg://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@postgres:5432/${DB_NAME:-mas_framework}
```

## Docker Container Issues

### Missing Dependencies

#### Symptoms
- Container fails to start with executable not found errors
- Application crashes with import errors
- Missing functionality in running containers

#### Example Error
```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: exec: "gunicorn": executable file not found in $PATH: unknown
```

#### Root Cause
The Dockerfile is configured to use Gunicorn as the WSGI server in the CMD instruction, but the gunicorn package was not included in the requirements.txt file.

#### Solution
- Add missing dependencies to requirements.txt
- Rebuild the container
- Start the service

#### Example
```
# Add to requirements.txt
gunicorn==21.2.0
```

```bash
# Rebuild and start the container
docker-compose build web-dashboard
docker-compose up web-dashboard
```

### Changes Not Reflected in Running Containers

#### Symptoms
- Code changes don't appear to have any effect
- Old behavior persists despite updates
- Logs show outdated code paths being executed

#### Root Cause
Docker containers are isolated environments. When you make changes to your code, those changes aren't automatically reflected in running containers unless you've mounted the code directory as a volume.

#### Solution
- Remember to rebuild containers after making code changes
- Use `docker-compose build <service-name>` to rebuild a specific service
- Use `docker-compose up --build` to rebuild all services

#### Example
```bash
# Rebuild a specific service
docker-compose build tool-integration

# Start the service with the new changes
docker-compose up tool-integration
```

## Authentication Issues

### Database Initialization

Before using the authentication system, you need to initialize the database with tables and default users:

```bash
# Navigate to the web-dashboard directory
cd services/web-dashboard

# Run the initialization script
python init_db.py
```

This script creates the necessary database tables and adds default users:
- Admin: admin@example.com / admin123
- User: user@example.com / user123

### Login Fails with "Invalid email or password"

#### Symptoms
- Users cannot log in even with correct credentials
- "Invalid email or password" error message
- No user session created after login attempt

#### Root Cause
1. Database tables not created
2. Default users not added to the database
3. Password hashing algorithm mismatch

#### Solution
1. Run the initialization script: `python init_db.py`
2. Check if users exist in the database: `flask shell` then `User.query.all()`
3. Verify password hashing in the User model matches the stored hashes

### "User not found" Error After Login

#### Symptoms
- User can log in but then gets redirected with a "User not found" error
- Session appears to be created but user data can't be loaded
- Intermittent authentication issues

#### Root Cause
The user_loader function in auth.py is not correctly loading the user from the session.

#### Solution
Ensure the user_loader function correctly converts the string ID to UUID and queries the database:

```python
@login_manager.user_loader
def load_user(user_id):
    try:
        uuid_obj = UUID(user_id)
        return User.query.get(uuid_obj)
    except (ValueError, TypeError):
        return None
```

### CSRF Token Validation Failed

#### Symptoms
- Form submissions fail with "CSRF token validation failed"
- POST requests rejected by the server
- 400 Bad Request errors

#### Root Cause
The CSRF protection is enabled but the form is missing the CSRF token.

#### Solution
Ensure all forms include the CSRF token:

```html
<form method="POST" action="{{ url_for('login') }}">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- Form fields -->
</form>
```

## API Integration Issues

### API Client Structure

The Web Dashboard integrates with backend services through API clients:

1. **BaseAPIClient**: Foundation class for all API clients
   - Handles HTTP requests, error handling, and response parsing
   - Implements retry logic and timeout handling

2. **Service-Specific Clients**:
   - **AgentOrchestratorClient**: Interacts with the Agent Orchestrator service
   - **ProjectCoordinatorClient**: Interacts with the Project Coordinator service
   - **ModelOrchestrationClient**: Interacts with the Model Orchestration service

### Common API Issues

#### Connection Errors

##### Symptoms
- Timeout errors
- Connection refused errors
- Network unreachable errors

##### Root Cause
- Backend service not running
- Incorrect API URL
- Network connectivity issues

##### Solution
- Check if the backend service is running
- Verify the API URL in the configuration
- Check network connectivity

#### Authentication Errors

##### Symptoms
- 401 Unauthorized errors
- 403 Forbidden errors
- Authentication token rejected

##### Root Cause
- Missing or invalid API keys or tokens
- Expired tokens
- Insufficient permissions

##### Solution
- Ensure API keys or tokens are properly configured
- Check if tokens have expired
- Verify user permissions

#### Timeout Errors

##### Symptoms
- Request timeout errors
- Long-running operations failing
- Inconsistent API responses

##### Root Cause
- Backend service overloaded
- Complex operations taking too long
- Network latency issues

##### Solution
- Increase the timeout value in the configuration
- Optimize backend service performance
- Implement asynchronous processing for long-running operations

## Cross-Service Communication Issues

### Project Creation via Chat Fails with 500 Error

#### Symptoms
- 500 Server Error when creating a project via chat
- Error message in logs about model validation
- Project not created despite successful form submission

#### Example Error
```
⚠️ Error creating project: 500 Server Error: Internal Server Error for url: http://project-coordinator:8000/projects/
```

#### Root Cause
There were two issues:
1. Model mismatch between the Web Dashboard and Project Coordinator services:
   - The Web Dashboard's `ProjectCoordinatorClient.create_project()` method in `services/web-dashboard/app/api/project_coordinator.py` sends a `status` field with default value 'PLANNING'
   - The Project Coordinator's `ProjectCreateRequest` model in `services/project-coordinator/src/models/api.py` doesn't expect a `status` field during creation

2. Case sensitivity in enum values:
   - The Web Dashboard was sending uppercase enum values (e.g., 'PLANNING')
   - The database constraints were expecting lowercase values (e.g., 'planning')

#### Solution
1. **Standardize enum values to uppercase**:
   - Update all enum values in `shared/models/src/enums.py` to use uppercase strings
   - Update database constraints to use uppercase values
   - Create a migration script to update existing data
   - Enhance enum validation to enforce uppercase values
   - See [Enum Standardization Guide](./enum_standardization.md) for details

2. **Modify ProjectCreateRequest in Project Coordinator**:
   ```python
   class ProjectCreateRequest(BaseModel):
       """Request model for creating a new project."""
       name: str
       description: Optional[str] = None
       owner_id: Optional[UUID] = None
       status: Optional[ProjectStatus] = None  # Add this field
       metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
   ```

3. **Update Web Dashboard client to not send status**:
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

4. **Implement adapter to handle the field mismatch**:
   ```python
   # In WebToCoordinatorAdapter
   @staticmethod
   def project_create_request_to_coordinator(web_request):
       """Convert a Web Dashboard project create request to a Project Coordinator request."""
       # Create a copy of the request data
       coordinator_request = web_request.copy()
       
       # Remove fields not expected by Project Coordinator
       if 'status' in coordinator_request:
           del coordinator_request['status']
           
       return coordinator_request
   ```

### Enum Validation Warnings During Transition Period

#### Symptoms
- Deprecation warnings about lowercase enum values
- Warnings in logs but functionality still works
- Inconsistent enum value casing across services

#### Example Warning
```
DeprecationWarning: Lowercase enum value 'draft' provided. Please use uppercase values ('DRAFT') for consistency. Support for lowercase values will be removed in a future version.
```

#### Root Cause
The `EnumValidator.validate_enum()` method in `shared/utils/src/enum_validation.py` has been updated to:
- Accept uppercase values as the standard
- Issue a deprecation warning when lowercase values are provided
- Automatically convert lowercase values to uppercase during the transition period

#### Solution
1. **Update code to use uppercase enum values**:
   ```python
   # Change this:
   project = Project(status="draft")
   
   # To this:
   project = Project(status="DRAFT")
   
   # Or better yet, use the enum directly:
   project = Project(status=ProjectStatus.DRAFT)
   ```

2. **If you can't update all code immediately**:
   - The warnings won't break functionality during the transition period
   - Lowercase values will be automatically converted to uppercase
   - Plan to update all code before the transition period ends

### Service Integration Workflow Issues

#### Symptoms
- Workflow failures when certain services are unavailable
- Error messages about missing services
- Inconsistent behavior in cross-service operations

#### Example Error
```
WorkflowError: Service not found: No service of type PLANNING_SYSTEM found
```

#### Root Cause
The Service Integration service's workflow implementations (like `ProjectPlanningWorkflow`) require multiple services to be available. If any required service is missing, the entire workflow fails.

#### Solution
1. **Implement better error handling**:
   ```python
   try:
       # Get Planning System service
       planning_service = await self.service_discovery.get_service_by_type(ServiceType.PLANNING_SYSTEM)
       
       # Generate strategic plan
       response = await self.service_client.post(...)
   except ServiceNotFoundError:
       # Fallback to a simpler plan generation if Planning System is unavailable
       self.logger.warning("Planning System unavailable, using fallback plan generation")
       response = self._generate_fallback_plan(project)
   ```

2. **Make certain services optional in workflows**:
   ```python
   # Get Planning System service if available
   try:
       planning_service = await self.service_discovery.get_service_by_type(ServiceType.PLANNING_SYSTEM)
       has_planning_system = True
   except ServiceNotFoundError:
       has_planning_system = False
       self.logger.warning("Planning System unavailable, some features will be limited")
   
   # Use planning service if available, otherwise skip
   if has_planning_system:
       # Use planning service
   else:
       # Skip or use alternative approach
   ```

3. **Implement service mocks for development**:
   ```python
   class MockPlanningService:
       """Mock implementation of Planning System for development and testing."""
       
       async def generate_strategic_plan(self, project):
           """Generate a simple strategic plan."""
           return {
               "plan": {
                   "phases": ["PLANNING", "DEVELOPMENT", "TESTING", "DEPLOYMENT"],
                   "timeline": {"start": datetime.now().isoformat(), "end": None},
                   "resources": []
               }
           }
   ```

## Debugging Techniques

### Checking Service Health

#### Description
Always implement and use health endpoints to verify service status. A health endpoint should:

- Return a 200 OK status when the service is healthy
- Include basic service information
- Check critical dependencies (database, cache, etc.)

#### Example
```python
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "service-name"}
```

To check the health endpoint from within a container:
```python
# Using Python requests
python -c "import requests; print(requests.get('http://localhost:8000/health').text)"
```

### Logging

#### Description
Implement comprehensive logging throughout your services:

- Use different log levels appropriately (DEBUG, INFO, WARNING, ERROR)
- Include contextual information in log messages
- Log the start and end of important operations
- Log exceptions with full stack traces

#### Example
```python
try:
    # Operation that might fail
    result = await some_operation()
    logger.info(f"Operation completed successfully: {result}")
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise
```

### Container Inspection

#### Description
To inspect a running container:

- View logs: `docker-compose logs <service-name>`
- Execute commands: `docker-compose exec <service-name> <command>`
- Inspect environment: `docker-compose exec <service-name> env`

## Best Practices

### Preventing Common Issues

1. **Standardize Import Patterns**
   - Use consistent import patterns across services
   - Prefer importing from shared modules when possible
   - Use explicit imports rather than wildcard imports

2. **Implement Graceful Fallbacks**
   - Add fallback mechanisms for missing components
   - Provide meaningful error messages
   - Log detailed information about failures

3. **Maintain Compatibility Layers**
   - Add alias classes for backward compatibility
   - Document deprecated patterns and their replacements
   - Implement bridge modules for major refactorings

4. **Follow Naming Conventions**
   - Use consistent naming across services
   - Follow the established patterns for model classes
   - Use descriptive names that reflect the purpose

5. **Document Dependencies**
   - Clearly document all dependencies and their versions
   - Use version ranges rather than exact versions when possible
   - Document any version constraints or incompatibilities

### Key Lessons Learned

1. **Importance of Proper Imports**
   - Missing imports can cause subtle runtime errors
   - Always ensure all classes and functions are properly imported
   - Pay special attention to imports when using complex class hierarchies

2. **Careful Variable Referencing**
   - Use clear, distinct names for variables
   - Review code for references to undefined variables
   - Be especially careful with similar parameter and local variable names

3. **Container Rebuilding**
   - Remember to rebuild containers after making code changes
   - Changes to code are not automatically reflected in running containers
   - Use volumes for development to avoid frequent rebuilds

4. **Table Naming Consistency**
   - Use the same naming convention for table names in foreign key references
   - Explicitly set `__tablename__` when in doubt
   - Be aware of how your ORM generates table names

5. **Avoiding SQLAlchemy Reserved Names**
   - Never use SQLAlchemy reserved names as column names
   - Use domain-specific names for columns that might conflict
   - Follow the pattern of prefixing "metadata" with the entity name

6. **Understanding Inheritance Patterns**
   - Choose the appropriate inheritance pattern based on your data model
   - Configure inheritance relationships correctly
   - Test polymorphic queries to ensure they work as expected

7. **Model Consistency Across Services**
   - Ensure API models are consistent across service boundaries
   - Pay attention to field names, types, and validation rules
   - Use adapters to handle differences between services

## Contributing to This Guide

If you encounter and solve an issue that is not covered in this guide, please add it to help other developers. Include:

1. A clear description of the issue
2. The solution or workaround
3. An example if possible
4. Any relevant context or background information

Use the standardized format:

```markdown
### Issue Title

#### Symptoms
- List observable symptoms
- Error messages
- Unexpected behaviors

#### Root Cause
Explanation of what causes the issue

#### Solution
Step-by-step resolution

#### Example
```code or configuration example```
```

## Related Documents

### Prerequisites
- [Service Standardization Plan](/docs/developer-guides/service-development/service-standardization-plan.md) - Understand the standardization efforts
- [Model Standardization Progress](/docs/developer-guides/service-development/model-standardization-progress.md) - Current status of model standardization

### Next Steps
- [Service Startup Troubleshooting Guide](/docs/developer-guides/service-development/service-startup-troubleshooting.md) - Guide for troubleshooting service startup issues
- [Service Migration Guide](/docs/developer-guides/service-development/service-migration-guide.md) - Guide for migrating services to use shared components

### Reference
- [Enum Standardization Guide](/docs/developer-guides/service-development/enum_standardization.md) - Guide for standardizing enum usage
- [SQLAlchemy Guide](/docs/best-practices/sqlalchemy-guide.md) - Best practices for working with SQLAlchemy
- [Pydantic Guide](/docs/best-practices/pydantic-guide.md) - Best practices for working with Pydantic
