# Import models in the correct order to avoid circular dependencies
# This file ensures proper initialization order for SQLAlchemy models

# First, import base models without relationships
from .base import BaseModel
from .user import UserModel

# Then import models with simple relationships
from .project import ProjectModel
from .tool import ToolModel

# Then import models with more complex relationships
from .agent import AgentModel
from .task import TaskModel
from .communication import CommunicationModel
from .audit import AuditLogModel
from .human_interaction import HumanInteractionModel
from .ai_model import AIModelModel

# Finally, import association tables
# These are imported after all models to avoid circular dependencies
from .agent import agent_tool_association
from .task import task_dependency

# Export all models
__all__ = [
    'BaseModel',
    'UserModel',
    'ProjectModel',
    'ToolModel',
    'AgentModel',
    'TaskModel',
    'CommunicationModel',
    'AuditLogModel',
    'HumanInteractionModel',
    'AIModelModel',
    'agent_tool_association',
    'task_dependency',
]
