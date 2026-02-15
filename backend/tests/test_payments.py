"""
Payment Endpoints Tests - Stripe & PayPal Integration
Tests for subscription plans, checkout sessions, payment status, and user subscriptions.
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_USER_EMAIL = f"testpay_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPass123"
TEST_USER_NAME = "Test Payment User"

class TestPaymentPlans:
    """Test subscription plans endpoint"""
    
    def test_get_subscription_plans(self):
        """Test /api/payments/plans returns all 4 plans"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        
        plans = data["plans"]
        
        # Verify all 4 plans exist
        expected_plans = ["premium_monthly", "premium_yearly", "ultimate_monthly", "ultimate_yearly"]
        for plan_id in expected_plans:
            assert plan_id in plans, f"Plan {plan_id} should exist"
        
        print(f"SUCCESS: Found {len(plans)} plans: {list(plans.keys())}")
    
    def test_plan_structure(self):
        """Test that each plan has required fields"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        assert response.status_code == 200
        
        plans = response.json()["plans"]
        required_fields = ["name", "amount", "currency", "interval", "features"]
        
        for plan_id, plan in plans.items():
            for field in required_fields:
                assert field in plan, f"Plan {plan_id} missing field '{field}'"
            
            # Verify amount is a float
            assert isinstance(plan["amount"], (int, float)), f"Plan {plan_id} amount should be numeric"
            assert plan["amount"] > 0, f"Plan {plan_id} amount should be positive"
            
            # Verify currency
            assert plan["currency"] == "usd", f"Plan {plan_id} currency should be 'usd'"
            
            # Verify interval
            assert plan["interval"] in ["monthly", "yearly"], f"Plan {plan_id} interval should be 'monthly' or 'yearly'"
            
            # Verify features is a list
            assert isinstance(plan["features"], list), f"Plan {plan_id} features should be a list"
            assert len(plan["features"]) > 0, f"Plan {plan_id} should have at least one feature"
        
        print("SUCCESS: All plans have valid structure")
    
    def test_plan_prices(self):
        """Test that plan prices are correct"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        assert response.status_code == 200
        
        plans = response.json()["plans"]
        
        # Expected prices
        expected_prices = {
            "premium_monthly": 9.99,
            "premium_yearly": 59.99,
            "ultimate_monthly": 19.99,
            "ultimate_yearly": 119.99
        }
        
        for plan_id, expected_price in expected_prices.items():
            actual_price = plans[plan_id]["amount"]
            assert actual_price == expected_price, f"Plan {plan_id} price should be ${expected_price}, got ${actual_price}"
        
        print("SUCCESS: All plan prices are correct")


class TestPaymentCheckout:
    """Test checkout session creation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create test user and get auth token"""
        # Try to signup
        signup_data = {
            "email": TEST_USER_EMAIL,
            "username": TEST_USER_NAME,
            "password": TEST_USER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 400:  # Email exists, try login
            login_data = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
            if response.status_code == 200:
                return response.json().get("token")
        
        # Try with existing test user
        login_data = {"email": "testpay2@test.com", "password": "TestPass123"}
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("token")
        
        # Create new user with different email
        new_email = f"testpay_{uuid.uuid4().hex[:8]}@test.com"
        signup_data = {"email": new_email, "username": "Test User", "password": "TestPass123"}
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        if response.status_code == 200:
            return response.json().get("token")
        
        pytest.skip("Could not create or login test user")
    
    def test_checkout_requires_auth(self):
        """Test that checkout requires authentication"""
        checkout_data = {
            "plan_id": "premium_monthly",
            "origin_url": "https://example.com",
            "payment_method": "stripe"
        }
        response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Checkout requires authentication")
    
    def test_checkout_invalid_plan(self, auth_token):
        """Test checkout with invalid plan"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        checkout_data = {
            "plan_id": "invalid_plan",
            "origin_url": "https://example.com",
            "payment_method": "stripe"
        }
        response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data, headers=headers)
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        print("SUCCESS: Invalid plan returns 400")
    
    def test_stripe_checkout_session_creation(self, auth_token):
        """Test Stripe checkout session creation"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        checkout_data = {
            "plan_id": "premium_monthly",
            "origin_url": "https://example.com",
            "payment_method": "stripe"
        }
        response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data, headers=headers)
        
        # Should return 200 with checkout URL
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data, "Response should contain checkout_url"
        assert "session_id" in data, "Response should contain session_id"
        assert data["payment_method"] == "stripe", "Payment method should be stripe"
        
        # Checkout URL should point to Stripe
        assert "stripe.com" in data["checkout_url"] or "checkout" in data["checkout_url"].lower(), \
            "Checkout URL should point to Stripe"
        
        print(f"SUCCESS: Stripe checkout created with session_id: {data['session_id'][:20]}...")
    
    def test_paypal_checkout_mock(self, auth_token):
        """Test PayPal checkout (mock mode)"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        checkout_data = {
            "plan_id": "ultimate_monthly",
            "origin_url": "https://example.com",
            "payment_method": "paypal"
        }
        response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "checkout_url" in data, "Response should contain checkout_url"
        assert "session_id" in data, "Response should contain session_id"
        assert data["payment_method"] == "paypal", "Payment method should be paypal"
        
        # PayPal in demo mode should have a note
        if "note" in data:
            print(f"PayPal Note: {data['note']}")
        
        print(f"SUCCESS: PayPal checkout created with session_id: {data['session_id'][:20]}...")
    
    def test_checkout_all_plans(self, auth_token):
        """Test checkout works for all 4 plans"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        plans = ["premium_monthly", "premium_yearly", "ultimate_monthly", "ultimate_yearly"]
        
        for plan_id in plans:
            checkout_data = {
                "plan_id": plan_id,
                "origin_url": "https://example.com",
                "payment_method": "stripe"
            }
            response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data, headers=headers)
            assert response.status_code == 200, f"Checkout failed for plan {plan_id}: {response.text}"
        
        print(f"SUCCESS: Checkout works for all {len(plans)} plans")


class TestPaymentStatus:
    """Test payment status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_and_session(self):
        """Create test user, get token, and create a checkout session"""
        # Create or login user
        email = f"testpay_status_{uuid.uuid4().hex[:8]}@test.com"
        signup_data = {"email": email, "username": "Test Status User", "password": "TestPass123"}
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        
        if response.status_code == 200:
            token = response.json().get("token")
        else:
            pytest.skip("Could not create test user")
        
        # Create a checkout session
        headers = {"Authorization": f"Bearer {token}"}
        checkout_data = {
            "plan_id": "premium_monthly",
            "origin_url": "https://example.com",
            "payment_method": "stripe"
        }
        response = requests.post(f"{BASE_URL}/api/payments/checkout", json=checkout_data, headers=headers)
        
        if response.status_code == 200:
            session_id = response.json().get("session_id")
            return {"token": token, "session_id": session_id}
        else:
            pytest.skip("Could not create checkout session")
    
    def test_payment_status_valid_session(self, auth_and_session):
        """Test getting payment status for valid session"""
        if not auth_and_session:
            pytest.skip("No session data")
        
        session_id = auth_and_session["session_id"]
        
        response = requests.get(f"{BASE_URL}/api/payments/status/{session_id}?payment_method=stripe")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "session_id" in data, "Response should contain session_id"
        assert "status" in data, "Response should contain status"
        assert "payment_status" in data, "Response should contain payment_status"
        
        print(f"SUCCESS: Payment status retrieved - status: {data['status']}, payment_status: {data['payment_status']}")
    
    def test_payment_status_invalid_session(self):
        """Test getting payment status for invalid session"""
        fake_session_id = str(uuid.uuid4())
        
        response = requests.get(f"{BASE_URL}/api/payments/status/{fake_session_id}?payment_method=stripe")
        assert response.status_code == 404, f"Expected 404 for invalid session, got {response.status_code}"
        
        print("SUCCESS: Invalid session returns 404")


class TestUserSubscription:
    """Test user subscription status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create test user and get auth token"""
        email = f"testpay_sub_{uuid.uuid4().hex[:8]}@test.com"
        signup_data = {"email": email, "username": "Test Sub User", "password": "TestPass123"}
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        
        pytest.skip("Could not create test user")
    
    def test_subscription_requires_auth(self):
        """Test that subscription status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/payments/user-subscription")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: User subscription requires authentication")
    
    def test_new_user_has_free_plan(self, auth_token):
        """Test that new user has free plan by default"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/user-subscription", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "has_subscription" in data, "Response should contain has_subscription"
        assert "subscription" in data, "Response should contain subscription"
        
        # New user should not have premium subscription
        sub = data["subscription"]
        assert sub["plan_id"] == "free" or data["has_subscription"] == False, \
            "New user should have free plan or no subscription"
        
        print(f"SUCCESS: New user subscription status - has_subscription: {data['has_subscription']}, plan: {sub.get('plan_id', 'free')}")


class TestPaymentHistory:
    """Test payment history endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Create test user and get auth token"""
        email = f"testpay_hist_{uuid.uuid4().hex[:8]}@test.com"
        signup_data = {"email": email, "username": "Test Hist User", "password": "TestPass123"}
        response = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        
        pytest.skip("Could not create test user")
    
    def test_history_requires_auth(self):
        """Test that payment history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/payments/history")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Payment history requires authentication")
    
    def test_get_payment_history(self, auth_token):
        """Test getting payment history for user"""
        if not auth_token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payments/history", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "transactions" in data, "Response should contain transactions"
        assert isinstance(data["transactions"], list), "Transactions should be a list"
        
        print(f"SUCCESS: Payment history retrieved with {len(data['transactions'])} transactions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
