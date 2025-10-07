import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app
import time

@pytest.mark.asyncio
async def test_password_security():
    """Test password security requirements."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test password hashing (passwords should not be stored in plain text)
        r = await client.post("/auth/register", json={
            "employee_id": "SECURITY_TEST",
            "password": "securepassword123"
        })
        assert r.status_code == 201
        
        # Login to verify password works
        r = await client.post("/auth/login", json={
            "employee_id": "SECURITY_TEST",
            "password": "securepassword123"
        })
        assert r.status_code == 200
        
        # Wrong password should fail
        r = await client.post("/auth/login", json={
            "employee_id": "SECURITY_TEST",
            "password": "wrongpassword"
        })
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_jwt_token_security():
    """Test JWT token security."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register and login
        await client.post("/auth/register", json={
            "employee_id": "JWT_TEST",
            "password": "test123"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": "JWT_TEST",
            "password": "test123"
        })
        token = r.json()["access_token"]
        
        # Valid token should work
        r = await client.get("/auth/me", headers={
            "authorization": f"Bearer {token}"
        })
        assert r.status_code == 200
        
        # Invalid token should fail
        r = await client.get("/auth/me", headers={
            "authorization": "Bearer invalid.token.here"
        })
        assert r.status_code == 401
        
        # Missing Bearer prefix should fail
        r = await client.get("/auth/me", headers={
            "authorization": token
        })
        assert r.status_code == 401
        
        # No authorization header should fail
        r = await client.get("/auth/me")
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_role_based_access_security():
    """Test that role-based access control is properly enforced."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register simple user
        await client.post("/auth/register", json={
            "employee_id": "SIMPLE_SEC",
            "password": "test123",
            "role": "simple"
        })
        
        # Register admin user
        await client.post("/auth/register", json={
            "employee_id": "ADMIN_SEC",
            "password": "test123",
            "role": "admin"
        })
        
        # Get tokens
        r = await client.post("/auth/login", json={
            "employee_id": "SIMPLE_SEC",
            "password": "test123"
        })
        simple_token = r.json()["access_token"]
        
        r = await client.post("/auth/login", json={
            "employee_id": "ADMIN_SEC",
            "password": "test123"
        })
        admin_token = r.json()["access_token"]
        
        # Admin creates a session
        r = await client.post("/sessions/handout", 
                            headers={"authorization": f"Bearer {admin_token}"},
                            json={"threshold": 0.95, "notes": "Admin session"})
        admin_session_id = r.json()["session_id"]
        
        # Simple user should not be able to access admin's session details
        r = await client.get(f"/sessions/{admin_session_id}", 
                           headers={"authorization": f"Bearer {simple_token}"})
        assert r.status_code == 404
        
        # Simple user should not be able to perform operations on admin's session
        r = await client.post(f"/sessions/{admin_session_id}/handout/predict",
                            headers={"authorization": f"Bearer {simple_token}"},
                            json={"image": "test", "threshold": 0.95})
        assert r.status_code == 404

@pytest.mark.asyncio
async def test_input_sanitization():
    """Test that inputs are properly sanitized."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test SQL injection attempts in employee_id
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "null",
            "undefined"
        ]
        
        for malicious_input in malicious_inputs:
            r = await client.post("/auth/register", json={
                "employee_id": malicious_input,
                "password": "test123"
            })
            # Should either reject invalid input or handle it safely
            if r.status_code == 201:
                # If accepted, login should work normally (no injection occurred)
                r2 = await client.post("/auth/login", json={
                    "employee_id": malicious_input,
                    "password": "test123"
                })
                assert r2.status_code == 200

@pytest.mark.asyncio
async def test_rate_limiting_simulation():
    """Simulate potential rate limiting scenarios."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test multiple rapid requests (basic load test)
        start_time = time.time()
        responses = []
        
        for i in range(10):
            r = await client.post("/predict", json={
                "image": f"base64_test_{i}",
                "threshold": 0.95
            })
            responses.append(r.status_code)
        
        end_time = time.time()
        
        # All requests should succeed (no rate limiting implemented yet)
        assert all(status == 200 for status in responses)
        
        # Should complete reasonably quickly
        assert end_time - start_time < 10  # 10 seconds for 10 requests

@pytest.mark.asyncio
async def test_session_isolation():
    """Test that user sessions are properly isolated."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Create two users
        await client.post("/auth/register", json={
            "employee_id": "USER1_ISO",
            "password": "test123"
        })
        
        await client.post("/auth/register", json={
            "employee_id": "USER2_ISO",
            "password": "test123"
        })
        
        # Get tokens
        r = await client.post("/auth/login", json={
            "employee_id": "USER1_ISO",
            "password": "test123"
        })
        token1 = r.json()["access_token"]
        
        r = await client.post("/auth/login", json={
            "employee_id": "USER2_ISO",
            "password": "test123"
        })
        token2 = r.json()["access_token"]
        
        # User1 creates a session
        r = await client.post("/sessions/handout",
                            headers={"authorization": f"Bearer {token1}"},
                            json={"threshold": 0.95, "notes": "User1 session"})
        user1_session_id = r.json()["session_id"]
        
        # User2 should not see User1's session in their list
        r = await client.get("/sessions",
                           headers={"authorization": f"Bearer {token2}"})
        user2_sessions = r.json()
        
        user2_session_ids = [item["id"] for item in user2_sessions["items"]]
        assert user1_session_id not in user2_session_ids

@pytest.mark.asyncio
async def test_data_validation_security():
    """Test that data validation prevents security issues."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register user for authenticated tests
        await client.post("/auth/register", json={
            "employee_id": "DATA_VAL_TEST",
            "password": "test123"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": "DATA_VAL_TEST",
            "password": "test123"
        })
        token = r.json()["access_token"]
        headers = {"authorization": f"Bearer {token}"}
        
        # Test extremely large input values
        r = await client.post("/predict", json={
            "image": "x" * 10000,  # Very large image data
            "threshold": 0.95
        })
        assert r.status_code in [200, 413, 422]  # Should handle gracefully
        
        # Test with null/None values where not expected
        r = await client.post("/sessions/handout",
                            headers=headers,
                            json={
                                "threshold": None,
                                "notes": "test"
                            })
        assert r.status_code == 422  # Should reject null threshold
        
        # Test with negative values where not appropriate
        r = await client.post("/sessions/handout",
                            headers=headers,
                            json={
                                "threshold": -1.0,
                                "notes": "test"
                            })
        assert r.status_code == 422  # Should reject negative threshold

@pytest.mark.asyncio
async def test_error_information_disclosure():
    """Test that error messages don't disclose sensitive information."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test login with non-existent user
        r = await client.post("/auth/login", json={
            "employee_id": "NONEXISTENT_USER_123456",
            "password": "anypassword"
        })
        assert r.status_code == 401
        error_msg = r.json().get("detail", "").lower()
        
        # Should not reveal whether user exists or not
        sensitive_words = ["not found", "does not exist", "user", "employee"]
        assert not any(word in error_msg for word in sensitive_words)
        
        # Test accessing non-existent session
        await client.post("/auth/register", json={
            "employee_id": "ERROR_TEST",
            "password": "test123"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": "ERROR_TEST",
            "password": "test123"
        })
        token = r.json()["access_token"]
        
        fake_session_id = "00000000-0000-0000-0000-000000000000"
        r = await client.get(f"/sessions/{fake_session_id}",
                           headers={"authorization": f"Bearer {token}"})
        assert r.status_code == 404
        
        # Error should be generic
        error_msg = r.json().get("detail", "")
        assert error_msg == "Session not found"  # Generic message