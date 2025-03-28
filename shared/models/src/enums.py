"""
Shared enum definitions for the Berrys_AgentsV2 project.

This module contains all enum definitions used across the project,
ensuring consistency between SQLAlchemy models and Pydantic models.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any, Union


class ProjectStatus(str, Enum):
    """Status of a project."""
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class AgentStatus(str, Enum):
    """Status of an agent."""
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class AgentType(str, Enum):
    """Type of an agent."""
    COORDINATOR = "COORDINATOR"
    ASSISTANT = "ASSISTANT"
    RESEARCHER = "RESEARCHER"
    DEVELOPER = "DEVELOPER"
    DESIGNER = "DESIGNER"
    SPECIALIST = "SPECIALIST"
    AUDITOR = "AUDITOR"
    CUSTOM = "CUSTOM"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    """Priority of a task."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolType(str, Enum):
    """Type of a tool."""
    API = "API"
    CLI = "CLI"
    LIBRARY = "LIBRARY"
    SERVICE = "SERVICE"
    CUSTOM = "CUSTOM"


class ToolStatus(str, Enum):
    """Status of a tool."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"
    EXPERIMENTAL = "EXPERIMENTAL"


class ModelProvider(str, Enum):
    """Provider of an AI model."""
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    OLLAMA = "OLLAMA"
    CUSTOM = "CUSTOM"


class ModelStatus(str, Enum):
    """Status of an AI model."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


class ModelCapability(str, Enum):
    """Capability of an AI model."""
    CHAT = "CHAT"
    COMPLETION = "COMPLETION"
    EMBEDDING = "EMBEDDING"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    AUDIO_TRANSCRIPTION = "AUDIO_TRANSCRIPTION"
    AUDIO_TRANSLATION = "AUDIO_TRANSLATION"


class RequestType(str, Enum):
    """Type of a model request."""
    CHAT = "CHAT"
    COMPLETION = "COMPLETION"
    EMBEDDING = "EMBEDDING"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    AUDIO_TRANSCRIPTION = "AUDIO_TRANSCRIPTION"
    AUDIO_TRANSLATION = "AUDIO_TRANSLATION"


class HumanInteractionType(str, Enum):
    """Type of human interaction."""
    APPROVAL = "APPROVAL"
    FEEDBACK = "FEEDBACK"
    CLARIFICATION = "CLARIFICATION"
    NOTIFICATION = "NOTIFICATION"


class AuditAction(str, Enum):
    """Action recorded in an audit log."""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXECUTE = "EXECUTE"


class UserRole(str, Enum):
    """Role of a user."""
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"


class UserStatus(str, Enum):
    """Status of a user."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"


class DependencyType(str, Enum):
    """Type of task dependency."""
    FINISH_TO_START = "FINISH_TO_START"  # Task B can't start until Task A finishes
    START_TO_START = "START_TO_START"    # Task B can't start until Task A starts
    FINISH_TO_FINISH = "FINISH_TO_FINISH"  # Task B can't finish until Task A finishes
    START_TO_FINISH = "START_TO_FINISH"  # Task B can't finish until Task A starts


class AnalyticsType(str, Enum):
    """Type of analytics data."""
    PERFORMANCE = "PERFORMANCE"
    USAGE = "USAGE"
    COST = "COST"
    QUALITY = "QUALITY"
    TIMELINE = "TIMELINE"


class ArtifactType(str, Enum):
    """Type of project artifact."""
    DOCUMENT = "DOCUMENT"
    CODE = "CODE"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    DATA = "DATA"
    MODEL = "MODEL"
    OTHER = "OTHER"


class ResourceType(str, Enum):
    """Type of project resource."""
    AGENT = "AGENT"
    MODEL = "MODEL"
    TOOL = "TOOL"
    COMPUTE = "COMPUTE"
    STORAGE = "STORAGE"
    OTHER = "OTHER"


class OptimizationTarget(str, Enum):
    """Target for optimization."""
    PERFORMANCE = "PERFORMANCE"
    COST = "COST"
    QUALITY = "QUALITY"
    SPEED = "SPEED"
    ACCURACY = "ACCURACY"


class ServiceType(str, Enum):
    """Type of service in the system."""
    AGENT_ORCHESTRATOR = "AGENT_ORCHESTRATOR"
    MODEL_ORCHESTRATION = "MODEL_ORCHESTRATION"
    TOOL_INTEGRATION = "TOOL_INTEGRATION"
    PROJECT_COORDINATOR = "PROJECT_COORDINATOR"
    PLANNING_SYSTEM = "PLANNING_SYSTEM"
    SERVICE_INTEGRATION = "SERVICE_INTEGRATION"
    API_GATEWAY = "API_GATEWAY"
    WEB_DASHBOARD = "WEB_DASHBOARD"


class ServiceStatus(str, Enum):
    """Status of a service."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"


class WorkflowType(str, Enum):
    """Type of workflow."""
    PROJECT_PLANNING = "PROJECT_PLANNING"
    AGENT_TASK_EXECUTION = "AGENT_TASK_EXECUTION"
    TOOL_INTEGRATION = "TOOL_INTEGRATION"
    MODEL_EVALUATION = "MODEL_EVALUATION"
    DATA_PROCESSING = "DATA_PROCESSING"


class WorkflowStatus(str, Enum):
    """Status of a workflow."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MessageRole(str, Enum):
    """Role of a message in chat requests."""
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    FUNCTION = "FUNCTION"
    TOOL = "TOOL"


class ToolCategory(str, Enum):
    """Category of a tool."""
    UTILITY = "UTILITY"
    INTEGRATION = "INTEGRATION"
    ANALYSIS = "ANALYSIS"
    COMMUNICATION = "COMMUNICATION"
    DEVELOPMENT = "DEVELOPMENT"
    SECURITY = "SECURITY"
    CUSTOM = "CUSTOM"


class ExecutionStatus(str, Enum):
    """Status of a tool execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


# Map of enum classes by name for easy lookup
ENUM_MAP: Dict[str, type] = {
    "ProjectStatus": ProjectStatus,
    "AgentStatus": AgentStatus,
    "AgentType": AgentType,
    "TaskStatus": TaskStatus,
    "TaskPriority": TaskPriority,
    "ToolType": ToolType,
    "ToolStatus": ToolStatus,
    "ToolCategory": ToolCategory,
    "ExecutionStatus": ExecutionStatus,
    "ModelProvider": ModelProvider,
    "ModelStatus": ModelStatus,
    "ModelCapability": ModelCapability,
    "RequestType": RequestType,
    "HumanInteractionType": HumanInteractionType,
    "AuditAction": AuditAction,
    "UserRole": UserRole,
    "UserStatus": UserStatus,
    "DependencyType": DependencyType,
    "AnalyticsType": AnalyticsType,
    "ArtifactType": ArtifactType,
    "ResourceType": ResourceType,
    "OptimizationTarget": OptimizationTarget,
    "ServiceType": ServiceType,
    "ServiceStatus": ServiceStatus,
    "WorkflowType": WorkflowType,
    "WorkflowStatus": WorkflowStatus,
    "MessageRole": MessageRole,
}


def get_enum_by_name(enum_name: str) -> Optional[type]:
    """
    Get an enum class by name.
    
    Args:
        enum_name: The name of the enum class
        
    Returns:
        The enum class, or None if not found
    """
    return ENUM_MAP.get(enum_name)


def get_enum_values(enum_class: type) -> List[str]:
    """
    Get all values for an enum class.
    
    Args:
        enum_class: The enum class
        
    Returns:
        List of enum values
    """
    return [e.value for e in enum_class]


def get_enum_names(enum_class: type) -> List[str]:
    """
    Get all names for an enum class.
    
    Args:
        enum_class: The enum class
        
    Returns:
        List of enum names
    """
    return [e.name for e in enum_class]


def is_valid_enum_value(enum_class: type, value: str) -> bool:
    """
    Check if a value is valid for an enum class.
    
    Args:
        enum_class: The enum class
        value: The value to check
        
    Returns:
        True if the value is valid, False otherwise
    """
    return value in get_enum_values(enum_class)


def is_valid_enum_name(enum_class: type, name: str) -> bool:
    """
    Check if a name is valid for an enum class.
    
    Args:
        enum_class: The enum class
        name: The name to check
        
    Returns:
        True if the name is valid, False otherwise
    """
    return name.upper() in [e.name.upper() for e in enum_class]


def get_enum_from_value(enum_class: type, value: str) -> Optional[Enum]:
    """
    Get an enum instance from a value.
    
    Args:
        enum_class: The enum class
        value: The value to look up
        
    Returns:
        The enum instance, or None if not found
    """
    for e in enum_class:
        if e.value == value:
            return e
    return None


def get_enum_from_name(enum_class: type, name: str) -> Optional[Enum]:
    """
    Get an enum instance from a name.
    
    Args:
        enum_class: The enum class
        name: The name to look up
        
    Returns:
        The enum instance, or None if not found
    """
    try:
        return enum_class[name.upper()]
    except (KeyError, ValueError):
        return None
