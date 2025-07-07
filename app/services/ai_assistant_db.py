"""app/services/ai_assistant_db.py
Database service for AI assistant chat system using SQLite.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging
import os

from app.models.ai_assistant import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class AIAssistantDB:
    """Database service for AI assistant chat system."""
    
    def __init__(self, db_path: str = "./data/ai_assistant.db"):
        self.db_path = db_path
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
            # Create chat_sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    status TEXT NOT NULL,
                    context_data TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create chat_messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (chat_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create trade_questions table for questionnaire data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    questions_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_email)
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id 
                ON chat_messages (chat_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp 
                ON chat_messages (timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at 
                ON chat_sessions (updated_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
                ON chat_sessions (user_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_questions_user_email 
                ON trade_questions (user_email)
            """)
            
            # Check if user_id column exists, if not add it (migration)
            cursor = conn.execute("PRAGMA table_info(chat_sessions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("Adding user_id column to chat_sessions table")
                conn.execute("ALTER TABLE chat_sessions ADD COLUMN user_id INTEGER")
                # Set a default user_id for existing sessions (will be 0 for legacy data)
                conn.execute("UPDATE chat_sessions SET user_id = 0 WHERE user_id IS NULL")
            
            conn.commit()
    
    def create_chat_session(
        self, 
        user_id: int,
        status: str, 
        context_data: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        chat_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO chat_sessions (id, user_id, title, status, context_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_id,
                user_id,
                title,
                status,
                json.dumps(context_data) if context_data else None,
                now,
                now
            ))
            conn.commit()
        
        return ChatSession(
            id=chat_id,
            title=title,
            status=status,
            context_data=context_data,
            created_at=now,
            updated_at=now,
            is_active=True
        )
    
    def get_chat_session(self, chat_id: str, user_id: Optional[int] = None) -> Optional[ChatSession]:
        """Get a chat session by ID, optionally filtered by user."""
        with self._get_connection() as conn:
            if user_id is not None:
                row = conn.execute("""
                    SELECT * FROM chat_sessions WHERE id = ? AND user_id = ? AND is_active = 1
                """, (chat_id, user_id)).fetchone()
            else:
                row = conn.execute("""
                    SELECT * FROM chat_sessions WHERE id = ? AND is_active = 1
                """, (chat_id,)).fetchone()
            
            if not row:
                return None
            
            context_data = None
            if row['context_data']:
                try:
                    context_data = json.loads(row['context_data'])
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse context_data for chat {chat_id}")
            
            return ChatSession(
                id=row['id'],
                title=row['title'],
                status=row['status'],
                context_data=context_data,
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                is_active=bool(row['is_active'])
            )
    
    def update_chat_session_title(self, chat_id: str, title: str) -> bool:
        """Update chat session title."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE chat_sessions 
                SET title = ?, updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (title, datetime.utcnow(), chat_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_chat_session_timestamp(self, chat_id: str) -> bool:
        """Update chat session updated_at timestamp."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE chat_sessions 
                SET updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (datetime.utcnow(), chat_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_message(
        self, 
        chat_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a message to a chat session."""
        now = datetime.utcnow()
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO chat_messages (chat_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                chat_id,
                role,
                content,
                now,
                json.dumps(metadata) if metadata else None
            ))
            message_id = cursor.lastrowid
            conn.commit()
        
        # Update chat session timestamp
        self.update_chat_session_timestamp(chat_id)
        
        return ChatMessage(
            id=message_id,
            chat_id=chat_id,
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata
        )
    
    def get_chat_messages(self, chat_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get messages for a chat session."""
        query = """
            SELECT * FROM chat_messages 
            WHERE chat_id = ? 
            ORDER BY timestamp ASC
        """
        params = [chat_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            
            messages = []
            for row in rows:
                metadata = None
                if row['metadata']:
                    try:
                        metadata = json.loads(row['metadata'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata for message {row['id']}")
                
                messages.append(ChatMessage(
                    id=row['id'],
                    chat_id=row['chat_id'],
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=metadata
                ))
            
            return messages
    
    def get_recent_chats(self, user_id: int, limit: int = 50) -> List[ChatSession]:
        """Get recent chat sessions for a user ordered by updated_at."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM chat_sessions 
                WHERE user_id = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            chats = []
            for row in rows:
                context_data = None
                if row['context_data']:
                    try:
                        context_data = json.loads(row['context_data'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse context_data for chat {row['id']}")
                
                chats.append(ChatSession(
                    id=row['id'],
                    title=row['title'],
                    status=row['status'],
                    context_data=context_data,
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    is_active=bool(row['is_active'])
                ))
            
            return chats
    
    def delete_chat_session(self, chat_id: str) -> bool:
        """Soft delete a chat session."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE chat_sessions 
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.utcnow(), chat_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_chat_history(self, chat_id: str, user_id: Optional[int] = None) -> Optional[Tuple[ChatSession, List[ChatMessage]]]:
        """Get complete chat history (session + messages)."""
        chat_session = self.get_chat_session(chat_id, user_id)
        if not chat_session:
            return None
        
        messages = self.get_chat_messages(chat_id)
        return chat_session, messages
    
    def get_user_questionnaire(self, user_email: str) -> Optional[List[Dict[str, str]]]:
        """Get user's questionnaire data from trade_questions table."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT questions_json FROM trade_questions 
                WHERE user_email = ?
            """, (user_email,)).fetchone()
            
            if not row or not row['questions_json']:
                return None
            
            try:
                questions_data = json.loads(row['questions_json'])
                # Ensure it's a list of question/answer pairs
                if isinstance(questions_data, list):
                    return questions_data
                else:
                    logger.warning(f"Invalid questionnaire format for user {user_email}")
                    return None
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse questionnaire JSON for user {user_email}")
                return None
    
    def save_user_questionnaire(self, user_email: str, questions: List[Dict[str, str]]) -> bool:
        """Save or update user's questionnaire data."""
        now = datetime.utcnow()
        questions_json = json.dumps(questions)
        
        with self._get_connection() as conn:
            # Try to update existing record first
            cursor = conn.execute("""
                UPDATE trade_questions 
                SET questions_json = ?, updated_at = ?
                WHERE user_email = ?
            """, (questions_json, now, user_email))
            
            if cursor.rowcount == 0:
                # Insert new record if update didn't affect any rows
                conn.execute("""
                    INSERT INTO trade_questions (user_email, questions_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (user_email, questions_json, now, now))
            
            conn.commit()
            return True


# Global database instance
ai_assistant_db = AIAssistantDB()