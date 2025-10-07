import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.app import app

# Test data
ADMIN_EMP = "ADMIN_TEST"
ADMIN_PWD = "admin123"
SIMPLE_EMP = "SIMPLE_TEST"
SIMPLE_PWD = "simple123"

@pytest_asyncio.fixture
async def admin_client():
    """Fixture for authenticated admin client."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register admin user
        await client.post("/auth/register", json={
            "employee_id": ADMIN_EMP, 
            "password": ADMIN_PWD, 
            "role": "admin"
        })
        
        # Login and get token
        r = await client.post("/auth/login", json={
            "employee_id": ADMIN_EMP, 
            "password": ADMIN_PWD
        })
        token = r.json()["access_token"]
        client.headers.update({"authorization": f"Bearer {token}"})
        yield client

@pytest_asyncio.fixture
async def simple_client():
    """Fixture for authenticated simple user client."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register simple user
        await client.post("/auth/register", json={
            "employee_id": SIMPLE_EMP, 
            "password": SIMPLE_PWD, 
            "role": "simple"
        })
        
        # Login and get token
        r = await client.post("/auth/login", json={
            "employee_id": SIMPLE_EMP, 
            "password": SIMPLE_PWD
        })
        token = r.json()["access_token"]
        client.headers.update({"authorization": f"Bearer {token}"})
        yield client

@pytest.mark.asyncio
async def test_create_handout_session(admin_client):
    """Test creating a handout session."""

    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test handout session"
    })
    
    assert r.status_code == 201
    data = r.json()
    assert "session_id" in data
    assert data["status"] == "draft"
    assert data["threshold_used"] == 0.95
    assert "created_at" in data

@pytest.mark.asyncio
async def test_handout_predict_flow(admin_client):
    """Test handout predict flow."""

    # Create session
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    # Test handout predict
    r = await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    
    assert r.status_code == 200
    data = r.json()
    assert "classes_catalog" in data
    assert "detections" in data
    assert "not_found" in data
    assert "summary" in data

@pytest.mark.asyncio
async def test_handout_adjust_flow(admin_client):
    """Test handout adjust flow."""

    # Create session and run predict
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    
    # Test handout adjust with valid 11 annotations
    classes = [
        "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
        "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
        "screwdriver_minus", "oil_can_opener"
    ]
    annotations = [
        {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
        for c in classes
    ]
    
    r = await admin_client.post(f"/sessions/{session_id}/handout/adjust", json={
        "annotations": annotations
    })
    
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["stage"] == "handout"
    assert data["count"] == 11

@pytest.mark.asyncio
async def test_issue_session(admin_client):
    """Test issuing a session."""

    # Create session, predict, and adjust
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    
    classes = [
        "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
        "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
        "screwdriver_minus", "oil_can_opener"
    ]
    annotations = [
        {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
        for c in classes
    ]
    
    await admin_client.post(f"/sessions/{session_id}/handout/adjust", json={
        "annotations": annotations
    })
    
    # Test issue
    r = await admin_client.post(f"/sessions/{session_id}/issue", json={
        "confirm": True
    })
    
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "issued"
    assert "issued_at" in data

@pytest.mark.asyncio
async def test_handover_flow(admin_client):
    """Test complete handover flow."""

    # Create and complete handout phase
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    # Complete handout phase
    await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    
    classes = [
        "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
        "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
        "screwdriver_minus", "oil_can_opener"
    ]
    annotations = [
        {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
        for c in classes
    ]
    
    await admin_client.post(f"/sessions/{session_id}/handout/adjust", json={
        "annotations": annotations
    })
    
    await admin_client.post(f"/sessions/{session_id}/issue", json={"confirm": True})
    
    # Test handover predict
    r = await admin_client.post(f"/sessions/{session_id}/handover/predict", json={
        "image": "base64_handover_image",
        "threshold": 0.95
    })
    
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    
    # Test handover adjust
    r = await admin_client.post(f"/sessions/{session_id}/handover/adjust", json={
        "annotations": annotations
    })
    
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["stage"] == "handover"
    assert data["count"] == 11

@pytest.mark.asyncio
async def test_session_diff(admin_client):
    """Test session diff endpoint."""

    # Create complete session
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    # Complete both phases
    classes = [
        "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
        "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
        "screwdriver_minus", "oil_can_opener"
    ]
    annotations = [
        {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
        for c in classes
    ]
    
    # Handout phase
    await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image", "threshold": 0.95
    })
    await admin_client.post(f"/sessions/{session_id}/handout/adjust", json={
        "annotations": annotations
    })
    await admin_client.post(f"/sessions/{session_id}/issue", json={"confirm": True})
    
    # Handover phase
    await admin_client.post(f"/sessions/{session_id}/handover/predict", json={
        "image": "base64_handover_image", "threshold": 0.95
    })
    await admin_client.post(f"/sessions/{session_id}/handover/adjust", json={
        "annotations": annotations
    })
    
    # Test diff
    r = await admin_client.get(f"/sessions/{session_id}/diff")
    
    assert r.status_code == 200
    data = r.json()
    assert "expected" in data
    assert "handout_final" in data
    assert "handover_final" in data
    assert "missing" in data
    assert "extra" in data

@pytest.mark.asyncio
async def test_finalize_session(admin_client):
    """Test finalizing a session."""

    # Create and complete session
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Test session"
    })
    session_id = r.json()["session_id"]
    
    # Complete full flow
    classes = [
        "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
        "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
        "screwdriver_minus", "oil_can_opener"
    ]
    annotations = [
        {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
        for c in classes
    ]
    
    # Complete handout and handover
    await admin_client.post(f"/sessions/{session_id}/handout/predict", json={
        "image": "base64_test_image", "threshold": 0.95
    })
    await admin_client.post(f"/sessions/{session_id}/handout/adjust", json={
        "annotations": annotations
    })
    await admin_client.post(f"/sessions/{session_id}/issue", json={"confirm": True})
    await admin_client.post(f"/sessions/{session_id}/handover/predict", json={
        "image": "base64_handover_image", "threshold": 0.95
    })
    await admin_client.post(f"/sessions/{session_id}/handover/adjust", json={
        "annotations": annotations
    })
    
    # Test finalize
    r = await admin_client.post(f"/sessions/{session_id}/finalize", json={
        "confirm": True
    })
    
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "returned"
    assert "returned_at" in data

@pytest.mark.asyncio
async def test_list_sessions(admin_client, simple_client):
    """Test listing sessions with role-based access."""

    # Admin creates a session
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Admin session"
    })
    admin_session_id = r.json()["session_id"]
    
    # Simple user creates a session
    r = await simple_client.post("/sessions/handout", json={
        "threshold": 0.90,
        "notes": "Simple user session"
    })
    simple_session_id = r.json()["session_id"]
    
    # Admin should see all sessions
    r = await admin_client.get("/sessions?limit=10")
    assert r.status_code == 200
    admin_data = r.json()
    
    # Simple user should see only their own sessions
    r = await simple_client.get("/sessions?limit=10")
    assert r.status_code == 200
    simple_data = r.json()
    
    # Admin sees more sessions than simple user
    assert admin_data["total"] >= simple_data["total"]
    
    # Simple user should only see their own employee_id
    simple_employee_ids = {item["employee_id"] for item in simple_data["items"]}
    assert simple_employee_ids == {SIMPLE_EMP} or len(simple_employee_ids) == 0

@pytest.mark.asyncio
async def test_get_session_details(admin_client, simple_client):
    """Test getting session details with role-based access."""

    # Simple user creates a session
    r = await simple_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Simple user session"
    })
    simple_session_id = r.json()["session_id"]
    
    # Simple user can access their own session
    r = await simple_client.get(f"/sessions/{simple_session_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["employee_id"] == SIMPLE_EMP
    
    # Admin can access any session
    r = await admin_client.get(f"/sessions/{simple_session_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["employee_id"] == SIMPLE_EMP  # Shows actual owner, not current user

@pytest.mark.asyncio
async def test_session_access_denied(admin_client, simple_client):
    """Test that simple users cannot access other users' sessions for operations."""

    # Admin creates a session
    r = await admin_client.post("/sessions/handout", json={
        "threshold": 0.95,
        "notes": "Admin session"
    })
    admin_session_id = r.json()["session_id"]
    
    # Simple user should not be able to access admin's session for operations
    r = await simple_client.post(f"/sessions/{admin_session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    assert r.status_code == 404  # Session not found for simple user
    
    # Simple user should not be able to get details of admin's session
    r = await simple_client.get(f"/sessions/{admin_session_id}")
    assert r.status_code == 404  # Session not found for simple user

@pytest.mark.asyncio
async def test_invalid_session_operations(admin_client):
    """Test invalid session operations."""

    # Try to operate on non-existent session
    fake_session_id = "00000000-0000-0000-0000-000000000000"
    
    r = await admin_client.post(f"/sessions/{fake_session_id}/handout/predict", json={
        "image": "base64_test_image",
        "threshold": 0.95
    })
    assert r.status_code == 404
    
    r = await admin_client.get(f"/sessions/{fake_session_id}")
    assert r.status_code == 404