"""app/services/user_db.py
Database service for user management and authentication.
"""

import sqlite3
import bcrypt
from datetime import datetime
from typing import List, Optional, Tuple
from contextlib import contextmanager
import logging
import os

from app.core.config import config
from app.models.user import User, UserCreate, WhitelistEmail

logger = logging.getLogger(__name__)


class UserDB:
    """Database service for user management."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.USER_DB_PATH
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create email whitelist table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    added_by INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (added_by) REFERENCES users (id)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users (email)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_active 
                ON users (is_active)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_whitelist_email 
                ON email_whitelist (email)
            """)
            
            conn.commit()
    

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def is_email_whitelisted(self, email: str) -> bool:
        """Check if an email is in the whitelist."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT id FROM email_whitelist 
                WHERE email = ? AND is_active = 1
            """, (email.lower(),)).fetchone()
            return row is not None
    
    def add_email_to_whitelist(self, email: str, added_by: Optional[int] = None) -> WhitelistEmail:
        """Add an email to the whitelist."""
        now = datetime.utcnow()
        
        with self._get_connection() as conn:
            # Check if already exists
            existing = conn.execute("""
                SELECT * FROM email_whitelist WHERE email = ?
            """, (email.lower(),)).fetchone()
            
            if existing:
                # Reactivate if inactive
                if not existing['is_active']:
                    conn.execute("""
                        UPDATE email_whitelist 
                        SET is_active = 1, updated_at = ?
                        WHERE email = ?
                    """, (now, email.lower()))
                    conn.commit()
                
                return WhitelistEmail(
                    id=existing['id'],
                    email=existing['email'],
                    added_by=existing['added_by'],
                    created_at=datetime.fromisoformat(existing['created_at']),
                    is_active=True
                )
            else:
                # Insert new
                cursor = conn.execute("""
                    INSERT INTO email_whitelist (email, added_by, created_at)
                    VALUES (?, ?, ?)
                """, (email.lower(), added_by, now))
                whitelist_id = cursor.lastrowid
                conn.commit()
                
                return WhitelistEmail(
                    id=whitelist_id,
                    email=email.lower(),
                    added_by=added_by,
                    created_at=now,
                    is_active=True
                )
    
    def remove_email_from_whitelist(self, email: str) -> bool:
        """Remove an email from the whitelist (soft delete)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE email_whitelist 
                SET is_active = 0
                WHERE email = ?
            """, (email.lower(),))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_whitelist_emails(self) -> List[WhitelistEmail]:
        """Get all active whitelist emails."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM email_whitelist 
                WHERE is_active = 1
                ORDER BY created_at DESC
            """).fetchall()
            
            emails = []
            for row in rows:
                emails.append(WhitelistEmail(
                    id=row['id'],
                    email=row['email'],
                    added_by=row['added_by'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    is_active=bool(row['is_active'])
                ))
            
            return emails
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if email is whitelisted
        if not self.is_email_whitelisted(user_create.email):
            raise ValueError("Email is not whitelisted for registration")
        
        # Check if user already exists
        if self.get_user_by_email(user_create.email):
            raise ValueError("User with this email already exists")
        
        now = datetime.utcnow()
        password_hash = self._hash_password(user_create.password)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO users (email, password_hash, full_name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_create.email.lower(),
                password_hash,
                user_create.full_name,
                now,
                now
            ))
            user_id = cursor.lastrowid
            conn.commit()
        
        return User(
            id=user_id,
            email=user_create.email.lower(),
            full_name=user_create.full_name,
            is_active=True,
            created_at=now,
            updated_at=now
        )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM users WHERE email = ? AND is_active = 1
            """, (email.lower(),)).fetchone()
            
            if not row:
                return None
            
            return User(
                id=row['id'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM users WHERE id = ? AND is_active = 1
            """, (user_id,)).fetchone()
            
            if not row:
                return None
            
            return User(
                id=row['id'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM users WHERE email = ? AND is_active = 1
            """, (email.lower(),)).fetchone()
            
            if not row:
                return None
            
            if not self._verify_password(password, row['password_hash']):
                return None
            
            return User(
                id=row['id'],
                email=row['email'],
                full_name=row['full_name'],
                is_active=bool(row['is_active']),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
    
    def update_user(self, user_id: int, full_name: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        """Update user information."""
        now = datetime.utcnow()
        
        with self._get_connection() as conn:
            # Build dynamic update query
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = ?")
                params.append(full_name)
            
            if email is not None:
                # Check if new email is whitelisted
                if not self.is_email_whitelisted(email):
                    raise ValueError("New email is not whitelisted")
                updates.append("email = ?")
                params.append(email.lower())
            
            if not updates:
                return self.get_user_by_id(user_id)
            
            updates.append("updated_at = ?")
            params.append(now)
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor = conn.execute(query, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                return self.get_user_by_id(user_id)
            return None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        with self._get_connection() as conn:
            # Get current password hash
            row = conn.execute("""
                SELECT password_hash FROM users WHERE id = ? AND is_active = 1
            """, (user_id,)).fetchone()
            
            if not row:
                return False
            
            # Verify current password
            if not self._verify_password(current_password, row['password_hash']):
                return False
            
            # Update password
            new_password_hash = self._hash_password(new_password)
            cursor = conn.execute("""
                UPDATE users 
                SET password_hash = ?, updated_at = ?
                WHERE id = ?
            """, (new_password_hash, datetime.utcnow(), user_id))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user (soft delete)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE users 
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow(), user_id))
            conn.commit()
            return cursor.rowcount > 0


# Global database instance
user_db = UserDB()