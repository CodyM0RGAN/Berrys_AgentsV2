"""
Enums for the Agent Orchestrator service.

This module provides enums for the Agent Orchestrator service.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any


class ExecutionState(str, Enum):
    """
    Execution state enum.
    """
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentStateDetail(str, Enum):
    """
    Agent state detail enum.
    
    This enum provides more detailed state information beyond the basic
    AgentStatus (ACTIVE, INACTIVE, etc.) from shared.models.src.enums.
    """
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    TERMINATED = "TERMINATED"
