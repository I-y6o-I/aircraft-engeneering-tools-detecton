import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app

EMP = "TEST001"
PWD = "test123"

@pytest.mark.asyncio
async def test_register_login_me():
    """Test basic authentication flow: register, login, and access protected endpoint."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test registration
        r = await client.post("/auth/register", json={"employee_id": EMP, "password": PWD})
        assert r.status_code in (201, 409)  # can be run again
        
        # Test login
        r = await client.post("/auth/login", json={"employee_id": EMP, "password": PWD})
        assert r.status_code == 200
        token = r.json()["access_token"]
        assert token is not None
        assert len(token) > 50  # JWT tokens are typically long
        
        # Test protected endpoint
        r = await client.get("/auth/me", headers={"authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["employee_id"] == EMP
        assert body["role"] in ("simple", "admin")
        assert "id" in body

@pytest.mark.asyncio
async def test_role_assignment():
    """Test that roles are properly assigned during registration."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Test registering as admin
        admin_emp = "ADMIN_TEST_001"
        r = await client.post("/auth/register", json={
            "employee_id": admin_emp, 
            "password": PWD,
            "role": "admin"
        })
        assert r.status_code in (201, 409)
        
        r = await client.post("/auth/login", json={
            "employee_id": admin_emp, 
            "password": PWD
        })
        assert r.status_code == 200
        token = r.json()["access_token"]
        
        r = await client.get("/auth/me", headers={"authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "admin"
        
        # Test registering as simple user
        simple_emp = "SIMPLE_TEST_001"
        r = await client.post("/auth/register", json={
            "employee_id": simple_emp, 
            "password": PWD,
            "role": "simple"
        })
        assert r.status_code in (201, 409)
        
        r = await client.post("/auth/login", json={
            "employee_id": simple_emp, 
            "password": PWD
        })
        assert r.status_code == 200
        token = r.json()["access_token"]
        
        r = await client.get("/auth/me", headers={"authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["role"] == "simple"

@pytest.mark.asyncio
async def test_duplicate_registration():
    """Test that duplicate employee_id registration is handled properly."""
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        emp_id = "DUPLICATE_TEST"
        
        # First registration should succeed
        r = await client.post("/auth/register", json={
            "employee_id": emp_id, 
            "password": PWD
        })
        assert r.status_code == 201
        
        # Second registration with same employee_id should fail
        r = await client.post("/auth/register", json={
            "employee_id": emp_id, 
            "password": "different_password"
        })
        assert r.status_code == 409  # Conflict