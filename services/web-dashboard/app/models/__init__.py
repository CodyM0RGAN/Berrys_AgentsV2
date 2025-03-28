"""
Models package for the web dashboard application.

This package contains SQLAlchemy models for the application.
"""

from app.models.base import BaseModel
from app.models.user import User
from app.models.project import Project
from app.models.agent import Agent
from app.models.task import Task
from app.models.tool import Tool, AgentTool
from app.models.ai_model import AIModel, ModelUsage
from app.models.audit import AuditLog, log_create, log_update, log_delete
from app.models.human import HumanInteraction, request_approval, ask_question
# Removed chat models import: from app.models.chat import ChatSession, ChatMessage

__all__ = [
    'BaseModel', 
    'User', 
    'Project', 
    'Agent', 
    'Task', 
    'Tool', 
    'AgentTool',
    'AIModel',
    'ModelUsage',
    'AuditLog',
    'log_create',
    'log_update',
    'log_delete',
    'HumanInteraction',
    'request_approval',
    'ask_question'
    # Removed ChatSession and ChatMessage from __all__
]
