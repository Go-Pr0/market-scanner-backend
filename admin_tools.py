#!/usr/bin/env python3
"""
Admin tools for managing the JWT authentication system.
Provides command-line interface for user and whitelist management.
"""

import sys
import os
import argparse
import getpass
from typing import List, Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.user_db import user_db
from app.services.auth_service import auth_service
from app.models.user import UserCreate


class AdminTools:
    """Admin tools for user and whitelist management."""
    
    def list_users(self):
        """List all users in the system."""
        print("\n📋 USERS IN SYSTEM:")
        print("-" * 60)
        
        # Get all whitelisted emails and check which have accounts
        whitelist_emails = user_db.get_whitelist_emails()
        
        for email_obj in whitelist_emails:
            user = user_db.get_user_by_email(email_obj.email)
            if user:
                status = "✅ ACTIVE" if user.is_active else "❌ INACTIVE"
                print(f"ID: {user.id:2d} | {user.email:30s} | {status} | {user.full_name or 'No name'}")
            else:
                print(f"ID: -- | {email_obj.email:30s} | 📧 WHITELISTED ONLY")
        
        print(f"\nTotal whitelisted emails: {len(whitelist_emails)}")
        active_users = sum(1 for email_obj in whitelist_emails if user_db.get_user_by_email(email_obj.email))
        print(f"Total active users: {active_users}")
    
    def list_whitelist(self):
        """List all whitelisted emails."""
        print("\n📧 WHITELISTED EMAILS:")
        print("-" * 60)
        
        emails = user_db.get_whitelist_emails()
        for i, email_obj in enumerate(emails, 1):
            added_by = f"User {email_obj.added_by}" if email_obj.added_by else "System"
            print(f"{i:2d}. {email_obj.email:30s} | Added by: {added_by} | {email_obj.created_at.strftime('%Y-%m-%d')}")
        
        print(f"\nTotal whitelisted emails: {len(emails)}")
    
    def add_email_to_whitelist(self, email: str, added_by: Optional[int] = None):
        """Add an email to the whitelist."""
        try:
            if user_db.is_email_whitelisted(email):
                print(f"❌ Email {email} is already whitelisted")
                return False
            
            whitelist_email = user_db.add_email_to_whitelist(email, added_by)
            print(f"✅ Added {email} to whitelist (ID: {whitelist_email.id})")
            return True
        except Exception as e:
            print(f"❌ Error adding email to whitelist: {e}")
            return False
    
    def remove_email_from_whitelist(self, email: str):
        """Remove an email from the whitelist."""
        try:
            if not user_db.is_email_whitelisted(email):
                print(f"❌ Email {email} is not in whitelist")
                return False
            
            success = user_db.remove_email_from_whitelist(email)
            if success:
                print(f"✅ Removed {email} from whitelist")
                return True
            else:
                print(f"❌ Failed to remove {email} from whitelist")
                return False
        except Exception as e:
            print(f"❌ Error removing email from whitelist: {e}")
            return False
    
    def create_user(self, email: str, password: Optional[str] = None, full_name: Optional[str] = None):
        """Create a new user account."""
        try:
            # Check if email is whitelisted
            if not user_db.is_email_whitelisted(email):
                print(f"❌ Email {email} is not whitelisted. Add it to whitelist first.")
                return False
            
            # Check if user already exists
            if user_db.get_user_by_email(email):
                print(f"❌ User with email {email} already exists")
                return False
            
            # Get password if not provided
            if not password:
                password = getpass.getpass(f"Enter password for {email}: ")
                confirm_password = getpass.getpass("Confirm password: ")
                if password != confirm_password:
                    print("❌ Passwords do not match")
                    return False
            
            # Validate password length
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long")
                return False
            
            # Create user
            user_create = UserCreate(
                email=email,
                password=password,
                full_name=full_name
            )
            
            user = user_db.create_user(user_create)
            print(f"✅ Created user {email} (ID: {user.id})")
            return True
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False
    
    def deactivate_user(self, email: str):
        """Deactivate a user account."""
        try:
            user = user_db.get_user_by_email(email)
            if not user:
                print(f"❌ User {email} not found")
                return False
            
            success = user_db.deactivate_user(user.id)
            if success:
                print(f"✅ Deactivated user {email}")
                return True
            else:
                print(f"❌ Failed to deactivate user {email}")
                return False
        except Exception as e:
            print(f"❌ Error deactivating user: {e}")
            return False
    
    def test_login(self, email: str, password: Optional[str] = None):
        """Test user login."""
        try:
            if not password:
                password = getpass.getpass(f"Enter password for {email}: ")
            
            user = user_db.authenticate_user(email, password)
            if user:
                # Generate token to test full auth flow
                token = auth_service.create_access_token(user)
                print(f"✅ Login successful for {email}")
                print(f"   User ID: {user.id}")
                print(f"   Full Name: {user.full_name or 'Not set'}")
                print(f"   JWT Token: {token[:50]}...")
                return True
            else:
                print(f"❌ Login failed for {email} - invalid credentials")
                return False
        except Exception as e:
            print(f"❌ Error testing login: {e}")
            return False
    
    def bulk_add_emails(self, emails: List[str]):
        """Add multiple emails to whitelist."""
        print(f"\n📧 Adding {len(emails)} emails to whitelist...")
        success_count = 0
        
        for email in emails:
            if self.add_email_to_whitelist(email.strip()):
                success_count += 1
        
        print(f"\n✅ Successfully added {success_count}/{len(emails)} emails to whitelist")
        return success_count == len(emails)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Admin tools for JWT authentication system")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List commands
    subparsers.add_parser("list-users", help="List all users")
    subparsers.add_parser("list-whitelist", help="List whitelisted emails")
    
    # Whitelist management
    whitelist_add = subparsers.add_parser("add-email", help="Add email to whitelist")
    whitelist_add.add_argument("email", help="Email address to add")
    
    whitelist_remove = subparsers.add_parser("remove-email", help="Remove email from whitelist")
    whitelist_remove.add_argument("email", help="Email address to remove")
    
    bulk_add = subparsers.add_parser("bulk-add", help="Add multiple emails from file")
    bulk_add.add_argument("file", help="File containing email addresses (one per line)")
    
    # User management
    user_create = subparsers.add_parser("create-user", help="Create new user")
    user_create.add_argument("email", help="User email address")
    user_create.add_argument("--password", help="User password (will prompt if not provided)")
    user_create.add_argument("--name", help="User full name")
    
    user_deactivate = subparsers.add_parser("deactivate-user", help="Deactivate user")
    user_deactivate.add_argument("email", help="User email address")
    
    # Testing
    test_login = subparsers.add_parser("test-login", help="Test user login")
    test_login.add_argument("email", help="User email address")
    test_login.add_argument("--password", help="User password (will prompt if not provided)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    admin = AdminTools()
    
    try:
        if args.command == "list-users":
            admin.list_users()
        
        elif args.command == "list-whitelist":
            admin.list_whitelist()
        
        elif args.command == "add-email":
            admin.add_email_to_whitelist(args.email)
        
        elif args.command == "remove-email":
            admin.remove_email_from_whitelist(args.email)
        
        elif args.command == "bulk-add":
            if not os.path.exists(args.file):
                print(f"❌ File {args.file} not found")
                return 1
            
            with open(args.file, 'r') as f:
                emails = [line.strip() for line in f if line.strip()]
            
            admin.bulk_add_emails(emails)
        
        elif args.command == "create-user":
            admin.create_user(args.email, args.password, args.name)
        
        elif args.command == "deactivate-user":
            admin.deactivate_user(args.email)
        
        elif args.command == "test-login":
            admin.test_login(args.email, args.password)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    print("=" * 60)
    print("JWT AUTHENTICATION SYSTEM - ADMIN TOOLS")
    print("=" * 60)
    exit_code = main()
    sys.exit(exit_code)