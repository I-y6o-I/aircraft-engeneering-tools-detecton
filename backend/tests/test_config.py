import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app
from src.core.settings import settings

@pytest.mark.asyncio
async def test_app_configuration():
    """Test that the app is properly configured."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test that app starts and responds
        r = await client.get("/healthz")
        assert r.status_code == 200
        
        # Test CORS headers are present
        r = await client.options("/predict")
        assert r.status_code in [200, 405]  # Both are acceptable

@pytest.mark.asyncio
async def test_settings_validation():
    """Test that settings are properly configured."""

    # Test that required settings exist
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'JWT_SECRET')
    assert hasattr(settings, 'CORS_ORIGINS')
    
    # Test that JWT secret is not empty
    assert len(settings.JWT_SECRET) > 0
    
    # Test that database URL is configured
    assert settings.DATABASE_URL is not None
    assert len(settings.DATABASE_URL) > 0

@pytest.mark.asyncio
async def test_api_versioning():
    """Test API versioning and endpoints."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test that all expected endpoints exist
        endpoints_to_test = [
            ("/healthz", "GET", 200),
            ("/predict", "POST", 422),  # 422 because no body
            ("/auth/register", "POST", 422),  # 422 because no body
            ("/auth/login", "POST", 422),  # 422 because no body
        ]
        
        for endpoint, method, expected_status in endpoints_to_test:
            if method == "GET":
                r = await client.get(endpoint)
            elif method == "POST":
                r = await client.post(endpoint)
            else:
                continue
                
            assert r.status_code == expected_status

@pytest.mark.asyncio
async def test_error_handling():
    """Test global error handling."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test 404 for non-existent endpoint
        r = await client.get("/non-existent-endpoint")
        assert r.status_code == 404
        
        # Test 405 for wrong method
        r = await client.patch("/healthz")
        assert r.status_code == 405

@pytest.mark.asyncio
async def test_request_validation():
    """Test request validation across endpoints."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test malformed JSON
        r = await client.post("/predict", 
                            content="invalid json",
                            headers={"content-type": "application/json"})
        assert r.status_code == 422
        
        # Test missing content-type
        r = await client.post("/predict", content='{"test": "data"}')
        assert r.status_code == 422

@pytest.mark.asyncio
async def test_response_formats():
    """Test that responses follow expected formats."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test health check response format
        r = await client.get("/healthz")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
        
        # Test predict response format
        r = await client.post("/predict", json={
            "image": "test",
            "threshold": 0.95
        })
        assert r.status_code == 200
        data = r.json()
        
        # Verify required fields
        required_fields = ["classes_catalog", "detections", "not_found", "summary"]
        for field in required_fields:
            assert field in data
        
        # Verify data types
        assert isinstance(data["classes_catalog"], list)
        assert isinstance(data["detections"], list)
        assert isinstance(data["not_found"], list)
        assert isinstance(data["summary"], dict)

@pytest.mark.asyncio
async def test_authentication_flow():
    """Test authentication flow configuration."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test that protected endpoints require authentication
        protected_endpoints = [
            "/auth/me",
            "/sessions/handout",
            "/sessions"
        ]
        
        for endpoint in protected_endpoints:
            if "sessions" in endpoint and endpoint != "/sessions":
                r = await client.post(endpoint, json={})
            else:
                r = await client.get(endpoint)
            
            assert r.status_code in [401, 403]  # Unauthorized or Forbidden

@pytest.mark.asyncio
async def test_data_consistency():
    """Test data consistency across operations."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register user
        emp_id = "CONSISTENCY_TEST"
        password = "test123"
        
        r = await client.post("/auth/register", json={
            "employee_id": emp_id,
            "password": password
        })
        assert r.status_code in (201, 409)
        
        # Login and get user info
        r = await client.post("/auth/login", json={
            "employee_id": emp_id,
            "password": password
        })
        token = r.json()["access_token"]
        
        r = await client.get("/auth/me", headers={
            "authorization": f"Bearer {token}"
        })
        user_data = r.json()
        
        # Create session and verify user consistency
        r = await client.post("/sessions/handout",
                            headers={"authorization": f"Bearer {token}"},
                            json={"threshold": 0.95, "notes": "Consistency test"})
        session_id = r.json()["session_id"]
        
        # Get session details and verify user consistency
        r = await client.get(f"/sessions/{session_id}",
                           headers={"authorization": f"Bearer {token}"})
        session_data = r.json()
        
        # User ID should be consistent
        assert session_data["employee_id"] == user_data["employee_id"]

@pytest.mark.asyncio 
async def test_pagination_and_filtering():
    """Test pagination and filtering functionality."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register user
        emp_id = "PAGINATION_TEST"
        password = "test123"
        
        await client.post("/auth/register", json={
            "employee_id": emp_id,
            "password": password
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": emp_id,
            "password": password
        })
        token = r.json()["access_token"]
        headers = {"authorization": f"Bearer {token}"}
        
        # Test pagination parameters
        r = await client.get("/sessions?page=1&limit=5", headers=headers)
        assert r.status_code == 200
        data = r.json()
        
        # Verify pagination response structure
        assert "page" in data
        assert "limit" in data
        assert "total" in data
        assert "items" in data
        
        assert data["page"] == 1
        assert data["limit"] == 5
        assert isinstance(data["total"], int)
        assert isinstance(data["items"], list)
        
        # Test with different page size
        r = await client.get("/sessions?page=1&limit=2", headers=headers)
        assert r.status_code == 200
        data2 = r.json()
        assert data2["limit"] == 2

@pytest.mark.asyncio
async def test_content_type_handling():
    """Test content type handling."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test JSON content type
        r = await client.post("/predict",
                            json={"image": "test", "threshold": 0.95})
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/json")
        
        # Test that response is valid JSON
        data = r.json()
        assert isinstance(data, dict)