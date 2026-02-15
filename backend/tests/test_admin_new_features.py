"""
Test suite for Admin Panel New Features:
- Admin Analytics (users, characters, messages stats)
- Chat Analytics (popular characters, active users)
- Moderation (chat conversations view/delete)
- Announcements (create, edit, delete)
- Notifications (send to users/broadcast)
- Revenue Dashboard (mocked revenue data)
- Admins Management (view, create admin - super admin only)
- Activity Logs (admin actions with timestamps)
- Character Edit functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://girlfriend-app.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAdminAnalytics:
    """Test Admin Analytics endpoints - users, characters, messages stats with charts"""
    
    def test_admin_analytics_returns_all_fields(self, auth_headers):
        """Test that analytics endpoint returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify all expected fields
        assert "total_users" in data
        assert "total_characters" in data
        assert "total_messages" in data
        assert "total_images" in data
        assert "total_favorites" in data
        assert "total_custom_characters" in data
        assert "recent_users" in data
        assert "users_by_day" in data
        
        # Verify users_by_day is a list with chart data
        assert isinstance(data["users_by_day"], list)
        if len(data["users_by_day"]) > 0:
            assert "date" in data["users_by_day"][0]
            assert "count" in data["users_by_day"][0]
        
        print(f"Analytics: {data['total_users']} users, {data['total_characters']} chars, {data['total_messages']} msgs")
    
    def test_analytics_requires_auth(self):
        """Test that analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401


class TestChatAnalytics:
    """Test Chat Analytics - popular characters and active users"""
    
    def test_chat_analytics_returns_expected_fields(self, auth_headers):
        """Test chat analytics endpoint returns popular characters and active users"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/chats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "most_popular_characters" in data
        assert "most_active_users" in data
        assert "total_messages" in data
        assert "average_messages_per_user" in data
        assert "messages_by_day" in data
        
        # Verify popular characters structure
        if len(data["most_popular_characters"]) > 0:
            char = data["most_popular_characters"][0]
            assert "name" in char
            assert "chat_count" in char
        
        # Verify active users structure
        if len(data["most_active_users"]) > 0:
            user = data["most_active_users"][0]
            assert "message_count" in user
        
        print(f"Chat Analytics: {data['total_messages']} total msgs, {len(data['most_popular_characters'])} popular chars")
    
    def test_chat_analytics_requires_auth(self):
        """Test that chat analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/chats")
        assert response.status_code == 401


class TestModerationTab:
    """Test Moderation - chat conversations view/delete options"""
    
    def test_get_all_chats_for_moderation(self, auth_headers):
        """Test getting all chat conversations"""
        response = requests.get(f"{BASE_URL}/api/admin/chats?limit=50", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "chats" in data
        assert "total" in data
        
        # Verify chat structure if there are chats
        if len(data["chats"]) > 0:
            chat = data["chats"][0]
            assert "chat_id" in chat
            assert "user_name" in chat or "user_id" in chat
            assert "character_name" in chat or "character_id" in chat
            assert "message_count" in chat
        
        print(f"Moderation: {len(data['chats'])} chats found, total: {data['total']}")
    
    def test_get_chat_messages(self, auth_headers):
        """Test getting messages from a specific chat"""
        # First get chats
        chats_response = requests.get(f"{BASE_URL}/api/admin/chats?limit=1", headers=auth_headers)
        if chats_response.status_code == 200 and len(chats_response.json().get("chats", [])) > 0:
            chat_id = chats_response.json()["chats"][0]["chat_id"]
            
            # Get messages for that chat
            response = requests.get(f"{BASE_URL}/api/admin/chats/{chat_id}/messages", headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "messages" in data
            assert "chat_id" in data
            print(f"Chat {chat_id}: {len(data['messages'])} messages")
        else:
            pytest.skip("No chats available to test message retrieval")
    
    def test_moderation_requires_auth(self):
        """Test that moderation requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/chats")
        assert response.status_code == 401


class TestAnnouncements:
    """Test Announcements - create, edit, delete announcements"""
    
    def test_create_announcement(self, auth_headers):
        """Test creating a new announcement"""
        unique_id = str(uuid.uuid4())[:8]
        announcement_data = {
            "title": f"TEST_Announcement_{unique_id}",
            "message": "This is a test announcement message",
            "type": "info",
            "is_active": True
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/announcements", 
                                json=announcement_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "announcement" in data
        assert data["announcement"]["title"] == announcement_data["title"]
        assert data["announcement"]["message"] == announcement_data["message"]
        assert data["announcement"]["type"] == "info"
        assert data["announcement"]["is_active"] == True
        assert "id" in data["announcement"]
        
        print(f"Created announcement: {data['announcement']['id']}")
        return data["announcement"]["id"]
    
    def test_get_all_announcements(self, auth_headers):
        """Test getting all announcements"""
        response = requests.get(f"{BASE_URL}/api/admin/announcements", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "announcements" in data
        assert isinstance(data["announcements"], list)
        
        print(f"Total announcements: {len(data['announcements'])}")
    
    def test_update_announcement(self, auth_headers):
        """Test updating an announcement"""
        # First create an announcement
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "title": f"TEST_Update_{unique_id}",
            "message": "Original message",
            "type": "info",
            "is_active": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/announcements", 
                                       json=create_data, headers=auth_headers)
        assert create_response.status_code == 200
        announcement_id = create_response.json()["announcement"]["id"]
        
        # Update it
        update_data = {
            "title": f"TEST_Updated_{unique_id}",
            "message": "Updated message",
            "type": "warning",
            "is_active": False
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/announcements/{announcement_id}", 
                               json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data  # Response contains a success message
        
        # Verify update by fetching all announcements
        get_response = requests.get(f"{BASE_URL}/api/admin/announcements", headers=auth_headers)
        announcements = get_response.json().get("announcements", [])
        updated = next((a for a in announcements if a["id"] == announcement_id), None)
        assert updated is not None
        assert updated["title"] == update_data["title"]
        assert updated["type"] == "warning"
        
        print(f"Updated announcement: {announcement_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/announcements/{announcement_id}", headers=auth_headers)
    
    def test_delete_announcement(self, auth_headers):
        """Test deleting an announcement"""
        # First create an announcement
        unique_id = str(uuid.uuid4())[:8]
        create_data = {
            "title": f"TEST_Delete_{unique_id}",
            "message": "To be deleted",
            "type": "info",
            "is_active": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/announcements", 
                                       json=create_data, headers=auth_headers)
        assert create_response.status_code == 200
        announcement_id = create_response.json()["announcement"]["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/admin/announcements/{announcement_id}", 
                                  headers=auth_headers)
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/admin/announcements", headers=auth_headers)
        announcements = get_response.json().get("announcements", [])
        assert not any(a["id"] == announcement_id for a in announcements)
        
        print(f"Deleted announcement: {announcement_id}")
    
    def test_get_active_announcements_public(self):
        """Test that active announcements are publicly accessible"""
        response = requests.get(f"{BASE_URL}/api/announcements/active")
        assert response.status_code == 200
        
        data = response.json()
        assert "announcements" in data
        print(f"Public active announcements: {len(data['announcements'])}")


class TestNotifications:
    """Test Notifications - send notifications to users or broadcast"""
    
    def test_send_notification_to_user(self, auth_headers):
        """Test sending notification to a specific user"""
        unique_id = str(uuid.uuid4())[:8]
        notification_data = {
            "user_id": "test_user_123",
            "title": f"TEST_Notification_{unique_id}",
            "message": "This is a test notification",
            "type": "info"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/notifications", 
                                json=notification_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "notification" in data
        assert data["notification"]["title"] == notification_data["title"]
        assert data["notification"]["user_id"] == "test_user_123"
        
        print(f"Sent notification: {data['notification']['id']}")
    
    def test_send_broadcast_notification(self, auth_headers):
        """Test sending broadcast notification (to all users)"""
        unique_id = str(uuid.uuid4())[:8]
        notification_data = {
            "user_id": None,  # None means broadcast to all
            "title": f"TEST_Broadcast_{unique_id}",
            "message": "This is a broadcast notification",
            "type": "info"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/notifications", 
                                json=notification_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "notification" in data
        assert data["notification"]["user_id"] is None  # Broadcast
        
        print(f"Sent broadcast notification: {data['notification']['id']}")
    
    def test_get_admin_notifications_list(self, auth_headers):
        """Test getting list of sent notifications"""
        response = requests.get(f"{BASE_URL}/api/admin/notifications", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "notifications" in data
        print(f"Total notifications: {len(data['notifications'])}")


class TestRevenueDashboard:
    """Test Revenue Dashboard - mocked revenue data and subscription breakdown"""
    
    def test_revenue_analytics_returns_mocked_data(self, auth_headers):
        """Test revenue analytics endpoint returns expected mocked data"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/revenue", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify all expected fields
        assert "monthly_revenue" in data
        assert "annual_projected" in data
        assert "subscription_breakdown" in data
        assert "revenue_trend" in data
        
        # Should indicate data is mocked
        assert "is_mocked" in data
        assert data["is_mocked"] == True  # Revenue data is mocked
        
        # Verify subscription breakdown
        breakdown = data["subscription_breakdown"]
        assert "free" in breakdown
        assert "premium" in breakdown
        assert "ultimate" in breakdown
        
        # Verify revenue trend
        assert isinstance(data["revenue_trend"], list)
        if len(data["revenue_trend"]) > 0:
            month = data["revenue_trend"][0]
            assert "month" in month
            assert "revenue" in month
        
        print(f"Revenue: ${data['monthly_revenue']}/month, Mocked: {data['is_mocked']}")
    
    def test_revenue_requires_auth(self):
        """Test that revenue analytics requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics/revenue")
        assert response.status_code == 401


class TestAdminsManagement:
    """Test Admins tab - view all admins, create new admin (super admin only)"""
    
    def test_get_all_admins(self, auth_headers):
        """Test getting list of all admins"""
        response = requests.get(f"{BASE_URL}/api/admin/admins", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "admins" in data
        assert isinstance(data["admins"], list)
        
        # There should be at least 1 admin (the default one)
        assert len(data["admins"]) >= 1
        
        # Verify admin structure
        admin = data["admins"][0]
        assert "id" in admin
        assert "email" in admin
        assert "username" in admin
        # Password hash should NOT be returned
        assert "password_hash" not in admin
        
        print(f"Total admins: {len(data['admins'])}")
    
    def test_create_new_admin(self, auth_headers):
        """Test creating a new admin (super admin only)"""
        unique_id = str(uuid.uuid4())[:8]
        admin_data = {
            "email": f"test_admin_{unique_id}@test.com",
            "username": f"TEST_Admin_{unique_id}",
            "password": "testpass123",
            "role": "moderator"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/admins", 
                                json=admin_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "admin" in data
        assert data["admin"]["email"] == admin_data["email"]
        assert data["admin"]["username"] == admin_data["username"]
        assert "password_hash" not in data["admin"]  # Should not expose hash
        
        admin_id = data["admin"]["id"]
        print(f"Created admin: {admin_id}")
        
        # Cleanup - delete the test admin
        delete_response = requests.delete(f"{BASE_URL}/api/admin/admins/{admin_id}", headers=auth_headers)
        assert delete_response.status_code in [200, 403]  # 403 if trying to delete self
    
    def test_delete_admin(self, auth_headers):
        """Test deleting an admin"""
        # First create an admin
        unique_id = str(uuid.uuid4())[:8]
        admin_data = {
            "email": f"delete_admin_{unique_id}@test.com",
            "username": f"TEST_Delete_Admin_{unique_id}",
            "password": "testpass123",
            "role": "moderator"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/admins", 
                                       json=admin_data, headers=auth_headers)
        assert create_response.status_code == 200
        admin_id = create_response.json()["admin"]["id"]
        
        # Delete the admin
        response = requests.delete(f"{BASE_URL}/api/admin/admins/{admin_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/admin/admins", headers=auth_headers)
        admins = get_response.json().get("admins", [])
        assert not any(a["id"] == admin_id for a in admins)
        
        print(f"Deleted admin: {admin_id}")


class TestActivityLogs:
    """Test Activity Logs - showing all admin actions with timestamps"""
    
    def test_get_activity_logs(self, auth_headers):
        """Test getting activity logs"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-logs?limit=100", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
        
        # Verify log structure if there are logs
        if len(data["logs"]) > 0:
            log = data["logs"][0]
            assert "id" in log
            assert "admin_email" in log or "admin_id" in log
            assert "action" in log
            assert "timestamp" in log
        
        print(f"Activity logs: {len(data['logs'])} entries")
    
    def test_get_activity_logs_summary(self, auth_headers):
        """Test getting activity logs summary"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-logs/summary", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_logs" in data
        assert "recent_activity_count" in data
        
        print(f"Logs summary: {data['total_logs']} total, {data['recent_activity_count']} recent")
    
    def test_activity_logs_require_auth(self):
        """Test that activity logs require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/activity-logs")
        assert response.status_code == 401


class TestCharacterEdit:
    """Test Character Edit functionality from Characters tab"""
    
    def test_get_all_characters_admin(self, auth_headers):
        """Test getting all characters (default and custom) as admin"""
        response = requests.get(f"{BASE_URL}/api/admin/characters", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "default_characters" in data
        assert "custom_characters" in data
        assert "total_default" in data
        assert "total_custom" in data
        
        print(f"Characters: {data['total_default']} default, {data['total_custom']} custom")
    
    def test_update_character(self, auth_headers):
        """Test updating a character's details"""
        # First get a character to update
        chars_response = requests.get(f"{BASE_URL}/api/admin/characters", headers=auth_headers)
        assert chars_response.status_code == 200
        
        default_chars = chars_response.json().get("default_characters", [])
        if len(default_chars) == 0:
            pytest.skip("No characters available to test update")
        
        char_id = default_chars[0]["id"]
        original_name = default_chars[0]["name"]
        
        # Update the character
        update_data = {
            "description": "Updated description for testing",
            "occupation": "Test Occupation"
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/characters/{char_id}?is_custom=false", 
                               json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "character" in data
        assert data["character"]["description"] == update_data["description"]
        
        print(f"Updated character: {original_name} (ID: {char_id})")
        
        # Revert the change
        revert_data = {
            "description": default_chars[0].get("description", ""),
            "occupation": default_chars[0].get("occupation", "")
        }
        requests.put(f"{BASE_URL}/api/admin/characters/{char_id}?is_custom=false", 
                    json=revert_data, headers=auth_headers)


class TestCleanup:
    """Cleanup test data created during testing"""
    
    def test_cleanup_test_announcements(self, auth_headers):
        """Clean up TEST_ prefixed announcements"""
        response = requests.get(f"{BASE_URL}/api/admin/announcements", headers=auth_headers)
        if response.status_code == 200:
            announcements = response.json().get("announcements", [])
            deleted = 0
            for ann in announcements:
                if ann.get("title", "").startswith("TEST_"):
                    del_response = requests.delete(
                        f"{BASE_URL}/api/admin/announcements/{ann['id']}", 
                        headers=auth_headers
                    )
                    if del_response.status_code == 200:
                        deleted += 1
            print(f"Cleaned up {deleted} test announcements")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
