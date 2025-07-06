"""app/services/migration_service.py
Migration service to handle transition from old authentication system to new JWT system.
"""

import os
import json
import logging
from typing import List, Dict, Any
from app.services.user_db import user_db
from app.services.ai_assistant_db import ai_assistant_db

logger = logging.getLogger(__name__)


class MigrationService:
    """Service to handle data migration from old system to new JWT-based system."""
    
    def __init__(self):
        self.old_users_file = "./data/users.json"
        self.old_ai_db = "./data/ai_assistant.db"
    
    def migrate_users_from_json(self) -> Dict[str, Any]:
        """Migrate users from old users.json file to new database."""
        migration_result = {
            "migrated_users": 0,
            "whitelisted_emails": 0,
            "errors": []
        }
        
        if not os.path.exists(self.old_users_file):
            logger.info("No old users.json file found, skipping user migration")
            return migration_result
        
        try:
            with open(self.old_users_file, 'r') as f:
                old_users = json.load(f)
            
            logger.info(f"Found {len(old_users)} users in old system")
            
            for user_data in old_users:
                email = user_data.get('email')
                password = user_data.get('password')
                
                if not email or not password:
                    migration_result["errors"].append(f"Invalid user data: {user_data}")
                    continue
                
                try:
                    # Add email to whitelist
                    user_db.add_email_to_whitelist(email)
                    migration_result["whitelisted_emails"] += 1
                    logger.info(f"Added {email} to whitelist")
                    
                    # Check if user already exists
                    existing_user = user_db.get_user_by_email(email)
                    if existing_user:
                        logger.info(f"User {email} already exists, skipping")
                        continue
                    
                    # Create user with migrated password (ensure minimum length)
                    from app.models.user import UserCreate
                    # Ensure password meets minimum requirements
                    if len(password) < 8:
                        password = password + "123"  # Pad short passwords
                        logger.warning(f"Password for {email} was too short, padded to meet requirements")
                    
                    user_create = UserCreate(
                        email=email,
                        password=password,
                        full_name=None
                    )
                    
                    user = user_db.create_user(user_create)
                    migration_result["migrated_users"] += 1
                    logger.info(f"Migrated user: {email}")
                    
                except Exception as e:
                    error_msg = f"Failed to migrate user {email}: {e}"
                    migration_result["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Backup old file
            backup_file = f"{self.old_users_file}.backup"
            os.rename(self.old_users_file, backup_file)
            logger.info(f"Backed up old users.json to {backup_file}")
            
        except Exception as e:
            error_msg = f"Failed to migrate users from JSON: {e}"
            migration_result["errors"].append(error_msg)
            logger.error(error_msg)
        
        return migration_result
    
    def migrate_ai_assistant_data(self) -> Dict[str, Any]:
        """Migrate AI assistant data to include user_id for existing chats."""
        migration_result = {
            "migrated_chats": 0,
            "errors": []
        }
        
        try:
            # Get all chat sessions without user_id (legacy data)
            with ai_assistant_db._get_connection() as conn:
                rows = conn.execute("""
                    SELECT id FROM chat_sessions 
                    WHERE user_id IS NULL OR user_id = 0
                """).fetchall()
                
                if not rows:
                    logger.info("No legacy chat sessions found")
                    return migration_result
                
                logger.info(f"Found {len(rows)} legacy chat sessions")
                
                # Assign legacy chats to the first user (if any exists)
                first_user = user_db.get_user_by_id(1)
                if not first_user:
                    # Create a default legacy user
                    user_db.add_email_to_whitelist("legacy@system.local")
                    from app.models.user import UserCreate
                    legacy_user_create = UserCreate(
                        email="legacy@system.local",
                        password="legacy_password_change_me",
                        full_name="Legacy System User"
                    )
                    first_user = user_db.create_user(legacy_user_create)
                    logger.info("Created legacy system user for old chats")
                
                # Update legacy chats to belong to first user
                conn.execute("""
                    UPDATE chat_sessions 
                    SET user_id = ? 
                    WHERE user_id IS NULL OR user_id = 0
                """, (first_user.id,))
                
                migration_result["migrated_chats"] = len(rows)
                conn.commit()
                logger.info(f"Migrated {len(rows)} legacy chats to user {first_user.email}")
                
        except Exception as e:
            error_msg = f"Failed to migrate AI assistant data: {e}"
            migration_result["errors"].append(error_msg)
            logger.error(error_msg)
        
        return migration_result
    
    def run_full_migration(self) -> Dict[str, Any]:
        """Run complete migration from old system to new JWT system."""
        logger.info("Starting full system migration")
        
        total_result = {
            "user_migration": {},
            "ai_migration": {},
            "success": False,
            "summary": {}
        }
        
        try:
            # Step 1: Migrate users
            logger.info("Step 1: Migrating users...")
            total_result["user_migration"] = self.migrate_users_from_json()
            
            # Step 2: Migrate AI assistant data
            logger.info("Step 2: Migrating AI assistant data...")
            total_result["ai_migration"] = self.migrate_ai_assistant_data()
            
            # Calculate summary
            total_result["summary"] = {
                "total_users_migrated": total_result["user_migration"]["migrated_users"],
                "total_emails_whitelisted": total_result["user_migration"]["whitelisted_emails"],
                "total_chats_migrated": total_result["ai_migration"]["migrated_chats"],
                "total_errors": (
                    len(total_result["user_migration"]["errors"]) + 
                    len(total_result["ai_migration"]["errors"])
                )
            }
            
            total_result["success"] = total_result["summary"]["total_errors"] == 0
            
            logger.info("Migration completed successfully")
            logger.info(f"Summary: {total_result['summary']}")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            total_result["success"] = False
            total_result["error"] = str(e)
        
        return total_result


# Global migration service instance
migration_service = MigrationService()