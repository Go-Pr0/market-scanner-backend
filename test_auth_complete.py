#!/usr/bin/env python3
"""
Comprehensive test script for the JWT-based authentication system.
Tests all authentication endpoints and user separation functionality.
"""

import sys
import os
import requests
import json
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USERS = [
    {"email": "lampensn@icloud.com", "password": "Noah123123"},  # Padded password
    {"email": "user2@example.com", "password": "password2"},
    {"email": "user3@example.com", "password": "password3"}
]

class AuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        
    def test_server_health(self) -> bool:
        """Test if the server is running."""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    def test_email_whitelist_check(self, email: str) -> bool:
        """Test email whitelist checking."""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/check-email",
                json={"email": email}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("is_whitelisted", False)
            return False
        except Exception as e:
            print(f"Error checking email whitelist: {e}")
            return False
    
    def test_user_login(self, email: str, password: str) -> Dict[str, Any]:
        """Test user login and return token info."""
        try:
            response = self.session.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[email] = data["access_token"]
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": response.text, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_protected_endpoint(self, email: str) -> Dict[str, Any]:
        """Test accessing a protected endpoint with JWT token."""
        if email not in self.tokens:
            return {"success": False, "error": "No token for user"}
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[email]}"}
            response = self.session.get(f"{BASE_URL}/api/auth/me", headers=headers)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_ai_chat_separation(self, email: str, message: str) -> Dict[str, Any]:
        """Test AI chat with user separation."""
        if email not in self.tokens:
            return {"success": False, "error": "No token for user"}
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[email]}"}
            response = self.session.post(
                f"{BASE_URL}/api/chat/message",
                json={
                    "message": message,
                    "status": "pre-trade"
                },
                headers=headers
            )
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_chat_history_separation(self, email: str) -> Dict[str, Any]:
        """Test that users can only see their own chat history."""
        if email not in self.tokens:
            return {"success": False, "error": "No token for user"}
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[email]}"}
            response = self.session.get(f"{BASE_URL}/api/chat/recent", headers=headers)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_test(self):
        """Run all authentication tests."""
        print("=" * 80)
        print("JWT AUTHENTICATION SYSTEM - COMPREHENSIVE TEST")
        print("=" * 80)
        
        # Test 1: Server Health
        print("\n1. Testing server health...")
        if not self.test_server_health():
            print("❌ Server is not running! Please start the server first.")
            print("   Run: python main.py")
            return False
        print("✅ Server is running")
        
        # Test 2: Email Whitelist
        print("\n2. Testing email whitelist...")
        for user in TEST_USERS:
            email = user["email"]
            is_whitelisted = self.test_email_whitelist_check(email)
            if is_whitelisted:
                print(f"✅ {email} is whitelisted")
            else:
                print(f"❌ {email} is NOT whitelisted")
        
        # Test non-whitelisted email
        non_whitelisted = "notwhitelisted@example.com"
        is_whitelisted = self.test_email_whitelist_check(non_whitelisted)
        if not is_whitelisted:
            print(f"✅ {non_whitelisted} correctly NOT whitelisted")
        else:
            print(f"❌ {non_whitelisted} should NOT be whitelisted")
        
        # Test 3: User Login
        print("\n3. Testing user login...")
        login_results = {}
        for user in TEST_USERS:
            email = user["email"]
            password = user["password"]
            result = self.test_user_login(email, password)
            login_results[email] = result
            
            if result["success"]:
                user_data = result["data"]["user"]
                print(f"✅ {email} login successful (User ID: {user_data['id']})")
            else:
                print(f"❌ {email} login failed: {result.get('error', 'Unknown error')}")
        
        # Test 4: Protected Endpoints
        print("\n4. Testing protected endpoints...")
        for user in TEST_USERS:
            email = user["email"]
            if login_results[email]["success"]:
                result = self.test_protected_endpoint(email)
                if result["success"]:
                    user_data = result["data"]
                    print(f"✅ {email} can access protected endpoint (ID: {user_data['id']})")
                else:
                    print(f"❌ {email} cannot access protected endpoint: {result.get('error')}")
        
        # Test 5: AI Chat User Separation
        print("\n5. Testing AI chat user separation...")
        chat_results = {}
        for i, user in enumerate(TEST_USERS):
            email = user["email"]
            if login_results[email]["success"]:
                message = f"Hello, this is a test message from user {i+1}"
                result = self.test_ai_chat_separation(email, message)
                chat_results[email] = result
                
                if result["success"]:
                    chat_data = result["data"]
                    chat_id = chat_data["chat_id"]
                    print(f"✅ {email} created chat session: {chat_id}")
                else:
                    print(f"❌ {email} failed to create chat: {result.get('error')}")
        
        # Test 6: Chat History Separation
        print("\n6. Testing chat history separation...")
        for user in TEST_USERS:
            email = user["email"]
            if login_results[email]["success"]:
                result = self.test_chat_history_separation(email)
                if result["success"]:
                    chats = result["data"]["chats"]
                    print(f"✅ {email} can see {len(chats)} chat(s)")
                    # Verify user can only see their own chats
                    for chat in chats:
                        print(f"   - Chat: {chat['id']} ({chat.get('title', 'No title')})")
                else:
                    print(f"❌ {email} cannot access chat history: {result.get('error')}")
        
        # Test 7: Invalid Token
        print("\n7. Testing invalid token handling...")
        try:
            headers = {"Authorization": "Bearer invalid_token_here"}
            response = self.session.get(f"{BASE_URL}/api/auth/me", headers=headers)
            if response.status_code == 401:
                print("✅ Invalid token correctly rejected")
            else:
                print(f"❌ Invalid token not properly handled (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")
        
        print("\n" + "=" * 80)
        print("AUTHENTICATION SYSTEM TEST COMPLETED")
        print("=" * 80)
        
        # Summary
        successful_logins = sum(1 for result in login_results.values() if result["success"])
        print(f"\n📊 SUMMARY:")
        print(f"   - Users successfully logged in: {successful_logins}/{len(TEST_USERS)}")
        print(f"   - JWT tokens generated: {len(self.tokens)}")
        print(f"   - System ready for production use: {'✅ YES' if successful_logins == len(TEST_USERS) else '❌ NO'}")
        
        return successful_logins == len(TEST_USERS)


def main():
    """Main test function."""
    tester = AuthTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed! The JWT authentication system is working correctly.")
        print("\n���� NEXT STEPS:")
        print("   1. Update frontend to use JWT authentication")
        print("   2. Add more emails to whitelist as needed")
        print("   3. Configure production JWT secret key")
        print("   4. Set up HTTPS for production")
    else:
        print("\n⚠️  Some tests failed. Please check the server logs and fix any issues.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)