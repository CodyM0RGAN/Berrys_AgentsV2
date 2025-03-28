"""
User model for the web dashboard application.

This module defines the User model for authentication and authorization.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

# Import shared Pydantic models for API contracts
from shared.models.src.user import User as SharedUserModel, UserRole, UserStatus, UserSummary

from app.models.base import BaseModel

class User(BaseModel, UserMixin):
    """
    User model for authentication and authorization.
    
    Attributes:
        id: The user's unique identifier (UUID)
        email: The user's email address (used for login)
        username: The user's username
        name: The user's full name
        password_hash: The hashed password
        role: The user's role (admin, user, etc.)
        status: The user's status (active, inactive, etc.)
        is_active: Whether the user account is active
    """
    __tablename__ = 'user'  # Singular table name per SQLAlchemy guide
    
    # Override id from BaseModel to add docstring
    id = Column(BaseModel.id.type, primary_key=True, default=BaseModel.id.default.arg)
    
    # User attributes
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False, default='USER')
    status = Column(String(20), nullable=False, default='ACTIVE')
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    
    def __init__(self, email, username, name, password, role='USER', status='ACTIVE'):
        """
        Initialize a new User.
        
        Args:
            email: The user's email address
            username: The user's username
            name: The user's full name
            password: The plaintext password (will be hashed)
            role: The user's role (default: 'USER')
            status: The user's status (default: 'ACTIVE')
        """
        self.email = email
        self.username = username
        self.name = name
        self.set_password(password)
        self.role = role
        self.status = status
    
    def set_password(self, password):
        """
        Set the user's password (hashed).
        
        Args:
            password: The plaintext password to hash
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: The plaintext password to check
            
        Returns:
            True if the password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """
        Check if the user has admin role.
        
        Returns:
            True if the user is an admin, False otherwise
        """
        return self.role == 'ADMIN'
    
    def get_id(self):
        """
        Get the user ID as a string.
        
        Required by Flask-Login.
        
        Returns:
            The user ID as a string
        """
        return str(self.id)
    
    def to_api_model(self) -> SharedUserModel:
        """
        Convert to shared API model.
        
        Returns:
            A SharedUserModel instance with this user's data
        """
        return SharedUserModel(
            id=self.id,
            username=self.username,
            email=self.email,
            is_active=self.is_active,
            is_admin=self.is_admin(),
            role=UserRole(self.role),
            status=UserStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    def to_summary(self) -> UserSummary:
        """
        Convert to user summary model.
        
        Returns:
            A UserSummary instance with this user's data
        """
        return UserSummary(
            id=self.id,
            username=self.username,
            email=self.email,
            role=UserRole(self.role),
            status=UserStatus(self.status)
        )
    
    @classmethod
    def from_api_model(cls, api_model: SharedUserModel, password: str = None) -> 'User':
        """
        Create from shared API model.
        
        Args:
            api_model: The SharedUserModel to convert
            password: Optional password to set (if not provided, a random one will be generated)
            
        Returns:
            A new User instance
        """
        import secrets
        import string
        
        # Generate a random password if none provided
        if password is None:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        return cls(
            email=api_model.email,
            username=api_model.username,
            name=api_model.username,  # Use username as name if not provided
            password=password,
            role=api_model.role.value,
            status=api_model.status.value
        )
    
    def __repr__(self):
        """
        Get a string representation of the User.
        
        Returns:
            A string representation of the User
        """
        return f'<User {self.email}>'
