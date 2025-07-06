"""app/routers/auth.py
Authentication router for user registration, login, and management.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.concurrency import run_in_threadpool

from app.core.security import require_auth, get_current_user
from app.models.user import (
    UserCreate, 
    UserLogin, 
    TokenResponse, 
    UserResponse, 
    PasswordChange, 
    UserUpdate,
    WhitelistEmailCreate,
    WhitelistEmailResponse,
    User
)
from app.services.auth_service import auth_service
from app.services.user_db import user_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(user_create: UserCreate):
    """Register a new user."""
    try:
        token_response = await run_in_threadpool(
            auth_service.register_user,
            user_create
        )
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    """Authenticate a user and return a JWT token."""
    try:
        token_response = await run_in_threadpool(
            auth_service.login_user,
            user_login
        )
        return token_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh the current user's access token."""
    try:
        # Create a new token for the current user
        token_response = TokenResponse(
            access_token=auth_service.create_access_token(current_user),
            token_type="bearer",
            expires_in=24 * 3600,  # 24 hours in seconds
            user=UserResponse(
                id=current_user.id,
                email=current_user.email,
                full_name=current_user.full_name,
                is_active=current_user.is_active,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        )
        return token_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user information."""
    try:
        updated_user = await run_in_threadpool(
            user_db.update_user,
            current_user.id,
            user_update.full_name,
            user_update.email
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change current user's password."""
    try:
        success = await run_in_threadpool(
            user_db.change_password,
            current_user.id,
            password_change.current_password,
            password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/check-email")
async def check_email_whitelist(email_check: dict):
    """Check if an email is whitelisted for registration."""
    email = email_check.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    is_whitelisted = await run_in_threadpool(
        auth_service.is_email_whitelisted,
        email
    )
    
    return {"email": email, "is_whitelisted": is_whitelisted}


# Admin endpoints for managing whitelist (require authentication)
@router.get("/whitelist", response_model=List[WhitelistEmailResponse])
async def get_whitelist_emails(current_user: User = Depends(get_current_user)):
    """Get all whitelisted emails (admin only)."""
    try:
        emails = await run_in_threadpool(user_db.get_whitelist_emails)
        return [
            WhitelistEmailResponse(
                id=email.id,
                email=email.email,
                added_by=email.added_by,
                created_at=email.created_at,
                is_active=email.is_active
            )
            for email in emails
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve whitelist"
        )


@router.post("/whitelist", response_model=WhitelistEmailResponse)
async def add_email_to_whitelist(
    email_create: WhitelistEmailCreate,
    current_user: User = Depends(get_current_user)
):
    """Add an email to the whitelist (admin only)."""
    try:
        whitelist_email = await run_in_threadpool(
            user_db.add_email_to_whitelist,
            email_create.email,
            current_user.id
        )
        
        return WhitelistEmailResponse(
            id=whitelist_email.id,
            email=whitelist_email.email,
            added_by=whitelist_email.added_by,
            created_at=whitelist_email.created_at,
            is_active=whitelist_email.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add email to whitelist"
        )


@router.delete("/whitelist/{email}")
async def remove_email_from_whitelist(
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Remove an email from the whitelist (admin only)."""
    try:
        success = await run_in_threadpool(
            user_db.remove_email_from_whitelist,
            email
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found in whitelist"
            )
        
        return {"message": "Email removed from whitelist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove email from whitelist"
        )