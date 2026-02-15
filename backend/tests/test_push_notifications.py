"""
Test Push Notification API Endpoints
Tests for notification scheduler, VAPID keys, subscription, preferences
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVAPIDPublicKey:
    """Test VAPID public key endpoint"""
    
    def test_get_vapid_public_key(self):
        """Test /api/push/vapid-public-key returns valid key"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "publicKey" in data, "Response should contain publicKey"
        assert len(data["publicKey"]) > 20, "publicKey should be a substantial VAPID key"
        print(f"VAPID public key: {data['publicKey'][:20]}...")


class TestUserRegistrationAndLogin:
    """Test user registration and login flow"""
    
    @pytest.fixture(scope="class")
    def test_user_credentials(self):
        """Generate unique test user credentials"""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "email": f"test_push_{unique_id}@test.com",
            "username": f"TestPush_{unique_id}",
            "password": "testpassword123"
        }
    
    @pytest.fixture(scope="class")
    def registered_user(self, test_user_credentials):
        """Register a test user and return token and user data"""
        # Register new user
        response = requests.post(
            f"{BASE_URL}/api/auth/signup",
            json=test_user_credentials
        )
        
        if response.status_code == 400 and "already registered" in response.text:
            # User already exists, try login
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "email": test_user_credentials["email"],
                    "password": test_user_credentials["password"]
                }
            )
        
        assert response.status_code == 200, f"Registration/Login failed: {response.text}"
        data = response.json()
        
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        
        return {
            "token": data["token"],
            "user": data["user"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_signup_returns_token(self, registered_user):
        """Test that signup/login returns a valid token"""
        assert registered_user["token"] is not None
        assert len(registered_user["token"]) > 10
        print(f"Got token: {registered_user['token'][:20]}...")
    
    def test_user_has_id(self, registered_user):
        """Test that user object contains id"""
        assert registered_user["user_id"] is not None
        print(f"User ID: {registered_user['user_id']}")


class TestPushSubscription:
    """Test push subscription endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session with new user"""
        unique_id = str(uuid.uuid4())[:8]
        credentials = {
            "email": f"test_sub_{unique_id}@test.com",
            "username": f"TestSub_{unique_id}",
            "password": "testpassword123"
        }
        
        # Register new user
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=credentials)
        
        if response.status_code == 400:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": credentials["email"], "password": credentials["password"]}
            )
        
        assert response.status_code == 200, f"Failed to get auth: {response.text}"
        data = response.json()
        
        return {
            "token": data["token"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_subscribe_requires_auth(self):
        """Test /api/push/subscribe requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json={
                "endpoint": "https://example.com/push/v1/test",
                "keys": {"p256dh": "test_key", "auth": "test_auth"}
            }
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Subscribe correctly requires auth")
    
    def test_subscribe_with_valid_auth(self, auth_session):
        """Test /api/push/subscribe works with valid auth token"""
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            headers={"Authorization": f"Bearer {auth_session['token']}"},
            json={
                "endpoint": f"https://example.com/push/v1/{auth_session['user_id']}",
                "keys": {"p256dh": "test_p256dh_key", "auth": "test_auth_key"}
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "Subscribed" in data["message"]
        print(f"Subscribe response: {data['message']}")
    
    def test_unsubscribe_requires_auth(self):
        """Test /api/push/unsubscribe requires authentication"""
        response = requests.post(f"{BASE_URL}/api/push/unsubscribe")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Unsubscribe correctly requires auth")
    
    def test_unsubscribe_with_valid_auth(self, auth_session):
        """Test /api/push/unsubscribe works with valid auth token"""
        response = requests.post(
            f"{BASE_URL}/api/push/unsubscribe",
            headers={"Authorization": f"Bearer {auth_session['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"Unsubscribe response: {data['message']}")


class TestPushPreferences:
    """Test notification preferences endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session with new user"""
        unique_id = str(uuid.uuid4())[:8]
        credentials = {
            "email": f"test_prefs_{unique_id}@test.com",
            "username": f"TestPrefs_{unique_id}",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=credentials)
        
        if response.status_code == 400:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": credentials["email"], "password": credentials["password"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        return {
            "token": data["token"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_get_preferences_returns_defaults(self, auth_session):
        """Test GET /api/push/preferences/{user_id} returns default values"""
        response = requests.get(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Check default values
        assert "enabled" in data
        assert data["enabled"] == True
        assert "frequency" in data
        assert data["frequency"] == "medium"
        assert "quiet_hours_start" in data
        assert "quiet_hours_end" in data
        print(f"Default preferences: enabled={data['enabled']}, frequency={data['frequency']}")
    
    def test_update_preferences(self, auth_session):
        """Test PUT /api/push/preferences/{user_id} updates preferences"""
        new_prefs = {
            "enabled": True,
            "frequency": "high",
            "quiet_hours_start": 23,
            "quiet_hours_end": 7
        }
        
        response = requests.put(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}",
            json=new_prefs
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "updated" in data["message"].lower()
        print(f"Update response: {data['message']}")
    
    def test_verify_updated_preferences(self, auth_session):
        """Test that preferences were actually updated"""
        # First update
        new_prefs = {
            "enabled": False,
            "frequency": "low",
            "quiet_hours_start": 21,
            "quiet_hours_end": 9
        }
        
        requests.put(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}",
            json=new_prefs
        )
        
        # Then verify
        response = requests.get(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["enabled"] == False
        assert data["frequency"] == "low"
        print(f"Verified updated preferences: enabled={data['enabled']}, frequency={data['frequency']}")


class TestGenerateNotification:
    """Test notification generation endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session with new user"""
        unique_id = str(uuid.uuid4())[:8]
        credentials = {
            "email": f"test_notify_{unique_id}@test.com",
            "username": f"TestNotify_{unique_id}",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=credentials)
        
        if response.status_code == 400:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": credentials["email"], "password": credentials["password"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        return {
            "token": data["token"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_generate_notification_random(self, auth_session):
        """Test /api/push/generate-notification/{user_id} creates random notification"""
        # First enable notifications for the user
        requests.put(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}",
            json={"enabled": True, "frequency": "high", "quiet_hours_start": 23, "quiet_hours_end": 0}
        )
        
        response = requests.get(
            f"{BASE_URL}/api/push/generate-notification/{auth_session['user_id']}",
            params={"notification_type": "random"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Notification should be generated (or reason for not sending)
        if data.get("send") == True:
            assert "notification" in data
            notification = data["notification"]
            assert "title" in notification
            assert "body" in notification
            assert "character_id" in notification
            print(f"Generated notification: {notification['title']} - {notification['body'][:30]}...")
        else:
            # Valid reason for not sending
            assert "message" in data
            print(f"Notification not sent: {data['message']}")
    
    def test_generate_notification_inactivity(self, auth_session):
        """Test /api/push/generate-notification/{user_id} with inactivity type"""
        response = requests.get(
            f"{BASE_URL}/api/push/generate-notification/{auth_session['user_id']}",
            params={"notification_type": "inactivity"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "send" in data
        print(f"Inactivity notification result: send={data.get('send')}, message={data.get('message', 'N/A')}")
    
    def test_notification_respects_disabled_prefs(self, auth_session):
        """Test that notification generation respects disabled preferences"""
        # Disable notifications
        requests.put(
            f"{BASE_URL}/api/push/preferences/{auth_session['user_id']}",
            json={"enabled": False, "frequency": "medium", "quiet_hours_start": 22, "quiet_hours_end": 8}
        )
        
        response = requests.get(
            f"{BASE_URL}/api/push/generate-notification/{auth_session['user_id']}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("send") == False, "Notification should not be sent when disabled"
        assert "disabled" in data.get("message", "").lower()
        print(f"Correctly blocked notification when disabled: {data['message']}")


class TestNotificationHistory:
    """Test notification history endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session"""
        unique_id = str(uuid.uuid4())[:8]
        credentials = {
            "email": f"test_history_{unique_id}@test.com",
            "username": f"TestHistory_{unique_id}",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=credentials)
        
        if response.status_code == 400:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": credentials["email"], "password": credentials["password"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        return {
            "token": data["token"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_get_notification_history(self, auth_session):
        """Test GET /api/push/notification-history/{user_id}"""
        response = requests.get(
            f"{BASE_URL}/api/push/notification-history/{auth_session['user_id']}"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "history" in data
        assert isinstance(data["history"], list)
        print(f"Notification history count: {len(data['history'])}")


class TestCheckInactivity:
    """Test inactivity check endpoint"""
    
    def test_check_inactivity_endpoint(self):
        """Test GET /api/push/check-inactivity returns list"""
        response = requests.get(f"{BASE_URL}/api/push/check-inactivity")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "inactive_users" in data
        assert isinstance(data["inactive_users"], list)
        print(f"Inactive users count: {len(data['inactive_users'])}")


class TestUpdateActivity:
    """Test activity update endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Create authenticated session"""
        unique_id = str(uuid.uuid4())[:8]
        credentials = {
            "email": f"test_activity_{unique_id}@test.com",
            "username": f"TestActivity_{unique_id}",
            "password": "testpassword123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=credentials)
        
        if response.status_code == 400:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": credentials["email"], "password": credentials["password"]}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        return {
            "token": data["token"],
            "user_id": data["user"].get("id") or data["user"].get("user_id")
        }
    
    def test_update_activity_with_auth(self, auth_session):
        """Test POST /api/push/update-activity with auth"""
        response = requests.post(
            f"{BASE_URL}/api/push/update-activity",
            headers={"Authorization": f"Bearer {auth_session['token']}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "message" in data
        print(f"Update activity response: {data['message']}")
    
    def test_update_activity_without_auth(self):
        """Test POST /api/push/update-activity without auth (should silently succeed)"""
        response = requests.post(f"{BASE_URL}/api/push/update-activity")
        # Should return 200 even without auth (silent fail)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestCharactersEndpoint:
    """Test characters page loads correctly"""
    
    def test_get_characters(self):
        """Test GET /api/characters returns list"""
        response = requests.get(f"{BASE_URL}/api/characters")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least some characters"
        
        # Check first character has required fields
        char = data[0]
        assert "id" in char
        assert "name" in char
        assert "category" in char
        print(f"Total characters: {len(data)}")
    
    def test_get_characters_by_category(self):
        """Test GET /api/characters with category filter"""
        for category in ["Girls", "Anime", "Guys"]:
            response = requests.get(f"{BASE_URL}/api/characters", params={"category": category})
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            # All returned characters should be in the requested category
            for char in data:
                assert char["category"] == category
            print(f"Characters in {category}: {len(data)}")


# Cleanup test class
class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_note(self):
        """Note about test cleanup"""
        print("Test users created with TEST_ prefix will persist in database")
        print("These can be cleaned up manually or via admin panel")
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
