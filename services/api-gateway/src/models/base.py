from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func
from datetime import datetime
import re

from ..database import Base


class BaseModel(Base):
    """
    Base model for all database models.
    """
    
    __abstract__ = True
    
    # Automatically convert CamelCase class name to snake_case table name
    @declared_attr
    def __tablename__(cls):
        # Convert CamelCase to snake_case
        name = re.sub('(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Remove "model" suffix if present
        if name.endswith('_model'):
            name = name[:-6]
        return name
    
    # Common columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
