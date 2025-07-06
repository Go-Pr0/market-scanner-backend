"""app/services/auth_service.py
Authentication service for JWT token management.
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.models.user import User, UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.user_db import user_db

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    def __init__(self):
        if JWT_SECRET_KEY == "your-secret-key-change-this-in-production":
            logger.warning("Using default JWT secret key. Please set JWT_SECRET_KEY environment variable in production.")
    
    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for a user."""
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "sub": str(user.id),  # Subject (user ID)
            "email": user.email,
            "full_name": user.full_name,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                return None
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a JWT token."""
        payload = self.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            return user_db.get_user_by_id(int(user_id))
        except (ValueError, TypeError):
            return None
    
    def register_user(self, user_create: UserCreate) -> TokenResponse:
        """Register a new user and return a token."""
        try:
            # Create the user
            user = user_db.create_user(user_create)
            
            # Generate access token
            access_token = self.create_access_token(user)
            
            # Create response
            user_response = UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=JWT_EXPIRATION_HOURS * 3600,  # Convert to seconds
                user=user_response
            )
        
        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise ValueError("Failed to register user")
    
    def login_user(self, user_login: UserLogin) -> TokenResponse:
        """Authenticate a user and return a token."""
        # Authenticate user
        user = user_db.authenticate_user(user_login.email, user_login.password)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Generate access token
        access_token = self.create_access_token(user)
        
        # Create response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,  # Convert to seconds
            user=user_response
        )
    
    def refresh_token(self, token: str) -> Optional[TokenResponse]:
        """Refresh an access token."""
        user = self.get_current_user(token)
        if not user:
            return None
        
        # Generate new access token
        access_token = self.create_access_token(user)
        
        # Create response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_EXPIRATION_HOURS * 3600,
            user=user_response
        )
    
    def is_email_whitelisted(self, email: str) -> bool:
        """Check if an email is whitelisted for registration."""
        return user_db.is_email_whitelisted(email)


# Global auth service instance
auth_service = AuthService()