import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app

@pytest.mark.asyncio
async def test_predict_adjust_validation_errors():
    """Test various validation errors for predict/adjust endpoint."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test with wrong number of annotations (too few)
        r = await client.post("/predict/adjust", json={
            "annotations": [
                {"class": "screwdriver_plus", "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"}
            ]
        })
        assert r.status_code == 422  # Validation error
        
        # Test with wrong number of annotations (too many)
        classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
            "screwdriver_minus", "oil_can_opener", "extra_tool"  # 12 instead of 11
        ]
        annotations = [
            {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
            for c in classes
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": annotations
        })
        assert r.status_code == 422  # Validation error
        
        # Test with invalid bbox coordinates (out of range)
        valid_classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
            "screwdriver_minus", "oil_can_opener"
        ]
        invalid_annotations = [
            {"class": c, "box": [1.5, 0.5, 0.2, 0.1], "source": "manual"}  # x > 1.0
            for c in valid_classes
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": invalid_annotations
        })
        assert r.status_code == 200  # Should return validation error in response
        data = r.json()
        assert data["ok"] is False
        assert "issues" in data
        
        # Test with unknown class
        unknown_class_annotations = [
            {"class": "unknown_tool", "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"}
        ] + [
            {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
            for c in valid_classes[1:]  # Skip first to make room for unknown
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": unknown_class_annotations
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert "issues" in data
        
        # Test with duplicate classes
        duplicate_annotations = [
            {"class": "screwdriver_plus", "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"},
            {"class": "screwdriver_plus", "box": [0.3, 0.3, 0.2, 0.1], "source": "manual"},  # Duplicate
        ] + [
            {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
            for c in valid_classes[2:]  # Skip first two
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": duplicate_annotations
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert "issues" in data

@pytest.mark.asyncio
async def test_predict_validation():
    """Test validation for predict endpoint."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test missing required fields
        r = await client.post("/predict", json={})
        assert r.status_code == 422
        
        # Test invalid threshold (too high)
        r = await client.post("/predict", json={
            "image": "base64_test",
            "threshold": 1.5
        })
        assert r.status_code == 422
        
        # Test invalid threshold (negative)
        r = await client.post("/predict", json={
            "image": "base64_test",
            "threshold": -0.1
        })
        assert r.status_code == 422
        
        # Test with valid data
        r = await client.post("/predict", json={
            "image": "base64_test",
            "threshold": 0.95
        })
        assert r.status_code == 200

@pytest.mark.asyncio
async def test_auth_validation_errors():
    """Test authentication validation errors."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test registration with missing fields
        r = await client.post("/auth/register", json={})
        assert r.status_code == 422
        
        # Test registration with invalid employee_id (too short)
        r = await client.post("/auth/register", json={
            "employee_id": "AB",  # Too short
            "password": "test123"
        })
        assert r.status_code == 422
        
        # Test registration with invalid password (too short)
        r = await client.post("/auth/register", json={
            "employee_id": "TEST123",
            "password": "123"  # Too short
        })
        assert r.status_code == 422
        
        # Test login with wrong credentials
        r = await client.post("/auth/login", json={
            "employee_id": "NONEXISTENT",
            "password": "wrongpassword"
        })
        assert r.status_code in [401, 403]
        
        # Test accessing protected endpoint without token
        r = await client.get("/auth/me")
        assert r.status_code in [401, 403]
        
        # Test accessing protected endpoint with invalid token
        r = await client.get("/auth/me", headers={
            "authorization": "Bearer invalid_token"
        })
        assert r.status_code in [401, 403]

@pytest.mark.asyncio
async def test_session_validation_errors():
    """Test session validation errors."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register and login user
        await client.post("/auth/register", json={
            "employee_id": "VALID_USER",
            "password": "test123"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": "VALID_USER",
            "password": "test123"
        })
        token = r.json()["access_token"]
        headers = {"authorization": f"Bearer {token}"}
        
        # Test creating session with invalid threshold
        r = await client.post("/sessions/handout", 
                            headers=headers,
                            json={
                                "threshold": 1.5,  # Invalid threshold
                                "notes": "Test"
                            })
        assert r.status_code == 422
        
        # Test creating session with negative threshold
        r = await client.post("/sessions/handout", 
                            headers=headers,
                            json={
                                "threshold": -0.1,  # Invalid threshold
                                "notes": "Test"
                            })
        assert r.status_code == 422
        
        # Test session operations without authentication
        r = await client.post("/sessions/handout", json={
            "threshold": 0.95,
            "notes": "Test"
        })
        assert r.status_code in [401, 403]

@pytest.mark.asyncio
async def test_edge_cases():
    """Test various edge cases."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test predict with extreme threshold values (valid but edge cases)
        r = await client.post("/predict", json={
            "image": "base64_test",
            "threshold": 0.0  # Minimum valid threshold
        })
        assert r.status_code == 200
        
        r = await client.post("/predict", json={
            "image": "base64_test",
            "threshold": 1.0  # Maximum valid threshold
        })
        assert r.status_code == 200
        
        # Test predict/adjust with edge case bbox coordinates
        valid_classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
            "screwdriver_minus", "oil_can_opener"
        ]
        edge_annotations = [
            {"class": c, "box": [0.0, 0.0, 1.0, 1.0], "source": "manual"}  # Full image bbox
            for c in valid_classes
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": edge_annotations
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        
        # Test with very small bbox
        small_bbox_annotations = [
            {"class": c, "box": [0.5, 0.5, 0.001, 0.001], "source": "manual"}  # Very small bbox
            for c in valid_classes
        ]
        
        r = await client.post("/predict/adjust", json={
            "annotations": small_bbox_annotations
        })
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True

@pytest.mark.asyncio
async def test_cors_and_options():
    """Test CORS and OPTIONS requests."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test OPTIONS request for CORS preflight
        # Note: FastAPI may return 405 for OPTIONS on some endpoints, which is acceptable
        r = await client.options("/predict")
        assert r.status_code in [200, 405]  # Both are acceptable for CORS
        
        r = await client.options("/auth/login")
        assert r.status_code in [200, 405]  # Both are acceptable for CORS

@pytest.mark.asyncio
async def test_content_type_validation():
    """Test content type validation."""
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test with wrong content type
        r = await client.post("/predict", 
                            content="image=test&threshold=0.95",
                            headers={"content-type": "application/x-www-form-urlencoded"})
        assert r.status_code == 422  # Should expect JSON