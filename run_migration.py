#!/usr/bin/env python3
"""
Migration script to transition from old authentication system to new JWT-based system.
This script should be run once to migrate existing data.
"""

import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.migration_service import migration_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run the complete migration process."""
    logger.info("=" * 60)
    logger.info("STARTING MIGRATION FROM OLD SYSTEM TO JWT-BASED AUTHENTICATION")
    logger.info("=" * 60)
    
    try:
        # Run full migration
        result = migration_service.run_full_migration()
        
        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION RESULTS")
        logger.info("=" * 60)
        
        if result["success"]:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.error("❌ Migration failed!")
            if "error" in result:
                logger.error(f"Error: {result['error']}")
        
        # Display summary
        summary = result.get("summary", {})
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"   Users migrated: {summary.get('total_users_migrated', 0)}")
        logger.info(f"   Emails whitelisted: {summary.get('total_emails_whitelisted', 0)}")
        logger.info(f"   Chats migrated: {summary.get('total_chats_migrated', 0)}")
        logger.info(f"   Total errors: {summary.get('total_errors', 0)}")
        
        # Display errors if any
        user_errors = result.get("user_migration", {}).get("errors", [])
        ai_errors = result.get("ai_migration", {}).get("errors", [])
        
        if user_errors:
            logger.warning(f"\n⚠️  User migration errors:")
            for error in user_errors:
                logger.warning(f"   - {error}")
        
        if ai_errors:
            logger.warning(f"\n⚠️  AI migration errors:")
            for error in ai_errors:
                logger.warning(f"   - {error}")
        
        logger.info("\n" + "=" * 60)
        logger.info("NEXT STEPS")
        logger.info("=" * 60)
        logger.info("1. Start the FastAPI server: python main.py")
        logger.info("2. Test login with migrated users")
        logger.info("3. Add new emails to whitelist as needed")
        logger.info("4. Update frontend to use JWT authentication")
        
        return 0 if result["success"] else 1
        
    except Exception as e:
        logger.error(f"❌ Migration failed with exception: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)