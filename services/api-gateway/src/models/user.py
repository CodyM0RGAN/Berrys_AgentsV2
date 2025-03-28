from sqlalchemy import Column, String, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class UserModel(BaseModel):
    """
    SQLAlchemy model for users.
    """
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(100), nullable=False)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default="USER")
    status = Column(String(20), nullable=False, default="ACTIVE")
    permissions = Column(JSON, nullable=True)
    
    # Relationships
    projects = relationship("ProjectModel", back_populates="owner")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', role='{self.role}')>"
