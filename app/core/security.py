from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.models.user import User
from app.services.auth_service import auth_service

# Setup logging
logger = logging.getLogger(__name__)

# Security scheme for API endpoints
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If the token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """
    Get the current authenticated user from JWT token (optional).
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        User or None: The authenticated user or None if not authenticated
    """
    if not credentials:
        return None
    
    user = auth_service.get_current_user(credentials.credentials)
    if not user or not user.is_active:
        return None
    
    return user


# FastAPI dependency for route protection
async def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency that requires authentication.
    Use this as a dependency in your route handlers.
    
    Returns:
        User: The authenticated user
    """
    return current_user

 