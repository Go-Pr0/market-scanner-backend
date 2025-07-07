#!/usr/bin/env python3
"""
Test script to verify the centralized configuration system is working properly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test the centralized configuration system."""
    print("Testing centralized configuration system...")
    
    try:
        from app.core.config import config, settings
        
        print("\n✅ Successfully imported config and settings")
        
        # Test basic configuration values
        print(f"App Name: {config.APP_NAME}")
        print(f"Version: {config.VERSION}")
        print(f"JWT Secret Key: {config.JWT_SECRET_KEY[:10]}..." if config.JWT_SECRET_KEY else "Not set")
        print(f"Gemini API Key: {'Set' if config.GEMINI_API_KEY else 'Not set'}")
        
        # Test database paths
        print(f"\nDatabase Paths:")
        print(f"  User DB: {config.USER_DB_PATH}")
        print(f"  AI Assistant DB: {config.AI_ASSISTANT_DB_PATH}")
        print(f"  Bybit DB: {config.BYBIT_DB_PATH}")
        
        # Test legacy compatibility
        print(f"\nLegacy compatibility:")
        print(f"  settings.app_name: {settings.app_name}")
        print(f"  settings.version: {settings.version}")
        print(f"  settings.gemini_api_key: {'Set' if settings.gemini_api_key else 'Not set'}")
        
        # Test that config and settings point to the same object
        assert config is settings, "config and settings should be the same object"
        print("✅ Legacy compatibility working correctly")
        
        print("\n✅ All configuration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_imports():
    """Test that services can import and use the config."""
    print("\nTesting service imports...")
    
    try:
        # Test auth service
        from app.services.auth_service import auth_service
        print("✅ Auth service imported successfully")
        
        # Test user_db service
        from app.services.user_db import user_db
        print("✅ User DB service imported successfully")
        
        # Test ai_assistant_db service
        from app.services.ai_assistant_db import ai_assistant_db
        print("✅ AI Assistant DB service imported successfully")
        
        # Test AI services
        from app.services.ai_service import generate_questions
        from app.services.ai_assistant_service import send_chat_message
        print("✅ AI services imported successfully")
        
        print("✅ All service imports passed!")
        return True
        
    except Exception as e:
        print(f"❌ Service import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CENTRALIZED CONFIGURATION SYSTEM TEST")
    print("=" * 60)
    
    config_test = test_config()
    service_test = test_service_imports()
    
    print("\n" + "=" * 60)
    if config_test and service_test:
        print("🎉 ALL TESTS PASSED! Configuration system is working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED! Please check the errors above.")
        sys.exit(1)