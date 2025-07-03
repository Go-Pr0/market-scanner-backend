from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Security scheme for API endpoints
security = HTTPBearer(auto_error=False)

def get_access_token():
    """Get the access token from environment variables."""
    return os.getenv("ACCESS_PASSWORD")

async def verify_access_token(request: Request) -> bool:
    """
    Verify the access token from the request headers.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        bool: True if the token is valid, False otherwise
        
    Raises:
        HTTPException: If the token is invalid or missing
    """
    # Get the access token from environment
    expected_token = get_access_token()
    
    if not expected_token:
        logger.critical("FATAL: ACCESS_PASSWORD environment variable is not set. API cannot start securely.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API is not configured for authentication. Please contact the administrator."
        )
    
    # Check for the custom header
    access_token = request.headers.get("X-Access-Token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access token required"
        )
    
    if access_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid access token"
        )
    
    return True

# FastAPI dependency for route protection
async def require_auth(request: Request):
    """
    FastAPI dependency that requires authentication.
    Use this as a dependency in your route handlers.
    """
    await verify_access_token(request)
    return True 