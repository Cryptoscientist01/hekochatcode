import requests
import sys
import json
from datetime import datetime

class AIGirlfriendAPITester:
    def __init__(self, base_url="https://digital-dating-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.character_id = None
        
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)
            
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, params=data)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
                
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_json = response.json()
                    print(f"   Response keys: {list(response_json.keys()) if isinstance(response_json, dict) else 'Array/String'}")
                except:
                    print("   Response: Non-JSON or empty")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                    
            return success, response.json() if success and response.content else {}
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
    
    def test_signup(self, username, email, password):
        """Test user signup"""
        success, response = self.run_test(
            "User Signup",
            "POST", 
            "auth/signup",
            200,
            data={"username": username, "email": email, "password": password}
        )
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   User ID: {self.user_id}")
            return True
        return False
        
    def test_login(self, email, password):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            data={"email": email, "password": password}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   User ID: {self.user_id}")
            return True
        return False
        
    def test_get_characters(self):
        """Test fetching characters"""
        success, response = self.run_test(
            "Get Characters",
            "GET",
            "characters",
            200
        )
        if success and isinstance(response, list) and len(response) > 0:
            self.character_id = response[0]['id']
            print(f"   Found {len(response)} characters")
            print(f"   Sample character: {response[0]['name']}")
            return True
        return False
        
    def test_get_character_by_id(self):
        """Test fetching specific character"""
        if not self.character_id:
            print("❌ No character ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Character by ID",
            "GET",
            f"characters/{self.character_id}",
            200
        )
        if success and 'name' in response:
            print(f"   Character: {response['name']}")
            return True
        return False
        
    def test_send_chat_message(self):
        """Test sending chat message"""
        if not self.character_id or not self.user_id:
            print("❌ Missing character_id or user_id for chat test")
            return False
            
        success, response = self.run_test(
            "Send Chat Message",
            "POST",
            "chat/send",
            200,
            data={
                "character_id": self.character_id,
                "user_id": self.user_id,
                "message": "Hello! How are you today?"
            }
        )
        if success and 'response' in response:
            print(f"   AI Response: {response['response'][:100]}...")
            return True
        return False
        
    def test_get_chat_history(self):
        """Test fetching chat history"""
        if not self.character_id or not self.user_id:
            print("❌ Missing character_id or user_id for chat history test")
            return False
            
        success, response = self.run_test(
            "Get Chat History",
            "GET",
            f"chat/history/{self.character_id}?user_id={self.user_id}",
            200
        )
        if success and 'messages' in response:
            print(f"   Found {len(response['messages'])} messages in history")
            return True
        return False
        
    def test_generate_voice(self):
        """Test voice generation"""
        success, response = self.run_test(
            "Generate Voice",
            "POST",
            "voice/generate",
            200,
            data={
                "text": "Hello, this is a test message for voice generation",
                "voice": "nova"
            }
        )
        if success and 'audio' in response:
            print(f"   Voice generated successfully (base64 length: {len(response['audio'])})")
            return True
        return False
        
    def test_generate_image(self):
        """Test image generation"""
        if not self.character_id:
            print("❌ No character ID available for image generation test")
            return False
            
        success, response = self.run_test(
            "Generate Image", 
            "POST",
            "image/generate",
            200,
            data={
                "prompt": "a beautiful sunset over mountains",
                "character_id": self.character_id
            }
        )
        if success and 'image' in response:
            print(f"   Image generated successfully (base64 length: {len(response['image'])})")
            return True
        return False

def main():
    # Initialize tester
    tester = AIGirlfriendAPITester()
    
    # Test credentials
    timestamp = datetime.now().strftime('%H%M%S')
    test_email = f"test_{timestamp}@example.com"
    test_username = f"testuser_{timestamp}"
    test_password = "TestPass123!"
    
    print("🚀 Starting AI Girlfriend API Testing...")
    print(f"Backend URL: {tester.base_url}")
    print(f"Test user: {test_email}")
    
    # Core functionality tests
    tests = [
        ("User Signup", lambda: tester.test_signup(test_username, test_email, test_password)),
        ("Get Characters", lambda: tester.test_get_characters()),
        ("Get Character by ID", lambda: tester.test_get_character_by_id()),
        ("Send Chat Message", lambda: tester.test_send_chat_message()),
        ("Get Chat History", lambda: tester.test_get_chat_history()),
        ("Generate Voice", lambda: tester.test_generate_voice()),
        ("Generate Image", lambda: tester.test_generate_image())
    ]
    
    # Run tests
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
    
    # Test login with existing user
    print(f"\n🔄 Testing login with existing user...")
    tester.token = None  # Reset token
    if not tester.test_login(test_email, test_password):
        print("❌ Login test failed")
        
    # Print results
    print(f"\n📊 TEST SUMMARY")
    print(f"   Tests run: {tester.tests_run}")
    print(f"   Tests passed: {tester.tests_passed}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    # Return success/failure
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())