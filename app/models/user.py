"""app/models/user.py
User management models for JWT authentication system.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User model."""
    id: Optional[int] = None
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class WhitelistEmail(BaseModel):
    """Email whitelist model."""
    id: Optional[int] = None
    email: EmailStr
    added_by: Optional[int] = None
    created_at: Optional[datetime] = None
    is_active: bool = True


class WhitelistEmailCreate(BaseModel):
    """Email whitelist creation model."""
    email: EmailStr


class WhitelistEmailResponse(BaseModel):
    """Email whitelist response model."""
    id: int
    email: EmailStr
    added_by: Optional[int] = None
    created_at: datetime
    is_active: bool


class PasswordChange(BaseModel):
    """Password change model."""
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class EmailCheckRequest(BaseModel):
    """Email check request model."""
    email: EmailStr


class EmailCheckResponse(BaseModel):
    """Email check response model."""
    email: EmailStr
    is_whitelisted: bool