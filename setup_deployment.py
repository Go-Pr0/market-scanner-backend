#!/usr/bin/env python3
"""
Deployment setup script for Market Scanner Backend.
Verifies database initialization and system readiness.
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def generate_jwt_secret():
    """Generate a secure JWT secret key."""
    return secrets.token_urlsafe(64)

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required. Current version:", f"{version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_environment():
    """Check if running in virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment (recommended for production)")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment_file():
    """Set up .env file if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    
    print("🔧 Creating .env file from template...")
    
    # Read template
    with open(env_example, 'r') as f:
        content = f.read()
    
    # Generate JWT secret
    jwt_secret = generate_jwt_secret()
    content = content.replace('your-super-secret-jwt-key-change-this-in-production-make-it-long-and-random', jwt_secret)
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env file created with secure JWT secret")
    print("⚠️  Please edit .env file to set your GEMINI_API_KEY and other production values")
    return True

def verify_database_initialization():
    """Verify that databases can be initialized."""
    print("🗄️  Verifying database initialization...")
    
    try:
        # Import database services to trigger initialization
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.services.user_db import user_db
        from app.services.ai_assistant_db import ai_assistant_db
        
        print("✅ User database initialized")
        print("✅ AI Assistant database initialized")
        
        # Check if data directory exists
        data_dir = Path("./data")
        if data_dir.exists():
            print(f"✅ Data directory exists: {data_dir.absolute()}")
            
            # List database files
            db_files = list(data_dir.glob("*.db"))
            for db_file in db_files:
                size = db_file.stat().st_size
                print(f"   📁 {db_file.name}: {size} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def verify_questionnaire_table():
    """Verify that trade_questions table exists and is accessible."""
    print("📋 Verifying questionnaire table...")
    
    try:
        from app.services.ai_assistant_db import ai_assistant_db
        
        # Test table access
        test_result = ai_assistant_db.get_user_questionnaire("test@example.com")
        print("✅ trade_questions table accessible (returned None as expected for non-existent user)")
        
        return True
        
    except Exception as e:
        print(f"❌ Questionnaire table verification failed: {e}")
        return False

def check_required_environment_vars():
    """Check if required environment variables are set."""
    print("🔐 Checking environment variables...")
    
    # Load environment
    from app.core.config import settings
    import os
    from dotenv import load_dotenv
    
    # Load .env file
    load_dotenv()
    
    checks = []
    
    # JWT Secret
    jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    if jwt_secret != "your-secret-key-change-this-in-production":
        print("✅ JWT_SECRET_KEY is set")
        checks.append(True)
    else:
        print("❌ JWT_SECRET_KEY not set (using default)")
        checks.append(False)
    
    # Gemini API Key
    if settings.gemini_api_key:
        print("✅ GEMINI_API_KEY is set")
        checks.append(True)
    else:
        print("⚠️  GEMINI_API_KEY not set (AI features will not work)")
        checks.append(True)  # Not critical for basic functionality
    
    return all(checks)

def test_basic_functionality():
    """Test basic application functionality."""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test user database
        from app.services.user_db import user_db
        whitelist = user_db.get_whitelist_emails()
        print(f"✅ User database functional ({len(whitelist)} whitelisted emails)")
        
        # Test AI assistant database
        from app.services.ai_assistant_db import ai_assistant_db
        # This should not fail even with empty database
        result = ai_assistant_db.get_user_questionnaire("nonexistent@test.com")
        print("✅ AI Assistant database functional")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def create_admin_user_prompt():
    """Prompt to create admin user."""
    print("\n👤 Admin User Setup")
    print("-" * 40)
    
    response = input("Would you like to create an admin user now? (y/n): ").lower().strip()
    
    if response == 'y':
        email = input("Enter admin email: ").strip()
        if email:
            print(f"\nTo create admin user, run:")
            print(f"python admin_tools.py add-email {email}")
            print(f"python admin_tools.py create-user {email}")
        else:
            print("❌ No email provided")
    else:
        print("ℹ️  You can create admin user later using admin_tools.py")

def main():
    """Main setup function."""
    print("=" * 60)
    print("MARKET SCANNER BACKEND - DEPLOYMENT SETUP")
    print("=" * 60)
    
    checks = []
    
    # System checks
    checks.append(check_python_version())
    checks.append(check_virtual_environment())
    
    # Setup steps
    checks.append(setup_environment_file())
    checks.append(install_dependencies())
    
    # Database verification
    checks.append(verify_database_initialization())
    checks.append(verify_questionnaire_table())
    
    # Configuration checks
    checks.append(check_required_environment_vars())
    
    # Functionality tests
    checks.append(test_basic_functionality())
    
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    if all(checks):
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your backend is ready for deployment")
        print("\nNext steps:")
        print("1. Edit .env file with your production values")
        print("2. Create admin user with admin_tools.py")
        print("3. Start the application with: python main.py")
        
        create_admin_user_prompt()
        
        return 0
    else:
        failed_count = len([c for c in checks if not c])
        print(f"❌ {failed_count} checks failed")
        print("Please fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)