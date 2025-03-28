import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging
from uuid import UUID

from shared.models.src.user import User, TokenData, Permission

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), user_service=None) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: JWT token
        user_service: User service for database operations
        
    Returns:
        User: Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(
            sub=username,
            exp=datetime.fromtimestamp(payload.get("exp")),
            permissions=payload.get("permissions", []),
            is_admin=payload.get("is_admin", False)
        )
    except JWTError:
        logger.error("JWT token error")
        raise credentials_exception
        
    if user_service is None:
        # This is a placeholder for when we don't have a user service
        # In a real implementation, we would fetch the user from the database
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User service not provided"
        )
        
    user = await user_service.get_user_by_username(username=token_data.sub)
    
    if user is None:
        logger.error(f"User not found: {username}")
        raise credentials_exception
        
    return user


def check_permission(required_permission: Permission, token_data: TokenData) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        required_permission: Permission to check
        token_data: Token data with user permissions
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    if token_data.is_admin:
        return True
        
    return required_permission in token_data.permissions


def get_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get token data from a JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        TokenData: Token data
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = TokenData(
            sub=username,
            exp=datetime.fromtimestamp(payload.get("exp")),
            permissions=payload.get("permissions", []),
            is_admin=payload.get("is_admin", False)
        )
        
        return token_data
    except JWTError:
        logger.error("JWT token error")
        raise credentials_exception


def require_permission(required_permission: Permission):
    """
    Dependency for requiring a specific permission.
    
    Args:
        required_permission: Permission to require
        
    Returns:
        function: Dependency function
    """
    def dependency(token_data: TokenData = Depends(get_token_data)):
        if not check_permission(required_permission, token_data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions: {required_permission}"
            )
        return token_data
    return dependency


def require_admin():
    """
    Dependency for requiring admin privileges.
    
    Returns:
        function: Dependency function
    """
    def dependency(token_data: TokenData = Depends(get_token_data)):
        if not token_data.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return token_data
    return dependency
