"""
Database initialization script for the web dashboard.

This script creates the database tables and populates them with initial data.
It also sets up Flask-Migrate for database migrations.
"""

import os
import sys
from uuid import uuid4
from datetime import datetime, timedelta

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    User, Project, Agent, Task, Tool, AgentTool, 
    AIModel, ModelUsage, AuditLog, HumanInteraction
)
from flask_migrate import Migrate, init, migrate, upgrade

def init_db():
    """Initialize the database with tables and initial data."""
    app = create_app()
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        # Check if migrations directory exists
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.exists(migrations_dir):
            print("Initializing migrations...")
            init(directory=migrations_dir)
        
        # Create initial migration
        print("Creating migration...")
        migrate(directory=migrations_dir, message="Initial migration")
        
        # Apply migration
        print("Applying migration...")
        upgrade(directory=migrations_dir)
        
        # Create sample data
        create_sample_data(app)
        
def create_sample_data(app):
    """Create sample data for the application."""
    
    # Check if users already exist
    if User.query.count() == 0:
        print("Creating default users...")
        
        # Create admin user
        admin = User(
            email="admin@example.com",
            username="admin",
            name="Admin User",
            password="admin123",
            role="ADMIN",
            status="ACTIVE"
        )
        
        # Create regular user
        user = User(
            email="user@example.com",
            username="user",
            name="Regular User",
            password="user123",
            role="USER",
            status="ACTIVE"
        )
        
        # Add users to database
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()
        
        print(f"Created admin user: {admin.email}")
        print(f"Created regular user: {user.email}")
        
        # Create sample AI models
        create_sample_models()
        
        # Create sample tools
        create_sample_tools()
        
        # Create sample projects, agents, and tasks
        create_sample_projects(admin.id, user.id)
        
        # Create sample audit logs
        create_sample_audit_logs(admin.id)
        
        # Create sample human interactions
        create_sample_interactions(admin.id)
    else:
        print("Users already exist, skipping creation.")
    
    # Print all entities
    print_all_entities()


def create_sample_models():
    """Create sample AI models."""
    print("Creating sample AI models...")
    
    # Check if models already exist
    if AIModel.query.count() > 0:
        print("AI models already exist, skipping creation.")
        return
    
    # Create sample models
    models = [
        AIModel(
            id="gpt-4o",
            provider="OPENAI",
            version="2023-05",
            context_window=128000,
            capabilities={
                "REASONING": 0.95,
                "CODE_GENERATION": 0.92,
                "CREATIVE": 0.90,
                "TOOL_USE": 0.95
            },
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            is_local=False,
            status="ACTIVE"
        ),
        AIModel(
            id="claude-3-opus",
            provider="ANTHROPIC",
            version="2023-05",
            context_window=200000,
            capabilities={
                "REASONING": 0.93,
                "CODE_GENERATION": 0.88,
                "CREATIVE": 0.92,
                "TOOL_USE": 0.90
            },
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            is_local=False,
            status="ACTIVE"
        ),
        AIModel(
            id="llama3:latest",
            provider="OLLAMA",
            version="3.0",
            context_window=8192,
            capabilities={
                "REASONING": 0.85,
                "CODE_GENERATION": 0.80,
                "CREATIVE": 0.82,
                "TOOL_USE": 0.75
            },
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
            is_local=True,
            status="ACTIVE"
        )
    ]
    
    for model in models:
        db.session.add(model)
    
    db.session.commit()
    print(f"Created {len(models)} AI models")


def create_sample_tools():
    """Create sample tools."""
    print("Creating sample tools...")
    
    # Check if tools already exist
    if Tool.query.count() > 0:
        print("Tools already exist, skipping creation.")
        return
    
    # Create sample tools
    tools = [
        Tool(
            name="Web Browser",
            version="1.0",
            capability="WEB_BROWSING",
            source="BUILT_IN",
            tool_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "format": "uri"},
                    "action": {"type": "string", "enum": ["GET", "POST"]}
                },
                "required": ["url", "action"]
            },
            status="APPROVED",
            description="Browse the web and retrieve information",
            documentation_url="https://example.com/docs/web-browser",
            integration_type="LIBRARY"
        ),
        Tool(
            name="Code Interpreter",
            version="1.0",
            capability="CODE_EXECUTION",
            source="BUILT_IN",
            tool_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string"}
                },
                "required": ["code", "language"]
            },
            status="APPROVED",
            description="Execute code in a sandboxed environment",
            documentation_url="https://example.com/docs/code-interpreter",
            integration_type="LIBRARY"
        ),
        Tool(
            name="File System",
            version="1.0",
            capability="FILE_OPERATIONS",
            source="BUILT_IN",
            tool_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "action": {"type": "string", "enum": ["READ", "WRITE", "DELETE"]}
                },
                "required": ["path", "action"]
            },
            status="APPROVED",
            description="Read, write, and delete files",
            documentation_url="https://example.com/docs/file-system",
            integration_type="LIBRARY"
        ),
        Tool(
            name="GitHub API",
            version="1.0",
            capability="VERSION_CONTROL",
            source="EXTERNAL_API",
            tool_schema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "action": {"type": "string"}
                },
                "required": ["repo", "action"]
            },
            status="APPROVED",
            description="Interact with GitHub repositories",
            documentation_url="https://docs.github.com/en/rest",
            integration_type="API"
        )
    ]
    
    for tool in tools:
        db.session.add(tool)
    
    db.session.commit()
    print(f"Created {len(tools)} tools")


def create_sample_projects(admin_id, user_id):
    """Create sample projects, agents, and tasks."""
    print("Creating sample projects, agents, and tasks...")
    
    # Check if projects already exist
    if Project.query.count() > 0:
        print("Projects already exist, skipping creation.")
        return
    
    # Create sample projects
    projects = [
        Project(
            name="Website Redesign",
            description="Redesign the company website with a modern look and feel",
            status="IN_PROGRESS",
            owner_id=admin_id
        ),
        Project(
            name="Mobile App Development",
            description="Develop a mobile app for iOS and Android",
            status="PLANNING",
            owner_id=user_id
        ),
        Project(
            name="Database Migration",
            description="Migrate from MySQL to PostgreSQL",
            status="COMPLETED",
            owner_id=admin_id
        )
    ]
    
    for project in projects:
        db.session.add(project)
    
    db.session.commit()
    print(f"Created {len(projects)} projects")
    
    # Get tools for agent assignment
    web_browser = Tool.query.filter_by(name="Web Browser").first()
    code_interpreter = Tool.query.filter_by(name="Code Interpreter").first()
    file_system = Tool.query.filter_by(name="File System").first()
    github_api = Tool.query.filter_by(name="GitHub API").first()
    
    # Create sample agents for each project
    for project in projects:
        agents = []
        
        if project.name == "Website Redesign":
            agents = [
                Agent(
                    name="UI Designer",
                    type="DESIGNER",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"specialization": "web_ui"}
                ),
                Agent(
                    name="Frontend Developer",
                    type="DEVELOPER",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"languages": ["JavaScript", "HTML", "CSS"]}
                ),
                Agent(
                    name="Project Manager",
                    type="MANAGER",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"role": "coordinator"}
                )
            ]
        elif project.name == "Mobile App Development":
            agents = [
                Agent(
                    name="iOS Developer",
                    type="DEVELOPER",
                    project_id=project.id,
                    status="READY",
                    configuration={"languages": ["Swift"]}
                ),
                Agent(
                    name="Android Developer",
                    type="DEVELOPER",
                    project_id=project.id,
                    status="READY",
                    configuration={"languages": ["Kotlin"]}
                ),
                Agent(
                    name="UX Researcher",
                    type="RESEARCHER",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"focus": "mobile_ux"}
                )
            ]
        elif project.name == "Database Migration":
            agents = [
                Agent(
                    name="Database Specialist",
                    type="SPECIALIST",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"databases": ["MySQL", "PostgreSQL"]}
                ),
                Agent(
                    name="Data Validator",
                    type="AUDITOR",
                    project_id=project.id,
                    status="ACTIVE",
                    configuration={"validation_level": "strict"}
                )
            ]
        
        for agent in agents:
            db.session.add(agent)
        
        db.session.commit()
        print(f"Created {len(agents)} agents for project '{project.name}'")
        
        # Assign tools to agents
        agent_tools = []
        
        for agent in agents:
            if agent.type == "DEVELOPER":
                agent_tools.append(AgentTool(
                    agent_id=agent.id,
                    tool_id=code_interpreter.id,
                    configuration={"allowed_languages": ["JavaScript", "Python", "Swift", "Kotlin"]}
                ))
                agent_tools.append(AgentTool(
                    agent_id=agent.id,
                    tool_id=github_api.id,
                    configuration={"permissions": ["read", "write"]}
                ))
            
            if agent.type == "RESEARCHER" or agent.type == "DESIGNER":
                agent_tools.append(AgentTool(
                    agent_id=agent.id,
                    tool_id=web_browser.id,
                    configuration={"allowed_domains": ["*"]}
                ))
            
            if agent.type == "SPECIALIST" or agent.type == "AUDITOR":
                agent_tools.append(AgentTool(
                    agent_id=agent.id,
                    tool_id=file_system.id,
                    configuration={"allowed_operations": ["READ", "WRITE"]}
                ))
        
        for agent_tool in agent_tools:
            db.session.add(agent_tool)
        
        db.session.commit()
        print(f"Assigned {len(agent_tools)} tools to agents")
        
        # Create sample tasks for each project
        tasks = []
        
        if project.name == "Website Redesign":
            tasks = [
                Task(
                    name="Design Homepage",
                    description="Create a modern homepage design",
                    project_id=project.id,
                    agent_id=agents[0].id,  # UI Designer
                    status="COMPLETED",
                    priority=4,
                    completed_at=datetime.utcnow() - timedelta(days=5)
                ),
                Task(
                    name="Implement Homepage",
                    description="Implement the homepage design in HTML/CSS/JS",
                    project_id=project.id,
                    agent_id=agents[1].id,  # Frontend Developer
                    status="IN_PROGRESS",
                    priority=4
                ),
                Task(
                    name="Design About Page",
                    description="Create an about page design",
                    project_id=project.id,
                    agent_id=agents[0].id,  # UI Designer
                    status="PENDING",
                    priority=3
                )
            ]
        elif project.name == "Mobile App Development":
            tasks = [
                Task(
                    name="Create App Wireframes",
                    description="Design wireframes for the mobile app",
                    project_id=project.id,
                    agent_id=agents[2].id,  # UX Researcher
                    status="COMPLETED",
                    priority=5,
                    completed_at=datetime.utcnow() - timedelta(days=10)
                ),
                Task(
                    name="Implement iOS Login Screen",
                    description="Implement the login screen for iOS",
                    project_id=project.id,
                    agent_id=agents[0].id,  # iOS Developer
                    status="IN_PROGRESS",
                    priority=4
                ),
                Task(
                    name="Implement Android Login Screen",
                    description="Implement the login screen for Android",
                    project_id=project.id,
                    agent_id=agents[1].id,  # Android Developer
                    status="PENDING",
                    priority=4
                )
            ]
        elif project.name == "Database Migration":
            tasks = [
                Task(
                    name="Create Migration Plan",
                    description="Create a plan for migrating from MySQL to PostgreSQL",
                    project_id=project.id,
                    agent_id=agents[0].id,  # Database Specialist
                    status="COMPLETED",
                    priority=5,
                    completed_at=datetime.utcnow() - timedelta(days=15)
                ),
                Task(
                    name="Export MySQL Data",
                    description="Export data from MySQL database",
                    project_id=project.id,
                    agent_id=agents[0].id,  # Database Specialist
                    status="COMPLETED",
                    priority=4,
                    completed_at=datetime.utcnow() - timedelta(days=10)
                ),
                Task(
                    name="Import to PostgreSQL",
                    description="Import data into PostgreSQL database",
                    project_id=project.id,
                    agent_id=agents[0].id,  # Database Specialist
                    status="COMPLETED",
                    priority=4,
                    completed_at=datetime.utcnow() - timedelta(days=5)
                ),
                Task(
                    name="Validate Migration",
                    description="Validate that the migration was successful",
                    project_id=project.id,
                    agent_id=agents[1].id,  # Data Validator
                    status="COMPLETED",
                    priority=5,
                    completed_at=datetime.utcnow() - timedelta(days=2)
                )
            ]
        
        for task in tasks:
            db.session.add(task)
        
        db.session.commit()
        print(f"Created {len(tasks)} tasks for project '{project.name}'")


def create_sample_audit_logs(user_id):
    """Create sample audit logs."""
    print("Creating sample audit logs...")
    
    # Check if audit logs already exist
    if AuditLog.query.count() > 0:
        print("Audit logs already exist, skipping creation.")
        return
    
    # Get some entities to reference
    project = Project.query.first()
    agent = Agent.query.first()
    task = Task.query.first()
    
    # Create sample audit logs
    audit_logs = [
        AuditLog(
            entity_id=project.id,
            entity_type="PROJECT",
            action="CREATE",
            new_state={"name": project.name, "status": project.status},
            actor_id=user_id
        ),
        AuditLog(
            entity_id=agent.id,
            entity_type="AGENT",
            action="CREATE",
            new_state={"name": agent.name, "type": agent.type},
            actor_id=user_id
        ),
        AuditLog(
            entity_id=task.id,
            entity_type="TASK",
            action="CREATE",
            new_state={"name": task.name, "status": "PENDING"},
            actor_id=user_id
        ),
        AuditLog(
            entity_id=task.id,
            entity_type="TASK",
            action="UPDATE",
            previous_state={"name": task.name, "status": "PENDING"},
            new_state={"name": task.name, "status": "IN_PROGRESS"},
            actor_id=user_id
        )
    ]
    
    for audit_log in audit_logs:
        db.session.add(audit_log)
    
    db.session.commit()
    print(f"Created {len(audit_logs)} audit logs")


def create_sample_interactions(user_id):
    """Create sample human interactions."""
    print("Creating sample human interactions...")
    
    # Check if interactions already exist
    if HumanInteraction.query.count() > 0:
        print("Human interactions already exist, skipping creation.")
        return
    
    # Get some entities to reference
    project = Project.query.first()
    agent = Agent.query.first()
    
    # Create sample interactions
    interactions = [
        HumanInteraction(
            entity_id=project.id,
            entity_type="PROJECT",
            interaction_type="APPROVAL",
            content={
                "title": "Project Approval",
                "message": "Please approve the project plan",
                "data": {"project_name": project.name}
            },
            status="COMPLETED",
            priority="HIGH",
            assignee_id=user_id,
            response={"approved": True, "comments": "Looks good!"},
            response_time=datetime.utcnow() - timedelta(days=1)
        ),
        HumanInteraction(
            entity_id=agent.id,
            entity_type="AGENT",
            interaction_type="QUESTION",
            content={
                "title": "Agent Configuration",
                "message": "What programming languages should this agent specialize in?",
                "options": ["Python", "JavaScript", "Java", "C++"]
            },
            status="PENDING",
            priority="MEDIUM",
            assignee_id=user_id
        )
    ]
    
    for interaction in interactions:
        db.session.add(interaction)
    
    db.session.commit()
    print(f"Created {len(interactions)} human interactions")


def print_all_entities():
    """Print all entities in the database."""
    # Print all users
    print("\nCurrent users in database:")
    for user in User.query.all():
        print(f"- {user.username} ({user.email}): {user.role}")
    
    # Print all AI models
    print("\nCurrent AI models in database:")
    for model in AIModel.query.all():
        print(f"- {model.id} ({model.provider}): {model.status}")
    
    # Print all tools
    print("\nCurrent tools in database:")
    for tool in Tool.query.all():
        print(f"- {tool.name} ({tool.capability}): {tool.status}")
    
    # Print all projects
    print("\nCurrent projects in database:")
    for project in Project.query.all():
        print(f"- {project.name} ({project.status})")
        
        # Print agents for this project
        for agent in project.agents:
            print(f"  - Agent: {agent.name} ({agent.type}, {agent.status})")
            
            # Print tools for this agent
            for agent_tool in agent.agent_tools:
                print(f"    - Tool: {agent_tool.tool.name}")
        
        # Print tasks for this project
        for task in project.tasks:
            print(f"  - Task: {task.name} ({task.status}, priority: {task.priority})")

if __name__ == "__main__":
    init_db()
