"""
Execution service for Agent Orchestrator.

This module re-exports the modular implementation of ExecutionService to maintain
backward compatibility with existing code.
"""

from .execution.service import ExecutionService

__all__ = ["ExecutionService"]
