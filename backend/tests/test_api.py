"""
Backend API tests for AI Companion web app
Tests: Auth (signup, login, Google session), Characters, Chat, Voice
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealth:
    """Health check and basic connectivity tests"""
    
    def test_api_reachable(self):
        """Verify API is reachable"""
        response = requests.get(f"{BASE_URL}/api/characters")
        assert response.status_code == 200, f"API not reachable: {response.status_code}"


class TestCharactersAPI:
    """Characters API endpoint tests"""
    
    def test_get_all_characters(self):
        """GET /api/characters returns characters list"""
        response = requests.get(f"{BASE_URL}/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 25  # Should have 25+ characters
        print(f"Total characters: {len(data)}")
    
    def test_get_characters_category_girls(self):
        """GET /api/characters?category=Girls returns Girls only"""
        response = requests.get(f"{BASE_URL}/api/characters?category=Girls")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # 10 girls
        for char in data:
            assert char['category'] == 'Girls'
        print(f"Girls count: {len(data)}")
    
    def test_get_characters_category_anime(self):
        """GET /api/characters?category=Anime returns Anime only"""
        response = requests.get(f"{BASE_URL}/api/characters?category=Anime")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8  # 8 anime
        for char in data:
            assert char['category'] == 'Anime'
        print(f"Anime count: {len(data)}")
    
    def test_get_characters_category_guys(self):
        """GET /api/characters?category=Guys returns Guys only"""
        response = requests.get(f"{BASE_URL}/api/characters?category=Guys")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7  # 7 guys
        for char in data:
            assert char['category'] == 'Guys'
        print(f"Guys count: {len(data)}")
    
    def test_get_single_character(self):
        """GET /api/characters/{id} returns single character"""
        # First get all characters to find an ID
        all_response = requests.get(f"{BASE_URL}/api/characters")
        assert all_response.status_code == 200
        characters = all_response.json()
        assert len(characters) > 0
        
        character_id = characters[0]['id']
        
        # Get single character
        response = requests.get(f"{BASE_URL}/api/characters/{character_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == character_id
        assert 'name' in data
        assert 'personality' in data
        assert 'traits' in data
        print(f"Single character fetched: {data['name']}")
    
    def test_get_nonexistent_character(self):
        """GET /api/characters/{invalid_id} returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/characters/{fake_id}")
        assert response.status_code == 404
        print("404 returned for nonexistent character")
    
    def test_character_data_structure(self):
        """Verify character data has all required fields"""
        response = requests.get(f"{BASE_URL}/api/characters?category=Girls")
        assert response.status_code == 200
        characters = response.json()
        
        for char in characters:
            assert 'id' in char
            assert 'name' in char
            assert 'age' in char
            assert 'personality' in char
            assert 'traits' in char
            assert isinstance(char['traits'], list)
            assert 'category' in char
            assert 'avatar_url' in char
            assert 'description' in char
        print("All character fields verified")


class TestAuthAPI:
    """Authentication API tests"""
    
    def test_signup_new_user(self):
        """POST /api/auth/signup creates new user"""
        unique_email = f"TEST_user_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "username": "TestUser",
            "password": "test123456"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response.status_code == 200, f"Signup failed: {response.text}"
        data = response.json()
        
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == unique_email
        print(f"User created: {unique_email}")
    
    def test_signup_duplicate_email(self):
        """POST /api/auth/signup rejects duplicate email"""
        unique_email = f"TEST_dup_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "username": "TestUser1",
            "password": "test123456"
        }
        
        # First signup
        response1 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response1.status_code == 200
        
        # Duplicate signup should fail
        payload['username'] = 'TestUser2'
        response2 = requests.post(f"{BASE_URL}/api/auth/signup", json=payload)
        assert response2.status_code == 400
        print("Duplicate email rejected")
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with valid credentials"""
        # First create a user
        unique_email = f"TEST_login_{uuid.uuid4().hex[:8]}@example.com"
        password = "test123456"
        
        signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "username": "LoginTestUser",
            "password": password
        })
        assert signup_response.status_code == 200
        
        # Now login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": password
        })
        assert login_response.status_code == 200
        data = login_response.json()
        
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == unique_email
        print(f"Login successful for: {unique_email}")
    
    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("Invalid credentials rejected with 401")
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Unauthenticated /auth/me returns 401")
    
    def test_google_session_invalid(self):
        """POST /api/auth/google/session with invalid session returns error"""
        response = requests.post(f"{BASE_URL}/api/auth/google/session", json={
            "session_id": "invalid_session_id"
        })
        # Should return 401 for invalid session
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Invalid Google session rejected")
    
    def test_logout(self):
        """POST /api/auth/logout clears session"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data.get('message') == 'Logged out successfully'
        print("Logout successful")


class TestChatAPI:
    """Chat API tests"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user and return credentials"""
        unique_email = f"TEST_chat_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/signup", json={
            "email": unique_email,
            "username": "ChatTestUser",
            "password": "test123456"
        })
        assert response.status_code == 200
        return response.json()
    
    @pytest.fixture
    def test_character(self):
        """Get a test character"""
        response = requests.get(f"{BASE_URL}/api/characters?category=Girls")
        assert response.status_code == 200
        characters = response.json()
        return characters[0]
    
    def test_send_chat_message(self, test_user, test_character):
        """POST /api/chat/send sends message and gets AI response"""
        user_id = test_user['user']['id']
        character_id = test_character['id']
        
        response = requests.post(f"{BASE_URL}/api/chat/send", json={
            "character_id": character_id,
            "user_id": user_id,
            "message": "Hello, how are you?"
        })
        
        assert response.status_code == 200, f"Chat send failed: {response.text}"
        data = response.json()
        
        assert 'response' in data
        assert 'message_id' in data
        assert len(data['response']) > 0
        print(f"AI Response received: {data['response'][:100]}...")
    
    def test_get_chat_history(self, test_user, test_character):
        """GET /api/chat/history/{character_id} returns chat history"""
        user_id = test_user['user']['id']
        character_id = test_character['id']
        
        # First send a message
        requests.post(f"{BASE_URL}/api/chat/send", json={
            "character_id": character_id,
            "user_id": user_id,
            "message": "Test message for history"
        })
        
        # Get history
        response = requests.get(f"{BASE_URL}/api/chat/history/{character_id}?user_id={user_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert 'messages' in data
        assert isinstance(data['messages'], list)
        print(f"Chat history retrieved: {len(data['messages'])} messages")
    
    def test_send_chat_invalid_character(self, test_user):
        """POST /api/chat/send with invalid character returns 404"""
        user_id = test_user['user']['id']
        fake_id = str(uuid.uuid4())
        
        response = requests.post(f"{BASE_URL}/api/chat/send", json={
            "character_id": fake_id,
            "user_id": user_id,
            "message": "Hello"
        })
        
        assert response.status_code == 404
        print("Chat with invalid character returns 404")


class TestVoiceAPI:
    """Voice generation API tests"""
    
    def test_voice_generate(self):
        """POST /api/voice/generate generates audio"""
        response = requests.post(f"{BASE_URL}/api/voice/generate", json={
            "text": "Hello, how are you today?",
            "voice": "nova"
        })
        
        assert response.status_code == 200, f"Voice generate failed: {response.text}"
        data = response.json()
        
        assert 'audio' in data
        assert 'format' in data
        assert data['format'] == 'mp3'
        assert len(data['audio']) > 0  # Base64 encoded audio
        print(f"Voice generated successfully, audio length: {len(data['audio'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
