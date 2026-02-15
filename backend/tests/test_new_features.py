"""
Test file for new features: Favorites, Custom Characters, and Standalone Image Generation APIs
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_EMAIL = "dropdown_test@example.com"
TEST_PASSWORD = "test123"
TEST_USER_ID = "89e4e973-6cae-4cf1-b8eb-1956b4f98c82"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token by logging in"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token"), data.get("user", {}).get("id", TEST_USER_ID)
    pytest.skip("Authentication failed - skipping authenticated tests")
    return None, None


@pytest.fixture(scope="module")
def test_character_id(api_client):
    """Get a valid character ID for testing"""
    response = api_client.get(f"{BASE_URL}/api/characters?category=Girls")
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]["id"]
    pytest.skip("No characters available for testing")
    return None


class TestFavoritesAPI:
    """Test suite for /api/favorites endpoints"""
    
    def test_add_favorite(self, api_client, auth_token, test_character_id):
        """POST /api/favorites/add - Add character to favorites"""
        token, user_id = auth_token
        
        response = api_client.post(f"{BASE_URL}/api/favorites/add", json={
            "user_id": user_id,
            "character_id": test_character_id
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "favorited" in data
        assert data["favorited"] == True
        print(f"✓ Added character {test_character_id} to favorites for user {user_id}")
    
    def test_add_favorite_duplicate(self, api_client, auth_token, test_character_id):
        """POST /api/favorites/add - Adding duplicate should handle gracefully"""
        token, user_id = auth_token
        
        # Add same character again
        response = api_client.post(f"{BASE_URL}/api/favorites/add", json={
            "user_id": user_id,
            "character_id": test_character_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["favorited"] == True
        assert "Already in favorites" in data.get("message", "")
        print("✓ Duplicate favorite handled correctly")
    
    def test_check_favorite_status(self, api_client, auth_token, test_character_id):
        """GET /api/favorites/check/{user_id}/{character_id} - Check if favorited"""
        token, user_id = auth_token
        
        response = api_client.get(f"{BASE_URL}/api/favorites/check/{user_id}/{test_character_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "favorited" in data
        assert data["favorited"] == True
        print(f"✓ Favorite check returned: {data['favorited']}")
    
    def test_get_favorites_list(self, api_client, auth_token):
        """GET /api/favorites/{user_id} - Get all favorites"""
        token, user_id = auth_token
        
        response = api_client.get(f"{BASE_URL}/api/favorites/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "favorites" in data
        assert isinstance(data["favorites"], list)
        print(f"✓ Retrieved {len(data['favorites'])} favorites")
        
        # Verify favorite structure has character details
        if len(data["favorites"]) > 0:
            fav = data["favorites"][0]
            assert "name" in fav
            assert "id" in fav
            print(f"  First favorite: {fav['name']}")
    
    def test_remove_favorite(self, api_client, auth_token, test_character_id):
        """POST /api/favorites/remove - Remove from favorites"""
        token, user_id = auth_token
        
        response = api_client.post(f"{BASE_URL}/api/favorites/remove", json={
            "user_id": user_id,
            "character_id": test_character_id
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["favorited"] == False
        print(f"✓ Removed character from favorites")
    
    def test_check_removed_favorite(self, api_client, auth_token, test_character_id):
        """Verify favorite was removed"""
        token, user_id = auth_token
        
        response = api_client.get(f"{BASE_URL}/api/favorites/check/{user_id}/{test_character_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["favorited"] == False
        print("✓ Favorite removal verified")


class TestCustomCharactersAPI:
    """Test suite for /api/characters custom character endpoints"""
    
    created_character_id = None
    
    def test_create_custom_character(self, api_client, auth_token):
        """POST /api/characters/create - Create a custom character"""
        token, user_id = auth_token
        
        test_character = {
            "user_id": user_id,
            "name": f"TEST_CustomChar_{uuid.uuid4().hex[:6]}",
            "age": 25,
            "personality": "Friendly and helpful test character with a warm personality",
            "description": "A test character created for API testing",
            "occupation": "Test Assistant",
            "traits": ["Friendly", "Helpful", "Creative"],
            "avatar_prompt": None  # Skip avatar generation for faster test
        }
        
        response = api_client.post(f"{BASE_URL}/api/characters/create", json=test_character)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "character" in data
        character = data["character"]
        assert character["name"] == test_character["name"]
        assert character["age"] == test_character["age"]
        assert character["is_custom"] == True
        assert character["user_id"] == user_id
        assert "id" in character
        
        # Store for later tests
        TestCustomCharactersAPI.created_character_id = character["id"]
        print(f"✓ Created custom character: {character['name']} (ID: {character['id']})")
    
    def test_get_my_characters(self, api_client, auth_token):
        """GET /api/characters/my/{user_id} - Get user's custom characters"""
        token, user_id = auth_token
        
        response = api_client.get(f"{BASE_URL}/api/characters/my/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data
        assert isinstance(data["characters"], list)
        print(f"✓ Retrieved {len(data['characters'])} custom characters")
        
        # Verify our test character is in the list
        if TestCustomCharactersAPI.created_character_id:
            char_ids = [c["id"] for c in data["characters"]]
            assert TestCustomCharactersAPI.created_character_id in char_ids
            print("✓ Created character found in my characters list")
    
    def test_get_custom_character_by_id(self, api_client):
        """GET /api/characters/custom/{character_id} - Get single custom character"""
        if not TestCustomCharactersAPI.created_character_id:
            pytest.skip("No character created to fetch")
        
        response = api_client.get(f"{BASE_URL}/api/characters/custom/{TestCustomCharactersAPI.created_character_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TestCustomCharactersAPI.created_character_id
        assert data["is_custom"] == True
        print(f"✓ Retrieved custom character: {data['name']}")
    
    def test_custom_character_not_found(self, api_client):
        """GET /api/characters/custom/{invalid_id} - Should return 404"""
        response = api_client.get(f"{BASE_URL}/api/characters/custom/invalid-character-id-12345")
        
        assert response.status_code == 404
        print("✓ Invalid character ID returns 404")
    
    def test_delete_custom_character(self, api_client, auth_token):
        """DELETE /api/characters/custom/{character_id} - Delete custom character"""
        token, user_id = auth_token
        
        if not TestCustomCharactersAPI.created_character_id:
            pytest.skip("No character created to delete")
        
        response = api_client.delete(
            f"{BASE_URL}/api/characters/custom/{TestCustomCharactersAPI.created_character_id}?user_id={user_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()
        print(f"✓ Deleted custom character")
    
    def test_deleted_character_not_found(self, api_client):
        """Verify deleted character returns 404"""
        if not TestCustomCharactersAPI.created_character_id:
            pytest.skip("No character to verify deletion")
        
        response = api_client.get(f"{BASE_URL}/api/characters/custom/{TestCustomCharactersAPI.created_character_id}")
        
        assert response.status_code == 404
        print("✓ Deleted character returns 404")


class TestImagesAPI:
    """Test suite for /api/images endpoints"""
    
    # Note: Skipping actual image generation as it requires AI API and takes time
    # Testing only the GET endpoints and structure
    
    def test_get_my_images_empty(self, api_client, auth_token):
        """GET /api/images/my/{user_id} - Get user's generated images (may be empty)"""
        token, user_id = auth_token
        
        response = api_client.get(f"{BASE_URL}/api/images/my/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)
        print(f"✓ Retrieved {len(data['images'])} user images")
    
    def test_image_generate_endpoint_exists(self, api_client, auth_token):
        """POST /api/images/generate - Verify endpoint exists (send minimal request)"""
        token, user_id = auth_token
        
        # Send a request with empty prompt to verify endpoint structure
        response = api_client.post(f"{BASE_URL}/api/images/generate", json={
            "user_id": user_id,
            "prompt": "",
            "style": "realistic"
        })
        
        # Empty prompt might fail with 500 or 422, but endpoint should exist (not 404)
        assert response.status_code != 404, "Image generation endpoint should exist"
        print(f"✓ Image generation endpoint exists (status: {response.status_code})")
    
    def test_delete_image_not_found(self, api_client, auth_token):
        """DELETE /api/images/{image_id} - Non-existent image returns 404"""
        token, user_id = auth_token
        
        response = api_client.delete(f"{BASE_URL}/api/images/nonexistent-image-id?user_id={user_id}")
        
        assert response.status_code == 404
        print("✓ Non-existent image deletion returns 404")


class TestFavoriteToggleOnChat:
    """Test favorite toggle on chat page (using check endpoint)"""
    
    def test_favorite_workflow(self, api_client, auth_token, test_character_id):
        """Full workflow: Check -> Add -> Check -> Remove -> Check"""
        token, user_id = auth_token
        
        # 1. Check initial status
        resp1 = api_client.get(f"{BASE_URL}/api/favorites/check/{user_id}/{test_character_id}")
        assert resp1.status_code == 200
        initial_status = resp1.json()["favorited"]
        print(f"  Initial favorite status: {initial_status}")
        
        # 2. Toggle (add if not favorited, remove if favorited)
        if not initial_status:
            resp2 = api_client.post(f"{BASE_URL}/api/favorites/add", json={
                "user_id": user_id,
                "character_id": test_character_id
            })
        else:
            resp2 = api_client.post(f"{BASE_URL}/api/favorites/remove", json={
                "user_id": user_id,
                "character_id": test_character_id
            })
        assert resp2.status_code == 200
        
        # 3. Check new status
        resp3 = api_client.get(f"{BASE_URL}/api/favorites/check/{user_id}/{test_character_id}")
        assert resp3.status_code == 200
        new_status = resp3.json()["favorited"]
        assert new_status == (not initial_status)
        print(f"  After toggle: {new_status}")
        
        # 4. Toggle back
        if new_status:
            resp4 = api_client.post(f"{BASE_URL}/api/favorites/remove", json={
                "user_id": user_id,
                "character_id": test_character_id
            })
        else:
            resp4 = api_client.post(f"{BASE_URL}/api/favorites/add", json={
                "user_id": user_id,
                "character_id": test_character_id
            })
        assert resp4.status_code == 200
        
        # 5. Verify back to initial
        resp5 = api_client.get(f"{BASE_URL}/api/favorites/check/{user_id}/{test_character_id}")
        assert resp5.status_code == 200
        final_status = resp5.json()["favorited"]
        assert final_status == initial_status
        print(f"✓ Favorite toggle workflow completed - back to initial: {final_status}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
