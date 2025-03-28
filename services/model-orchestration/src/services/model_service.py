"""
Model service module.

This module is a compatibility layer that imports and re-exports the ModelService class
from the modular implementation.
"""

from .model_service.model_service import ModelService

__all__ = ["ModelService"]
