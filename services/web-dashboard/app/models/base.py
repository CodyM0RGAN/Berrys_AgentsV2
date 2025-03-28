"""
Base model for SQLAlchemy models in the web dashboard application.

This module defines the BaseModel class that all SQLAlchemy models should inherit from.
It uses the shared base model from the shared models package.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import logging
import traceback

from app import db
from app.utils.sync_base import SQLAlchemyBaseModelMixin

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Using SQLAlchemyBaseModelMixin from app.utils.sync_base")

class BaseModel(SQLAlchemyBaseModelMixin, db.Model):
    """
    Base model for all SQLAlchemy models in the web dashboard.
    
    Inherits from SQLAlchemyBaseModelMixin to provide common fields and functionality,
    and from db.Model to integrate with Flask-SQLAlchemy.
    """
    __abstract__ = True
    
    def __init__(self, *args, **kwargs):
        """Initialize a new model instance with logging."""
        logger.info("Creating new %s instance", self.__class__.__name__)
        try:
            super().__init__(*args, **kwargs)
            logger.info("%s instance created successfully", self.__class__.__name__)
        except Exception as e:
            logger.error("Error creating %s instance: %s", self.__class__.__name__, str(e), exc_info=True)
            logger.error("Stack trace: %s", ''.join(traceback.format_stack()))
            raise
    
    def to_dict(self):
        """Convert the model instance to a dictionary with logging."""
        logger.info("Converting %s instance to dictionary", self.__class__.__name__)
        try:
            result = super().to_dict()
            logger.info("%s instance converted to dictionary successfully", self.__class__.__name__)
            return result
        except Exception as e:
            logger.error("Error converting %s instance to dictionary: %s", 
                      self.__class__.__name__, str(e), exc_info=True)
            raise
