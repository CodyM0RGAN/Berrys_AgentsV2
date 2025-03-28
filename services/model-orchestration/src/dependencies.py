from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional, Dict, Any

from .database import get_db
from shared.utils.src.messaging import get_event_bus, get_command_bus

from .config import ModelOrchestrationConfig, config, get_settings
from .exceptions import AuthenticationError
from shared.models.src.enums import ModelProvider
from .services.model_service import ModelService
from .services.performance_tracker import PerformanceTracker
from .providers.provider_factory import get_provider_factory

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token", auto_error=False)


class UserInfo:
    """
    User information model.
    """
    def __init__(
        self,
        id: str,
        username: str,
        email: Optional[str] = None,
        is_admin: bool = False,
        roles: list[str] = None,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.roles = roles or []


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: ModelOrchestrationConfig = Depends(get_settings),
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
    if token is None:
        raise AuthenticationError("Authentication required")
    
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
    settings: ModelOrchestrationConfig = Depends(get_settings),
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


async def get_provider_factory_dependency(
    settings: ModelOrchestrationConfig = Depends(get_settings),
):
    """
    Dependency to get the provider factory.
    
    Args:
        settings: Application settings
        
    Returns:
        ProviderFactory: Provider factory instance
    """
    return get_provider_factory(settings)


async def get_performance_tracker(
    db: AsyncSession = Depends(get_db),
    settings: ModelOrchestrationConfig = Depends(get_settings),
) -> PerformanceTracker:
    """
    Dependency to get the performance tracker.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        PerformanceTracker: Performance tracker instance
    """
    event_bus = get_event_bus()
    
    return PerformanceTracker(
        db=db,
        event_bus=event_bus,
        settings=settings,
    )


async def get_model_service(
    db: AsyncSession = Depends(get_db),
    settings: ModelOrchestrationConfig = Depends(get_settings),
    provider_factory = Depends(get_provider_factory_dependency),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker),
) -> ModelService:
    """
    Dependency to get the model service.
    
    Args:
        db: Database session
        settings: Application settings
        provider_factory: Provider factory
        performance_tracker: Performance tracker
        
    Returns:
        ModelService: Model service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    return ModelService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
        provider_factory=provider_factory,
        performance_tracker=performance_tracker,
    )
