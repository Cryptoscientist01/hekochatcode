"""
Tests for Admin Panel and Blog features
- Admin login at /optimus with credentials admin@admin.com / admin123
- Admin Dashboard showing analytics
- Admin Blog Manager - list posts, create/edit/delete posts
- Public Blog endpoints - list posts, get by slug, categories, tags, related posts
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin123"


class TestAdminLogin:
    """Test admin authentication endpoints"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "Token not returned"
        assert "admin" in data, "Admin data not returned"
        assert data["admin"]["email"] == ADMIN_EMAIL
        assert "password_hash" not in data["admin"], "Password hash should not be exposed"
        print(f"✓ Admin login successful, token received")
        
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        print(f"✓ Wrong password correctly rejected")
    
    def test_admin_login_wrong_email(self):
        """Test admin login with wrong email"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": "wrong@email.com",
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 401
        print(f"✓ Wrong email correctly rejected")


@pytest.fixture(scope="class")
def admin_token():
    """Get admin token for authenticated requests"""
    response = requests.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.fail(f"Could not get admin token: {response.text}")


class TestAdminVerify:
    """Test admin token verification"""
    
    def test_admin_verify_valid_token(self, admin_token):
        """Test verifying a valid admin token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "admin" in data
        assert data["admin"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin token verified successfully")
    
    def test_admin_verify_no_token(self):
        """Test verify endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/admin/verify")
        assert response.status_code == 401
        print(f"✓ Request without token correctly rejected")
    
    def test_admin_verify_invalid_token(self):
        """Test verify endpoint with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/verify",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        print(f"✓ Invalid token correctly rejected")


class TestAdminAnalytics:
    """Test admin analytics endpoints"""
    
    def test_get_analytics(self, admin_token):
        """Test fetching platform analytics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Analytics failed: {response.text}"
        data = response.json()
        
        # Verify all expected fields
        expected_fields = [
            "total_users", "total_characters", "total_custom_characters",
            "total_messages", "total_images", "total_favorites",
            "recent_users", "users_by_day"
        ]
        for field in expected_fields:
            assert field in data, f"Missing analytics field: {field}"
        
        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_characters"], int)
        assert isinstance(data["users_by_day"], list)
        
        print(f"✓ Analytics retrieved - Users: {data['total_users']}, Characters: {data['total_characters']}, Messages: {data['total_messages']}")
    
    def test_analytics_requires_auth(self):
        """Test that analytics endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401
        print(f"✓ Analytics correctly requires authentication")


class TestAdminUsers:
    """Test admin user management endpoints"""
    
    def test_get_all_users(self, admin_token):
        """Test fetching all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get users failed: {response.text}"
        data = response.json()
        
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        print(f"✓ Retrieved {len(data['users'])} users (total: {data['total']})")
    
    def test_users_pagination(self, admin_token):
        """Test user list pagination"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users?skip=0&limit=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "skip" in data
        assert "limit" in data
        print(f"✓ Pagination working - skip: {data['skip']}, limit: {data['limit']}")


class TestAdminCharacters:
    """Test admin character management endpoints"""
    
    def test_get_all_characters(self, admin_token):
        """Test fetching all characters"""
        response = requests.get(
            f"{BASE_URL}/api/admin/characters",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get characters failed: {response.text}"
        data = response.json()
        
        assert "default_characters" in data
        assert "custom_characters" in data
        assert "total_default" in data
        assert "total_custom" in data
        
        print(f"✓ Retrieved {data['total_default']} default + {data['total_custom']} custom characters")


class TestPublicBlogEndpoints:
    """Test public blog endpoints (no auth required)"""
    
    def test_get_blog_posts(self):
        """Test fetching published blog posts"""
        response = requests.get(f"{BASE_URL}/api/blog/posts")
        
        assert response.status_code == 200, f"Get blog posts failed: {response.text}"
        data = response.json()
        
        assert "posts" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        print(f"✓ Retrieved {len(data['posts'])} blog posts (total: {data['total']})")
        return data
    
    def test_get_blog_posts_pagination(self):
        """Test blog posts pagination"""
        response = requests.get(f"{BASE_URL}/api/blog/posts?page=1&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        print(f"✓ Blog pagination working")
    
    def test_get_blog_categories(self):
        """Test fetching blog categories"""
        response = requests.get(f"{BASE_URL}/api/blog/categories")
        
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        data = response.json()
        
        assert "categories" in data
        assert isinstance(data["categories"], list)
        print(f"✓ Retrieved {len(data['categories'])} categories")
    
    def test_get_blog_tags(self):
        """Test fetching blog tags"""
        response = requests.get(f"{BASE_URL}/api/blog/tags")
        
        assert response.status_code == 200, f"Get tags failed: {response.text}"
        data = response.json()
        
        assert "tags" in data
        assert isinstance(data["tags"], list)
        print(f"✓ Retrieved {len(data['tags'])} tags")


class TestAdminBlogCRUD:
    """Test admin blog post CRUD operations"""
    
    def test_create_blog_post(self, admin_token):
        """Test creating a new blog post"""
        test_slug = f"test-post-{uuid.uuid4().hex[:8]}"
        post_data = {
            "title": "Test Blog Post",
            "slug": test_slug,
            "content": "This is test content for the blog post.\n\n## Section 1\nSome content here.\n\n## Section 2\nMore content here.",
            "excerpt": "This is a test excerpt for the blog post.",
            "meta_description": "Test meta description for SEO",
            "meta_keywords": ["test", "blog", "ai"],
            "category": "Guides",
            "tags": ["testing", "automation"],
            "status": "draft"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json=post_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Create blog post failed: {response.text}"
        data = response.json()
        
        assert "post" in data
        assert "message" in data
        assert data["post"]["title"] == post_data["title"]
        assert data["post"]["slug"] == test_slug
        
        post_id = data["post"]["id"]
        print(f"✓ Created blog post with ID: {post_id}")
        
        return post_id, test_slug
    
    def test_get_admin_blog_posts(self, admin_token):
        """Test fetching all blog posts including drafts (admin)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/blog/posts",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Get admin blog posts failed: {response.text}"
        data = response.json()
        
        assert "posts" in data
        assert "total" in data
        print(f"✓ Admin retrieved {len(data['posts'])} blog posts (including drafts)")
        return data["posts"]
    
    def test_update_blog_post(self, admin_token):
        """Test updating a blog post"""
        # First create a post
        test_slug = f"update-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Original Title",
                "slug": test_slug,
                "content": "Original content",
                "excerpt": "Original excerpt",
                "meta_description": "Original meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert create_response.status_code == 200
        post_id = create_response.json()["post"]["id"]
        
        # Now update it
        update_data = {
            "title": "Updated Title",
            "content": "Updated content here",
            "status": "published"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated_post = update_response.json()["post"]
        
        assert updated_post["title"] == "Updated Title"
        assert updated_post["status"] == "published"
        assert updated_post["published_at"] is not None
        
        print(f"✓ Updated blog post - title changed, status changed to published")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        return post_id
    
    def test_get_single_blog_post_admin(self, admin_token):
        """Test fetching a single blog post by ID (admin)"""
        # Create a test post first
        test_slug = f"single-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Single Post Test",
                "slug": test_slug,
                "content": "Test content",
                "excerpt": "Test excerpt",
                "meta_description": "Test meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Fetch the single post
        response = requests.get(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        post = response.json()
        assert post["id"] == post_id
        assert post["title"] == "Single Post Test"
        
        print(f"✓ Retrieved single blog post by ID")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_delete_blog_post(self, admin_token):
        """Test deleting a blog post"""
        # Create a post to delete
        test_slug = f"delete-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Post to Delete",
                "slug": test_slug,
                "content": "This will be deleted",
                "excerpt": "Delete test",
                "meta_description": "Delete test meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Delete the post
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json()["message"].lower()
        
        # Verify deletion - should return 404
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert verify_response.status_code == 404
        
        print(f"✓ Blog post deleted and verified")
    
    def test_duplicate_slug_rejected(self, admin_token):
        """Test that duplicate slugs are rejected"""
        test_slug = f"unique-slug-{uuid.uuid4().hex[:8]}"
        
        # Create first post
        first_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "First Post",
                "slug": test_slug,
                "content": "First content",
                "excerpt": "First excerpt",
                "meta_description": "First meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = first_response.json()["post"]["id"]
        
        # Try to create second post with same slug
        second_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Second Post",
                "slug": test_slug,
                "content": "Second content",
                "excerpt": "Second excerpt",
                "meta_description": "Second meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert second_response.status_code == 400
        assert "slug" in second_response.json()["detail"].lower()
        
        print(f"✓ Duplicate slug correctly rejected")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPublicBlogBySlug:
    """Test public blog post retrieval by slug"""
    
    def test_get_published_post_by_slug(self, admin_token):
        """Test fetching a published blog post by slug (public endpoint)"""
        test_slug = f"public-test-{uuid.uuid4().hex[:8]}"
        
        # Create and publish a post
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Public Test Post",
                "slug": test_slug,
                "content": "This is public content.\n\n## Section\nWith sections.",
                "excerpt": "Public test excerpt",
                "meta_description": "Public test meta for SEO",
                "meta_keywords": ["public", "test"],
                "category": "Guides",
                "tags": ["testing"],
                "status": "published"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Fetch via public endpoint
        public_response = requests.get(f"{BASE_URL}/api/blog/posts/{test_slug}")
        
        assert public_response.status_code == 200, f"Public fetch failed: {public_response.text}"
        post = public_response.json()
        
        assert post["title"] == "Public Test Post"
        assert post["slug"] == test_slug
        assert post["content"] is not None
        assert "meta_description" in post
        
        print(f"✓ Public blog post retrieved by slug")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_draft_post_not_visible_publicly(self, admin_token):
        """Test that draft posts are not visible via public endpoint"""
        test_slug = f"draft-test-{uuid.uuid4().hex[:8]}"
        
        # Create a draft post
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Draft Post",
                "slug": test_slug,
                "content": "Draft content",
                "excerpt": "Draft excerpt",
                "meta_description": "Draft meta",
                "category": "General",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Try to fetch via public endpoint - should fail
        public_response = requests.get(f"{BASE_URL}/api/blog/posts/{test_slug}")
        assert public_response.status_code == 404
        
        print(f"✓ Draft posts correctly hidden from public")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_nonexistent_slug_returns_404(self):
        """Test that nonexistent slug returns 404"""
        response = requests.get(f"{BASE_URL}/api/blog/posts/nonexistent-slug-xyz123")
        assert response.status_code == 404
        print(f"✓ Nonexistent slug returns 404")


class TestBlogFiltering:
    """Test blog filtering by category and tag"""
    
    def test_filter_by_category(self, admin_token):
        """Test filtering blog posts by category"""
        test_category = "TestCategory"
        test_slug = f"category-test-{uuid.uuid4().hex[:8]}"
        
        # Create a published post with specific category
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Category Filter Test",
                "slug": test_slug,
                "content": "Content",
                "excerpt": "Excerpt",
                "meta_description": "Meta",
                "category": test_category,
                "status": "published"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Filter by category
        filter_response = requests.get(f"{BASE_URL}/api/blog/posts?category={test_category}")
        
        assert filter_response.status_code == 200
        data = filter_response.json()
        
        # All returned posts should have the specified category
        for post in data["posts"]:
            assert post["category"] == test_category
        
        print(f"✓ Category filtering working")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_filter_by_tag(self, admin_token):
        """Test filtering blog posts by tag"""
        test_tag = "testtag123"
        test_slug = f"tag-test-{uuid.uuid4().hex[:8]}"
        
        # Create a published post with specific tag
        create_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Tag Filter Test",
                "slug": test_slug,
                "content": "Content",
                "excerpt": "Excerpt",
                "meta_description": "Meta",
                "category": "General",
                "tags": [test_tag, "other"],
                "status": "published"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        post_id = create_response.json()["post"]["id"]
        
        # Filter by tag
        filter_response = requests.get(f"{BASE_URL}/api/blog/posts?tag={test_tag}")
        
        assert filter_response.status_code == 200
        data = filter_response.json()
        
        # All returned posts should contain the tag
        for post in data["posts"]:
            assert test_tag in post.get("tags", [])
        
        print(f"✓ Tag filtering working")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/admin/blog/posts/{post_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestRelatedPosts:
    """Test related posts endpoint"""
    
    def test_get_related_posts(self, admin_token):
        """Test fetching related posts"""
        shared_category = "RelatedTestCat"
        
        # Create two related posts
        slug1 = f"related-test-1-{uuid.uuid4().hex[:8]}"
        slug2 = f"related-test-2-{uuid.uuid4().hex[:8]}"
        
        post1_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Related Post 1",
                "slug": slug1,
                "content": "Content 1",
                "excerpt": "Excerpt 1",
                "meta_description": "Meta 1",
                "category": shared_category,
                "tags": ["shared-tag"],
                "status": "published"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        post1_id = post1_response.json()["post"]["id"]
        
        post2_response = requests.post(
            f"{BASE_URL}/api/admin/blog/posts",
            json={
                "title": "Related Post 2",
                "slug": slug2,
                "content": "Content 2",
                "excerpt": "Excerpt 2",
                "meta_description": "Meta 2",
                "category": shared_category,
                "tags": ["shared-tag"],
                "status": "published"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        post2_id = post2_response.json()["post"]["id"]
        
        # Get related posts for post1
        related_response = requests.get(f"{BASE_URL}/api/blog/related/{slug1}")
        
        assert related_response.status_code == 200
        data = related_response.json()
        assert "related" in data
        
        print(f"✓ Related posts endpoint working, found {len(data['related'])} related")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blog/posts/{post1_id}", headers={"Authorization": f"Bearer {admin_token}"})
        requests.delete(f"{BASE_URL}/api/admin/blog/posts/{post2_id}", headers={"Authorization": f"Bearer {admin_token}"})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
