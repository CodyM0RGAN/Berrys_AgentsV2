from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"
    VIEWER = "VIEWER"
    API = "API"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"


class Permission(str, Enum):
    CREATE_PROJECT = "CREATE_PROJECT"
    EDIT_PROJECT = "EDIT_PROJECT"
    DELETE_PROJECT = "DELETE_PROJECT"
    VIEW_PROJECT = "VIEW_PROJECT"
    
    CREATE_AGENT = "CREATE_AGENT"
    EDIT_AGENT = "EDIT_AGENT"
    DELETE_AGENT = "DELETE_AGENT"
    VIEW_AGENT = "VIEW_AGENT"
    
    CREATE_TASK = "CREATE_TASK"
    EDIT_TASK = "EDIT_TASK"
    DELETE_TASK = "DELETE_TASK"
    VIEW_TASK = "VIEW_TASK"
    
    CREATE_TOOL = "CREATE_TOOL"
    EDIT_TOOL = "EDIT_TOOL"
    DELETE_TOOL = "DELETE_TOOL"
    VIEW_TOOL = "VIEW_TOOL"
    
    MANAGE_USERS = "MANAGE_USERS"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"
    
    APPROVE_ACTIONS = "APPROVE_ACTIONS"
    EXECUTE_ACTIONS = "EXECUTE_ACTIONS"


class UserBase(BaseModel):
    """Base model for User with common attributes."""
    username: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    """Model for creating a new User."""
    password: str


class UserUpdate(BaseModel):
    """Model for updating an existing User."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserInDB(UserBase):
    """Model for User as stored in the database."""
    id: UUID = Field(default_factory=uuid4)
    password_hash: str
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class User(BaseModel):
    """Complete User model with all attributes (excluding password)."""
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserSummary(BaseModel):
    """Simplified User model for list views."""
    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    status: UserStatus

    class Config:
        orm_mode = True


class Token(BaseModel):
    """Model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenData(BaseModel):
    """Model for token payload data."""
    sub: str  # username
    exp: datetime
    permissions: List[Permission] = []
    is_admin: bool = False


class RolePermissions(BaseModel):
    """Model for role-based permissions."""
    role: UserRole
    permissions: List[Permission]


class UserPermissions(BaseModel):
    """Model for user-specific permissions."""
    user_id: UUID
    permissions: List[Permission]
    project_specific_permissions: Dict[UUID, List[Permission]] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    """Model for login requests."""
    username: str
    password: str


class PasswordResetRequest(BaseModel):
    """Model for password reset requests."""
    email: EmailStr


class PasswordReset(BaseModel):
    """Model for password reset."""
    token: str
    new_password: str
