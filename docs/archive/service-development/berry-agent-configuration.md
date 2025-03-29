# Berry Agent Configuration Guide

This guide explains how Berry, the project assistant agent, is configured in the database and how to use the agent repository to access Berry's configuration.

## Overview

Berry is a versatile assistant who engages in friendly conversations while also helping users create and manage projects. Berry recognizes when conversations might lead to project opportunities and can guide users through the project creation process when appropriate.

Berry's configuration is stored in the database using several tables:
- `agent_instruction`: Stores Berry's basic information, purpose, capabilities, tone guidelines, and knowledge domains
- `agent_capability`: Stores detailed information about Berry's capabilities
- `agent_knowledge_domain`: Stores detailed information about Berry's knowledge domains
- `agent_prompt_template`: Stores prompt templates for different conversation scenarios

## Database Schema

### Agent Instructions

The `agent_instruction` table stores the basic information about Berry:

```python
class AgentInstructions(Base):
    """SQLAlchemy model for agent instructions."""
    __tablename__ = "agent_instruction"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(255), nullable=False, unique=True)
    purpose = Column(Text, nullable=False)
    capabilities = Column(JSON, nullable=False)
    tone_guidelines = Column(Text, nullable=False)
    knowledge_domains = Column(JSON, nullable=False)
    response_templates = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Agent Capabilities

The `agent_capability` table stores detailed information about Berry's capabilities:

```python
class AgentCapability(Base):
    """SQLAlchemy model for agent capabilities."""
    __tablename__ = "agent_capability"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    capability_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=True)
```

### Agent Knowledge Domains

The `agent_knowledge_domain` table stores detailed information about Berry's knowledge domains:

```python
class AgentKnowledgeDomain(Base):
    """SQLAlchemy model for agent knowledge domains."""
    __tablename__ = "agent_knowledge_domain"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    domain_name = Column(String(255), nullable=False)
    priority_level = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
```

### Agent Prompt Templates

The `agent_prompt_template` table stores prompt templates for different conversation scenarios:

```python
class AgentPromptTemplate(Base):
    """SQLAlchemy model for agent prompt templates."""
    __tablename__ = "agent_prompt_template"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    template_version = Column(String(50), nullable=False)
    template_content = Column(Text, nullable=False)
    context_parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Berry's Configuration

Berry's configuration includes:

### Purpose

Berry's purpose is to be a versatile assistant who engages in friendly conversations while also helping users create and manage projects. Berry recognizes when conversations might lead to project opportunities and can guide users through the project creation process when appropriate.

### Capabilities

Berry has the following capabilities:

1. **Project Creation**: Ability to create new projects based on user ideas
2. **Agent Assignment**: Ability to assign specialized agents to projects
3. **Model Selection**: Ability to recommend appropriate AI models for projects
4. **General Conversation**: Ability to engage in friendly, helpful conversation on a wide range of topics
5. **Project Opportunity Recognition**: Ability to recognize when a conversation is trending toward a potential project

### Tone Guidelines

Berry's tone is friendly, enthusiastic, and supportive. The tone is conversational with occasional emojis to convey warmth. Berry is knowledgeable but approachable, avoiding overly technical language unless the user demonstrates technical expertise.

### Knowledge Domains

Berry has knowledge in the following domains:

1. **Project Management**: Knowledge of project management methodologies like agile, waterfall, and kanban
2. **AI Models**: Understanding of large language models, computer vision, and recommendation systems
3. **Agent Systems**: Knowledge of multi-agent coordination, specialized agent capabilities, and agent communication
4. **General Topics**: Awareness of current events, technology trends, and common interests
5. **Conversation Skills**: Skills in active listening, empathetic responses, and contextual awareness
6. **Project Indicators**: Ability to recognize solution seeking, creation interests, and development curiosity

### Response Templates

Berry has templates for common responses:

1. **Greeting**: "Hi there! I'm Berry, your friendly project assistant. How can I help you today?"
2. **Project Creation Suggestion**: "Based on what you've shared, I think we could create a project for {{project_type}}. Would you like me to set that up for you?"
3. **Project Creation Confirmation**: "Great! I've created a new project called '{{project_name}}'. Now, let's talk about what you'd like to accomplish with this project."

### Prompt Templates

Berry has the following prompt templates:

1. **Conversation Intent Recognition**: Helps Berry analyze the conversation to determine the user's primary intent
2. **Mental Model Building**: Helps Berry maintain a comprehensive mental model of the user's needs, interests, and the context of the conversation
3. **Response Strategies**: Helps Berry adapt response strategies based on the conversation context
4. **Project Potential Detection**: Helps Berry analyze the conversation for indicators of project potential

## Using the Agent Repository

The `AgentRepository` class provides methods for accessing Berry's configuration from the database:

```python
from ..repositories.agent_repository import AgentRepository

# Create an instance of the repository
agent_repository = AgentRepository(db)

# Get Berry's complete configuration
berry_config = agent_repository.get_complete_agent_configuration("Berry")

# Access specific parts of Berry's configuration
agent_name = berry_config["agent_name"]
purpose = berry_config["purpose"]
capabilities = berry_config["capabilities"]
tone_guidelines = berry_config["tone_guidelines"]
knowledge_domains = berry_config["knowledge_domains"]
response_templates = berry_config["response_templates"]
prompt_templates = berry_config["prompt_templates"]

# Get a specific prompt template
conversation_intent_template = prompt_templates["conversation_intent_recognition"]
template_content = conversation_intent_template["content"]
context_parameters = conversation_intent_template["context_parameters"]
```

## Using Berry's Configuration in the Chat Router

The chat router uses Berry's configuration to generate responses to user messages:

```python
# Get Berry's configuration from the repository
agent_repository = AgentRepository(db)
berry_config = agent_repository.get_complete_agent_configuration("Berry")

# Prepare context for the model orchestrator
context = {
    "agent_configuration": berry_config,
    "chat_history": chat_history,
    "user_id": chat_request.user_id,
    "session_id": chat_request.session_id
}

# Determine which prompt template to use based on the conversation context
prompt_template = None
if "prompt_templates" in berry_config and berry_config["prompt_templates"]:
    # For the first message in a conversation, use the conversation_intent_recognition template
    if len(chat_history) <= 1:
        if "conversation_intent_recognition" in berry_config["prompt_templates"]:
            prompt_template = berry_config["prompt_templates"]["conversation_intent_recognition"]
    # For project-related keywords, use the project_potential_detection template
    elif any(keyword in chat_request.message.lower() for keyword in 
             ["create", "build", "develop", "project", "idea", "make"]):
        if "project_potential_detection" in berry_config["prompt_templates"]:
            prompt_template = berry_config["prompt_templates"]["project_potential_detection"]
    # Default to the mental_model_building template
    else:
        if "mental_model_building" in berry_config["prompt_templates"]:
            prompt_template = berry_config["prompt_templates"]["mental_model_building"]

# Add the selected prompt template to the context
if prompt_template:
    context["selected_prompt_template"] = prompt_template

# Call the model orchestrator
response = await model_orchestrator_client.generate_response(
    message=chat_request.message,
    context=context
)
```

## Creating a New Agent

To create a new agent similar to Berry, you can use the following steps:

1. Create a migration script to insert the agent's configuration into the database
2. Use the `AgentRepository` to access the agent's configuration
3. Update the chat router to use the agent's configuration

Here's an example of creating a new agent:

```python
# Create the agent instructions
agent = AgentInstructions(
    id=uuid.uuid4(),
    agent_name="NewAgent",
    purpose="New agent purpose",
    capabilities={
        "capability1": {
            "description": "Capability 1 description",
            "parameters": {"param1": "value1"}
        }
    },
    tone_guidelines="Tone guidelines for the new agent",
    knowledge_domains={
        "domain1": {
            "priority": 1,
            "description": "Domain 1 description"
        }
    },
    response_templates={
        "greeting": "Hello, I'm NewAgent!"
    }
)
db.add(agent)
db.flush()

# Add capabilities
capability = AgentCapability(
    id=uuid.uuid4(),
    agent_instruction_id=agent.id,
    capability_name="capability1",
    description="Capability 1 description",
    parameters={"param1": "value1"}
)
db.add(capability)

# Add knowledge domains
knowledge_domain = AgentKnowledgeDomain(
    id=uuid.uuid4(),
    agent_instruction_id=agent.id,
    domain_name="domain1",
    priority_level=1,
    description="Domain 1 description"
)
db.add(knowledge_domain)

# Add prompt templates
prompt_template = AgentPromptTemplate(
    id=uuid.uuid4(),
    agent_instruction_id=agent.id,
    template_name="template1",
    template_version="1.0",
    template_content="This is a template for the new agent",
    context_parameters={"required": ["param1"], "optional": ["param2"]},
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(prompt_template)

db.commit()
```

## Best Practices

1. **Use the Repository Pattern**: Always use the `AgentRepository` to access agent configurations
2. **Version Prompt Templates**: Use versioning for prompt templates to track changes
3. **Test Agent Configurations**: Write tests to verify that agent configurations are correct
4. **Document Agent Capabilities**: Document the capabilities of each agent
5. **Use Context Parameters**: Define required and optional context parameters for prompt templates

## Applying Berry's Configuration

To apply Berry's configuration to the database, you can use the provided migration scripts:

### Windows

```bash
cd services/project-coordinator
scripts\apply_berry_migration.bat
```

### Unix-based Systems (Linux, macOS)

```bash
cd services/project-coordinator
chmod +x scripts/apply_berry_migration.sh
./scripts/apply_berry_migration.sh
```

### Manual Application

If you prefer to apply the migration manually, you can use Alembic directly:

```bash
cd services/project-coordinator
alembic upgrade head
```

After applying the migration, you can verify that Berry's configuration exists in the database:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.repositories.agent_repository import AgentRepository

# Create a database session
engine = create_engine("your-database-url")
Session = sessionmaker(bind=engine)
session = Session()

# Get Berry's configuration
repository = AgentRepository(session)
berry_config = repository.get_complete_agent_configuration("Berry")

# Print Berry's configuration
print(f"Agent Name: {berry_config['agent_name']}")
print(f"Purpose: {berry_config['purpose']}")
print(f"Capabilities: {list(berry_config['capabilities'].keys())}")
print(f"Prompt Templates: {list(berry_config['prompt_templates'].keys())}")
```

## Conclusion

Berry's database-driven configuration provides a flexible and maintainable way to define agent behavior. By using the `AgentRepository`, you can easily access Berry's configuration and use it to generate responses to user messages. You can also create new agents with different capabilities and prompt templates to handle specific use cases.

The migration script provided in this guide ensures that Berry's configuration is properly set up in the database, making it easy to get started with Berry's chat functionality.
