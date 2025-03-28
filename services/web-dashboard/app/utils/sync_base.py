"""
Synchronous base model for SQLAlchemy models in the web dashboard application.

This module provides a synchronous version of the SQLAlchemyBaseModelMixin from the shared models package.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, func, inspect
from sqlalchemy.dialects.postgresql import UUID

class SQLAlchemyBaseModelMixin:
    """
    Mixin class for all SQLAlchemy models.
    
    Provides common fields and functionality for all models.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def to_dict(self) -> dict:
        """
        Convert the model instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the model
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SQLAlchemyBaseModelMixin':
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
            
        Returns:
            SQLAlchemyBaseModelMixin: Model instance
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__table__.columns})
    
    def update_from_dict(self, data: dict) -> None:
        """
        Update the model instance from a dictionary.
        
        Args:
            data: Dictionary containing model data
        """
        for key, value in data.items():
            if hasattr(self, key) and key in self.__table__.columns:
                setattr(self, key, value)
