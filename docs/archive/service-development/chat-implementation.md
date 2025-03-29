# Chat Implementation Guide

This document provides technical details about the implementation of the chat functionality in Berry's Agents system, focusing on the architecture, design decisions, and key components.

## Overview

The chat functionality allows users to interact with Berry, a friendly AI assistant that helps users create and manage projects and acts as a liason between the AI team and the user to dynamically communicate between both parties. Berry guides users through the process of submitting project ideas, creating projects, and communicating user feedback to agent teams assigned to those projects.

## Architecture

The chat functionality is implemented across multiple services:

1. **Web Dashboard**: Provides the user interface for chat interactions
2. **Project Coordinator**: Handles chat messages, stores chat history, and manages project creation
3. **Model Orchestration**: Provides LLM capabilities for generating responses and analyzing messages

### Web Dashboard

The Web Dashboard service provides the chat interface for users to interact with Berry. Key components include:

- **Chat UI**: A responsive chat interface with real-time updates
- **Chat API Client**: Client for communicating with the Berry, a liason for other AI agents/services such as the Project Coordinator service
- **Chat Session Management**: Manages chat sessions and history

### Project Coordinator

The Project Coordinator service handles chat messages, stores chat history, and manages project creation. Key components include:

- **Chat Router**: API endpoints for chat interactions
- **Agent Instructions**: Database-driven instructions for Berry's personality and capabilities
- **Chat Session Storage**: Persistent storage for chat sessions and messages
- **Model Orchestrator Client**: Client for communicating with the Model Orchestration service

### Model Orchestration

The Model Orchestration service provides LLM capabilities for generating responses and analyzing messages. Key components include:

- **LLM Integration**: Integration with large language models
- **Response Generation**: Generates responses based on user messages and context
- **Message Analysis**: Analyzes messages to extract structured information

## Database Models

### Agent Instructions

The `AgentInstructions` model stores instructions for Berry's personality and capabilities:

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
    
    # Relationships
    capabilities_list = relationship("AgentCapability", back_populates="agent_instructions", cascade="all, delete-orphan")
    knowledge_domains_list = relationship("AgentKnowledgeDomain", back_populates="agent_instructions", cascade="all, delete-orphan")
```

### Agent Capability

The `AgentCapability` model stores detailed information about agent capabilities:

```python
class AgentCapability(Base):
    """SQLAlchemy model for agent capabilities."""
    __tablename__ = "agent_capability"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    capability_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=True)
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", back_populates="capabilities_list")
```

### Agent Knowledge Domain

The `AgentKnowledgeDomain` model stores detailed information about agent knowledge domains:

```python
class AgentKnowledgeDomain(Base):
    """SQLAlchemy model for agent knowledge domains."""
    __tablename__ = "agent_knowledge_domain"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_instruction_id = Column(UUID(as_uuid=True), ForeignKey("agent_instruction.id"), nullable=False)
    domain_name = Column(String(255), nullable=False)
    priority_level = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", back_populates="knowledge_domains_list")
```

### Agent Prompt Template

The `AgentPromptTemplate` model stores prompt templates for different conversation scenarios:

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
    
    # Unique constraint for agent_instruction_id, template_name, and template_version
    __table_args__ = (
        UniqueConstraint('agent_instruction_id', 'template_name', 'template_version', 
                         name='uix_agent_prompt_template'),
    )
    
    # Relationships
    agent_instructions = relationship("AgentInstructions", backref="prompt_templates")
```

### Chat Session

The `ChatSession` model stores chat sessions:

```python
class ChatSession(Base):
    """SQLAlchemy model for chat sessions."""
    __tablename__ = "chat_session"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
```

### Chat Message

The `ChatMessage` model stores chat messages:

```python
class ChatMessage(Base):
    """SQLAlchemy model for chat messages."""
    __tablename__ = "chat_message"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(36), ForeignKey("chat_session.id"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    message_metadata = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
```

## API Endpoints

### Send Message

```
POST /chat/message
```

Request:
```json
{
  "message": "I want to create a new project for a website",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "789e4567-e89b-12d3-a456-426614174000",
  "history": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-03-24T19:30:00.000Z"
    },
    {
      "role": "bot",
      "content": "Hi there! I'm Berry, your friendly project assistant. How can I help you today?",
      "timestamp": "2025-03-24T19:30:05.000Z"
    }
  ]
}
```

Response:
```json
{
  "response": "I'd be happy to help you create a new project for a website! Could you tell me more about what kind of website you're looking to build?",
  "actions": [
    {
      "type": "create_project",
      "data": {
        "name": "Website Project",
        "description": "Project created from chat: I want to create a new project for a website",
        "status": "PLANNING",
        "metadata": {
          "source": "chat",
          "session_id": "123e4567-e89b-12d3-a456-426614174000",
          "user_id": "789e4567-e89b-12d3-a456-426614174000"
        }
      }
    }
  ]
}
```

### Get Chat History

```
GET /chat/sessions/{session_id}
```

Response:
```json
[
  {
    "role": "user",
    "content": "Hello",
    "timestamp": "2025-03-24T19:30:00.000Z",
    "metadata": {}
  },
  {
    "role": "bot",
    "content": "Hi there! I'm Berry, your friendly project assistant. How can I help you today?",
    "timestamp": "2025-03-24T19:30:05.000Z",
    "metadata": {}
  },
  {
    "role": "user",
    "content": "I want to create a new project for a website",
    "timestamp": "2025-03-24T19:31:00.000Z",
    "metadata": {}
  },
  {
    "role": "bot",
    "content": "I'd be happy to help you create a new project for a website! Could you tell me more about what kind of website you're looking to build?",
    "timestamp": "2025-03-24T19:31:05.000Z",
    "metadata": {
      "actions": [
        {
          "type": "create_project",
          "data": {
            "name": "Website Project",
            "description": "Project created from chat: I want to create a new project for a website",
            "status": "PLANNING",
            "metadata": {
              "source": "chat",
              "session_id": "123e4567-e89b-12d3-a456-426614174000",
              "user_id": "789e4567-e89b-12d3-a456-426614174000"
            }
          }
        }
      ]
    }
  }
]
```

## LLM Integration

The chat functionality uses the Model Orchestration service to generate responses and analyze messages. The Model Orchestrator client provides methods for communicating with the Model Orchestration service:

```python
async def generate_response(
    self, 
    message: str, 
    context: Dict[str, Any]
) -> str:
    """
    Generate a response using the Model Orchestration service.
    
    Args:
        message: User message
        context: Context information for the model
        
    Returns:
        Generated response
    """
    # Implementation details...
```

```python
async def analyze_message(
    self, 
    message: str, 
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a message to extract structured information.
    
    Args:
        message: User message
        context: Context information for the model
        
    Returns:
        Extracted information
    """
    # Implementation details...
```

## Berry's Personality

Berry's personality is defined in the database using the `AgentInstructions` model. The default personality includes:

- **Purpose**: Berry is a friendly and knowledgeable project assistant designed to help users create and manage projects.
- **Capabilities**: Create projects, assign agents, select models, etc.
- **Tone Guidelines**: Friendly, enthusiastic, supportive, conversational, with occasional emojis.
- **Knowledge Domains**: Project management, AI models, agent systems, etc.

## Future Enhancements

1. **WebSocket Support**: Implement real-time chat with WebSockets
2. **Advanced Message Analysis**: Enhance message analysis to better extract project requirements
3. **Personalized Responses**: Tailor responses based on user preferences and history
4. **Multi-Agent Collaboration**: Allow Berry to collaborate with other agents
5. **Context-Aware Responses**: Improve response generation with more context awareness

## Troubleshooting

### Common Issues

1. **Database Connection Issues**: Ensure the database is running and accessible
2. **Model Orchestration Service Unavailable**: Check the Model Orchestration service status
3. **Chat Session Not Found**: Verify the session ID is correct
4. **Invalid Message Format**: Ensure the message format is correct

### Debugging

1. **Enable Debug Logging**: Set `log_level` to `DEBUG` in the configuration
2. **Check Logs**: Review the logs for error messages
3. **Test API Endpoints**: Use a tool like Postman to test the API endpoints
4. **Verify Database Schema**: Ensure the database schema is up to date

## Important Dependencies

When deploying the chat functionality, ensure all required dependencies are installed:

1. **PostgreSQL Driver**: Both the Web Dashboard and Project Coordinator services require a PostgreSQL driver for database connections:
   ```
   psycopg2-binary==2.9.6  # Required for PostgreSQL connections
   ```
   
   Without this dependency, the services will fail to start with a `ModuleNotFoundError: No module named 'psycopg2'` error.

2. **WebSocket Support**: For real-time chat functionality, ensure the following packages are installed:
   ```
   Flask-SocketIO==5.3.4
   eventlet==0.33.3
   gevent==23.7.0
   gevent-websocket==0.10.1
   ```

3. **HTTP Client**: For service-to-service communication, ensure an HTTP client is available:
   ```
   httpx==0.25.1  # For async HTTP requests
   requests==2.31.0  # For sync HTTP requests
   ```

Refer to the [Web Dashboard Troubleshooting Guide](web-dashboard-troubleshooting.md) for more information on resolving common deployment issues.
