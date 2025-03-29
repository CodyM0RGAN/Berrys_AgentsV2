# Web Dashboard Service

**Last Modified:** 2025-03-29  
**Completion Date:** 2025-03-29  
**Doc Type:** Reference  

---

## Overview

The Web Dashboard service provides the user interface for the Berrys_AgentsV2 platform. It enables users to create, manage, and monitor projects, agents, and tasks through an intuitive web interface. The service also provides visualizations, reports, and analytics for platform activities.

## Service Responsibilities

- **User Interface**: Providing the web interface for the platform
- **User Authentication**: Managing user authentication and session handling
- **Project Management**: Enabling project creation and management
- **Agent Management**: Enabling agent creation and management
- **Task Tracking**: Providing task visualization and tracking
- **Result Visualization**: Displaying project and task results
- **Analytics and Reporting**: Generating analytics and reports
- **User Preferences**: Managing user-specific settings and preferences

## Service Architecture

The Web Dashboard is built as a Flask application with a layered architecture:

```mermaid
graph TD
    subgraph "Presentation Layer"
        UI[UI Components]
        VE[View Engine]
        RT[Route Handlers]
    end
    
    subgraph "Business Logic Layer"
        PM[Project Manager]
        AM[Agent Manager]
        TM[Task Manager]
        RM[Result Manager]
        UM[User Manager]
        SM[Settings Manager]
    end
    
    subgraph "Data Access Layer"
        PR[Project Repository]
        AR[Agent Repository]
        TR[Task Repository]
        RR[Result Repository]
        UR[User Repository]
        SR[Settings Repository]
    end
    
    subgraph "External Interfaces"
        AG[API Gateway]
        PC[Project Coordinator]
        AO[Agent Orchestrator]
        PS[Planning System]
    end
    
    UI --> VE
    VE --> RT
    
    RT --> PM
    RT --> AM
    RT --> TM
    RT --> RM
    RT --> UM
    RT --> SM
    
    PM --> PR
    AM --> AR
    TM --> TR
    RM --> RR
    UM --> UR
    SM --> SR
    
    PM --> AG
    AM --> AG
    TM --> AG
    RM --> AG
    
    AG --> PC
    AG --> AO
    AG --> PS
    
    style UI fill:#d0e0ff,stroke:#0066cc
    style VE fill:#d0e0ff,stroke:#0066cc
    style RT fill:#d0e0ff,stroke:#0066cc
    style PM fill:#ffe0d0,stroke:#cc6600
    style AM fill:#ffe0d0,stroke:#cc6600
    style TM fill:#ffe0d0,stroke:#cc6600
    style RM fill:#ffe0d0,stroke:#cc6600
    style UM fill:#ffe0d0,stroke:#cc6600
    style SM fill:#ffe0d0,stroke:#cc6600
    style PR fill:#d0ffd0,stroke:#00cc00
    style AR fill:#d0ffd0,stroke:#00cc00
    style TR fill:#d0ffd0,stroke:#00cc00
    style RR fill:#d0ffd0,stroke:#00cc00
    style UR fill:#d0ffd0,stroke:#00cc00
    style SR fill:#d0ffd0,stroke:#00cc00
    style AG fill:#d0e0ff,stroke:#0066cc
    style PC fill:#d0e0ff,stroke:#0066cc
    style AO fill:#d0e0ff,stroke:#0066cc
    style PS fill:#d0e0ff,stroke:#0066cc
```

## Frontend Architecture

The frontend is built using a component-based architecture with React:

```mermaid
graph TD
    subgraph "Core Components"
        App[App]
        Router[Router]
        Layout[Layout]
        Nav[Navigation]
    end
    
    subgraph "Feature Components"
        PM[Project Management]
        AM[Agent Management]
        TM[Task Management]
        DM[Dashboard]
        RM[Results Management]
        SM[Settings]
    end
    
    subgraph "UI Components"
        Form[Forms]
        Table[Tables]
        Chart[Charts]
        Modal[Modals]
        Alert[Alerts]
        Card[Cards]
    end
    
    subgraph "State Management"
        Store[Redux Store]
        Actions[Actions]
        Reducers[Reducers]
        Sagas[Sagas]
    end
    
    App --> Router
    Router --> Layout
    Layout --> Nav
    
    Layout --> PM
    Layout --> AM
    Layout --> TM
    Layout --> DM
    Layout --> RM
    Layout --> SM
    
    PM --> Form
    PM --> Table
    PM --> Modal
    
    AM --> Form
    AM --> Table
    AM --> Chart
    
    TM --> Table
    TM --> Chart
    TM --> Card
    
    DM --> Chart
    DM --> Card
    DM --> Alert
    
    RM --> Table
    RM --> Chart
    RM --> Card
    
    PM --> Store
    AM --> Store
    TM --> Store
    DM --> Store
    RM --> Store
    
    Store --> Actions
    Actions --> Reducers
    Actions --> Sagas
    Reducers --> Store
    
    style App fill:#d0e0ff,stroke:#0066cc
    style Router fill:#d0e0ff,stroke:#0066cc
    style Layout fill:#d0e0ff,stroke:#0066cc
    style Nav fill:#d0e0ff,stroke:#0066cc
    style PM fill:#ffe0d0,stroke:#cc6600
    style AM fill:#ffe0d0,stroke:#cc6600
    style TM fill:#ffe0d0,stroke:#cc6600
    style DM fill:#ffe0d0,stroke:#cc6600
    style RM fill:#ffe0d0,stroke:#cc6600
    style SM fill:#ffe0d0,stroke:#cc6600
    style Form fill:#d0ffd0,stroke:#00cc00
    style Table fill:#d0ffd0,stroke:#00cc00
    style Chart fill:#d0ffd0,stroke:#00cc00
    style Modal fill:#d0ffd0,stroke:#00cc00
    style Alert fill:#d0ffd0,stroke:#00cc00
    style Card fill:#d0ffd0,stroke:#00cc00
    style Store fill:#e6e6ff,stroke:#0000cc
    style Actions fill:#e6e6ff,stroke:#0000cc
    style Reducers fill:#e6e6ff,stroke:#0000cc
    style Sagas fill:#e6e6ff,stroke:#0000cc
```

## Data Model

### Core Entities

```mermaid
erDiagram
    User ||--o{ UserPreference : has
    User ||--o{ UserRole : has
    User ||--o{ Project : owns
    User ||--o{ Dashboard : has
    UserRole }o--|| Role : assigned
    Project ||--o{ Task : contains
    Project ||--o{ Agent : uses
    Project ||--o{ ProjectResult : produces
    Dashboard ||--o{ Widget : contains
    
    User {
        UUID id
        string username
        string email
        string password_hash
        string first_name
        string last_name
        boolean active
        timestamp last_login
        timestamp created_at
        timestamp updated_at
    }
    
    UserPreference {
        UUID id
        UUID user_id
        string key
        jsonb value
        timestamp created_at
        timestamp updated_at
    }
    
    UserRole {
        UUID id
        UUID user_id
        UUID role_id
        timestamp created_at
    }
    
    Role {
        UUID id
        string name
        string description
        jsonb permissions
        timestamp created_at
        timestamp updated_at
    }
    
    Project {
        UUID id
        UUID user_id
        string name
        string description
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    Task {
        UUID id
        UUID project_id
        string name
        string description
        string status
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }
    
    Agent {
        UUID id
        string name
        string description
        string type
        string status
        jsonb capabilities
        jsonb configuration
        timestamp created_at
        timestamp updated_at
    }
    
    ProjectResult {
        UUID id
        UUID project_id
        string name
        string description
        string type
        string location
        jsonb metadata
        timestamp created_at
    }
    
    Dashboard {
        UUID id
        UUID user_id
        string name
        string description
        string layout
        timestamp created_at
        timestamp updated_at
    }
    
    Widget {
        UUID id
        UUID dashboard_id
        string type
        string title
        jsonb configuration
        jsonb data_source
        int position_x
        int position_y
        int width
        int height
        timestamp created_at
        timestamp updated_at
    }
```

## Routes and Views

### Main Routes

| Route | View | Description |
|-------|------|-------------|
| `/` | Dashboard | Main dashboard view |
| `/login` | Login | User login page |
| `/register` | Register | User registration page |
| `/projects` | Projects | Project listing |
| `/projects/new` | New Project | Project creation form |
| `/projects/:id` | Project Detail | Project details view |
| `/projects/:id/edit` | Edit Project | Project edit form |
| `/agents` | Agents | Agent listing |
| `/agents/new` | New Agent | Agent creation form |
| `/agents/:id` | Agent Detail | Agent details view |
| `/agents/:id/edit` | Edit Agent | Agent edit form |
| `/tasks` | Tasks | Task listing |
| `/tasks/:id` | Task Detail | Task details view |
| `/results` | Results | Results listing |
| `/results/:id` | Result Detail | Result details view |
| `/settings` | Settings | User settings |
| `/admin` | Admin | Admin dashboard (role restricted) |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List projects |
| GET | `/api/projects/:id` | Get project details |
| POST | `/api/projects` | Create project |
| PUT | `/api/projects/:id` | Update project |
| DELETE | `/api/projects/:id` | Delete project |
| GET | `/api/agents` | List agents |
| GET | `/api/agents/:id` | Get agent details |
| POST | `/api/agents` | Create agent |
| PUT | `/api/agents/:id` | Update agent |
| DELETE | `/api/agents/:id` | Delete agent |
| GET | `/api/tasks` | List tasks |
| GET | `/api/tasks/:id` | Get task details |
| PUT | `/api/tasks/:id/status` | Update task status |
| GET | `/api/results` | List results |
| GET | `/api/results/:id` | Get result details |
| GET | `/api/dashboards` | List dashboards |
| POST | `/api/dashboards` | Create dashboard |
| PUT | `/api/dashboards/:id` | Update dashboard |
| DELETE | `/api/dashboards/:id` | Delete dashboard |
| GET | `/api/widgets` | List widgets |
| POST | `/api/widgets` | Create widget |
| PUT | `/api/widgets/:id` | Update widget |
| DELETE | `/api/widgets/:id` | Delete widget |

## Key Features

### Project Management

- **Project Creation**: Form-based project creation with templates
- **Project Dashboard**: Overview of project status and metrics
- **Task Visualization**: Gantt chart and Kanban board views
- **Timeline View**: Timeline visualization of project activities
- **Resource Allocation**: Agent allocation and utilization tracking
- **Document Management**: Project-related document management

### Agent Management

- **Agent Catalog**: Browsable catalog of available agent templates
- **Agent Configuration**: Form-based agent configuration
- **Agent Monitoring**: Real-time monitoring of agent status
- **Agent Analytics**: Performance metrics and usage statistics
- **Specialization Management**: Agent specialization configuration
- **Capability Visualization**: Visual representation of agent capabilities

### Task Management

- **Task Board**: Kanban-style task board for task tracking
- **Task Details**: Detailed view of task information
- **Task Dependencies**: Visualization of task dependencies
- **Task Progress**: Real-time progress tracking
- **Result Viewer**: Integrated result viewing
- **Task History**: Historical view of task activities

### Dashboards and Reporting

- **Customizable Dashboards**: User-configurable dashboards
- **Interactive Widgets**: Drag-and-drop widget positioning
- **Data Visualization**: Rich charting and visualization tools
- **Report Generation**: Scheduled and on-demand report generation
- **Export Functionality**: Data export in various formats
- **Alert Configuration**: Configurable alerts and notifications

### User Management

- **User Registration**: User self-registration
- **Profile Management**: User profile management
- **Role-Based Access**: Role-based access control
- **Preference Settings**: User preference configuration
- **Activity History**: User activity logging
- **API Key Management**: Management of API keys for external access

## UI Components

### Charts and Visualizations

- **Line Charts**: Time-series data visualization
- **Bar Charts**: Comparative data visualization
- **Pie Charts**: Proportion visualization
- **Gantt Charts**: Project timeline visualization
- **Network Graphs**: Relationship visualization
- **Heatmaps**: Density visualization
- **Scatter Plots**: Distribution visualization
- **Tree Maps**: Hierarchical data visualization

### Interactive Elements

- **Data Tables**: Sortable and filterable data tables
- **Forms**: Form elements with validation
- **Modals**: Modal dialogs for focused interactions
- **Wizards**: Step-by-step guided flows
- **Tooltips**: Contextual information display
- **Dropdown Menus**: Selection menus
- **Search Fields**: Advanced search functionality
- **Pagination**: Paginated data display

### Layout Components

- **Navigation Bar**: Top navigation bar
- **Sidebar**: Collapsible sidebar
- **Tab Panels**: Tabbed content organization
- **Cards**: Content cards for information display
- **Grids**: Responsive grid layouts
- **Drawers**: Side drawers for supplementary information
- **Breadcrumbs**: Hierarchical navigation indicators
- **Accordions**: Collapsible content sections

## Authentication and Authorization

The service implements a comprehensive authentication and authorization system:

- **Authentication Methods**: Local username/password, OAuth, SSO
- **Session Management**: Session creation, tracking, and expiration
- **Password Policies**: Password strength enforcement and expiration
- **Multi-Factor Authentication**: Support for MFA methods
- **Role-Based Access Control**: Granular permission management
- **API Authentication**: JWT-based API authentication

## Theme and Styling

The user interface supports multiple themes and styling options:

- **Light and Dark Modes**: Support for light and dark color schemes
- **Customizable Colors**: Primary and secondary color customization
- **Typography Options**: Font family and size configuration
- **Density Settings**: UI density configuration
- **Responsive Design**: Adaptation to different screen sizes
- **Accessibility Features**: High contrast mode, screen reader support

## Integration Points

### API Gateway

- **Authentication**: User authentication and session management
- **Request Routing**: Routing requests to appropriate services
- **Response Formatting**: Standardizing response formats
- **Error Handling**: Consistent error handling

### Project Coordinator

- **Project Management**: Creating and managing projects
- **Project Status**: Retrieving project status information
- **Team Management**: Managing project teams
- **Result Access**: Accessing project results

### Agent Orchestrator

- **Agent Management**: Creating and managing agents
- **Agent Status**: Monitoring agent status
- **Task Assignment**: Assigning tasks to agents
- **Capability Discovery**: Discovering agent capabilities

### Planning System

- **Plan Management**: Creating and managing project plans
- **Task Management**: Creating and managing tasks
- **Dependency Management**: Managing task dependencies
- **Progress Tracking**: Tracking task progress

## Configuration

Configuration is managed through environment variables:

```python
# Example environment variables
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/web_dashboard
REDIS_URL=redis://localhost:6379
API_GATEWAY_URL=http://api-gateway:8080
SESSION_TYPE=redis
SESSION_PERMANENT=True
SESSION_USE_SIGNER=True
SESSION_REDIS=redis://localhost:6379
LOG_LEVEL=INFO
```

## Deployment

The service is deployed as a Docker container:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build frontend assets
COPY frontend/build /app/static

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "run:app"]
```

## Monitoring and Health

### Health Checks

The service provides health check endpoints:

- **GET /health/liveness**: Confirms the service is running
- **GET /health/readiness**: Confirms the service is ready to accept requests
- **GET /health/dependencies**: Checks the status of service dependencies

### Metrics

The service exposes Prometheus metrics at `/metrics`:

- **http_request_duration_seconds**: HTTP request duration histogram
- **http_request_count**: Count of HTTP requests by endpoint and status
- **active_sessions**: Count of active user sessions
- **concurrent_users**: Count of concurrent users
- **database_query_duration_seconds**: Database query duration histogram
- **api_gateway_request_duration_seconds**: API Gateway request duration histogram
- **frontend_asset_size_bytes**: Size of frontend assets

## Frontend Performance Optimization

The service implements several frontend performance optimizations:

- **Code Splitting**: Splitting code into manageable chunks
- **Lazy Loading**: Loading components only when needed
- **Asset Optimization**: Minification and compression of assets
- **Caching Strategies**: Efficient caching of frontend assets
- **Preloading**: Preloading critical resources
- **Virtual Scrolling**: Efficient rendering of large lists
- **Memoization**: Caching computation results for performance
- **Bundle Analysis**: Regular analysis and optimization of bundle size

## Common Issues and Troubleshooting

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Slow page load times | Large asset sizes, unoptimized queries | Optimize frontend assets, implement pagination, optimize database queries |
| Session timeouts | Short session expiration, network issues | Adjust session timeout settings, implement refresh tokens |
| UI rendering issues | Browser compatibility, JS errors | Test across browsers, implement error boundaries |
| API connection failures | Service unavailability, network issues | Implement circuit breakers, add request retries |
| Missing data in dashboards | Permission issues, data availability | Check permissions, verify data sources |
| Chart rendering problems | Data format issues, browser compatibility | Normalize data formats, use polyfills |
| High memory usage | Memory leaks, large datasets | Implement virtual scrolling, optimize component lifecycle |
| Authentication failures | Expired tokens, invalid credentials | Implement token refresh, improve error messages |

## Security Considerations

- **CSRF Protection**: Cross-Site Request Forgery protection
- **XSS Prevention**: Cross-Site Scripting prevention
- **Content Security Policy**: Restrictive CSP implementation
- **HTTPS Enforcement**: Mandatory HTTPS connections
- **Secure Cookies**: HttpOnly and Secure cookie flags
- **Input Validation**: Strict input validation
- **Output Encoding**: Proper output encoding
- **Rate Limiting**: API rate limiting
- **Audit Logging**: Comprehensive security event logging

## References

- [System Overview](../architecture/system-overview.md)
- [Communication Patterns](../architecture/communication-patterns.md)
- [Data Flow](../architecture/data-flow.md)
- [Project Execution](../../guides/process-flows/project-execution.md)
- [Agent Lifecycle](../../guides/process-flows/agent-lifecycle.md)
- [API Gateway Service](api-gateway.md)
- [Project Coordinator Service](project-coordinator.md)
