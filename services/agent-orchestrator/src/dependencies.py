from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from typing import Optional, Dict, Any, AsyncGenerator

from .database import get_db
from shared.utils.src.messaging import get_event_bus, get_command_bus

from .config import config, AgentOrchestratorConfig, get_settings
from .exceptions import AuthenticationError
from .models.api import UserInfo
from .services.agent_service import AgentService
from .services.template_service import TemplateService
from .services.lifecycle_manager import LifecycleManager
from .services.state_manager import StateManager
from .services.communication_service import CommunicationService
from .services.enhanced_communication_service import EnhancedCommunicationService
from .services.execution_service import ExecutionService
from .services.human_interaction_service import HumanInteractionService
from .services.communication.alerting_service import AlertingService

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: AgentOrchestratorConfig = Depends(get_settings),
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
    settings: AgentOrchestratorConfig = Depends(get_settings),
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


async def get_agent_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[AgentService, None]:
    """
    Dependency to get the agent service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        AgentService: Agent service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = AgentService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


async def get_template_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[TemplateService, None]:
    """
    Dependency to get the template service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        TemplateService: Template service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = TemplateService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


async def get_lifecycle_manager(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[LifecycleManager, None]:
    """
    Dependency to get the lifecycle manager.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        LifecycleManager: Lifecycle manager instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    manager = LifecycleManager(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield manager


async def get_state_manager(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[StateManager, None]:
    """
    Dependency to get the state manager.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        StateManager: State manager instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    manager = StateManager(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield manager


async def get_communication_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[CommunicationService, None]:
    """
    Dependency to get the communication service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        CommunicationService: Communication service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = CommunicationService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


async def get_enhanced_communication_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[EnhancedCommunicationService, None]:
    """
    Dependency to get the enhanced communication service.
    
    This service extends the basic CommunicationService with advanced routing and
    prioritization capabilities provided by the CommunicationHub.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        EnhancedCommunicationService: Enhanced communication service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = EnhancedCommunicationService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


async def get_alerting_service(
    enhanced_communication_service: EnhancedCommunicationService = Depends(get_enhanced_communication_service),
) -> AsyncGenerator[AlertingService, None]:
    """
    Dependency to get the alerting service.
    
    This service monitors metrics and triggers alerts when thresholds are exceeded.
    It is part of the Agent Communication Hub monitoring and analytics system.
    
    Args:
        enhanced_communication_service: Enhanced communication service instance
        
    Returns:
        AlertingService: Alerting service instance
    """
    # The alerting service is initialized and managed by the enhanced communication service
    alerting_service = enhanced_communication_service.alerting_service
    
    if alerting_service is None:
        raise RuntimeError("Alerting service not initialized in enhanced communication service")
    
    yield alerting_service


async def get_human_interaction_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
) -> AsyncGenerator[HumanInteractionService, None]:
    """
    Dependency to get the human interaction service.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        HumanInteractionService: Human interaction service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = HumanInteractionService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
    )
    
    yield service


async def get_execution_service(
    db: AsyncSession = Depends(get_db),
    settings: AgentOrchestratorConfig = Depends(get_settings),
    human_interaction_service: HumanInteractionService = Depends(get_human_interaction_service),
) -> AsyncGenerator[ExecutionService, None]:
    """
    Dependency to get the execution service.
    
    Args:
        db: Database session
        settings: Application settings
        human_interaction_service: Human interaction service
        
    Returns:
        ExecutionService: Execution service instance
    """
    event_bus = get_event_bus()
    command_bus = get_command_bus()
    
    service = ExecutionService(
        db=db,
        event_bus=event_bus,
        command_bus=command_bus,
        settings=settings,
        human_interaction_service=human_interaction_service,
    )
    
    yield service
