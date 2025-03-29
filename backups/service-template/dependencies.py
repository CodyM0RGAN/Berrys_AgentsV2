from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional, Dict, Any

from shared.utils.src.database import get_db
from shared.utils.src.messaging import get_event_bus, get_command_bus

from .config import get_settings, Settings
from .exceptions import AuthenticationError
from .models.api import UserInfo
from .services.resource_service import ResourceService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> UserInfo:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        settings: Application settings
        
    Returns:
        UserInfo: Current user information
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        
        # Extract user information
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token")
        
        # Create user info
        user_info = UserInfo(
            id=user_id,
            username=payload.get("username", ""),
            email=payload.get("email"),
            is_admin=payload.get("is_admin", False),
            roles=payload.get("roles", []),
        )
        
        return user_info
    except JWTError:
        raise AuthenticationError("Invalid token")


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> Optional[UserInfo]:
    """
    Dependency to get the current user if authenticated, or None if not.
    
    Args:
        token: JWT token from Authorization header (optional)
        settings: Application settings
        
    Returns:
        Optional[UserInfo]: Current user information or None
    """
    if token is None:
        return None
        
    try:
        return await get_current_user(token, settings)
    except AuthenticationError:
        return None


async def get_admin_user(
    user: UserInfo = Depends(get_current_user),
) -> UserInfo:
    """
    Dependency to get the current user and verify they are an admin.
    
    Args:
        user: Current authenticated user
        
    Returns:
        UserInfo: Current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


async def get_resource_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ResourceService:
    """
    Dependency to get the resource service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        ResourceService: Resource service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    return ResourceService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
