import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app

@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete workflow from registration to session completion."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Step 1: Register user
        employee_id = "WORKFLOW_TEST"
        password = "test123"
        
        r = await client.post("/auth/register", json={
            "employee_id": employee_id,
            "password": password,
            "role": "admin"
        })
        assert r.status_code in (201, 409)
        
        # Step 2: Login
        r = await client.post("/auth/login", json={
            "employee_id": employee_id,
            "password": password
        })
        assert r.status_code == 200
        token = r.json()["access_token"]
        headers = {"authorization": f"Bearer {token}"}
        
        # Step 3: Create handout session
        r = await client.post("/sessions/handout", 
                            headers=headers,
                            json={
                                "threshold": 0.95,
                                "notes": "Complete workflow test"
                            })
        assert r.status_code == 201
        session_id = r.json()["session_id"]
        
        # Step 4: Run handout prediction
        r = await client.post(f"/sessions/{session_id}/handout/predict",
                            headers=headers,
                            json={
                                "image": "base64_workflow_test",
                                "threshold": 0.95
                            })
        assert r.status_code == 200
        predict_data = r.json()
        assert "detections" in predict_data
        
        # Step 5: Adjust handout annotations
        classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
            "screwdriver_minus", "oil_can_opener"
        ]
        annotations = [
            {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
            for c in classes
        ]
        
        r = await client.post(f"/sessions/{session_id}/handout/adjust",
                            headers=headers,
                            json={"annotations": annotations})
        assert r.status_code == 200
        assert r.json()["ok"] is True
        
        # Step 6: Issue session
        r = await client.post(f"/sessions/{session_id}/issue",
                            headers=headers,
                            json={"confirm": True})
        assert r.status_code == 200
        assert r.json()["status"] == "issued"
        
        # Step 7: Run handover prediction
        r = await client.post(f"/sessions/{session_id}/handover/predict",
                            headers=headers,
                            json={
                                "image": "base64_handover_test",
                                "threshold": 0.95
                            })
        assert r.status_code == 200
        
        # Step 8: Adjust handover annotations
        r = await client.post(f"/sessions/{session_id}/handover/adjust",
                            headers=headers,
                            json={"annotations": annotations})
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["stage"] == "handover"
        
        # Step 9: Check diff
        r = await client.get(f"/sessions/{session_id}/diff", headers=headers)
        assert r.status_code == 200
        diff_data = r.json()
        assert "handout_final" in diff_data
        assert "handover_final" in diff_data
        
        # Step 10: Finalize session
        r = await client.post(f"/sessions/{session_id}/finalize",
                            headers=headers,
                            json={"confirm": True})
        assert r.status_code == 200
        assert r.json()["status"] == "returned"
        
        # Step 11: Verify session appears in list
        r = await client.get("/sessions", headers=headers)
        assert r.status_code == 200
        sessions_data = r.json()
        session_ids = [item["id"] for item in sessions_data["items"]]
        assert session_id in session_ids
        
        # Step 12: Get detailed session info
        r = await client.get(f"/sessions/{session_id}", headers=headers)
        assert r.status_code == 200
        session_data = r.json()
        assert session_data["id"] == session_id
        assert session_data["status"] == "returned"
        assert session_data["employee_id"] == employee_id
        assert "handout" in session_data
        assert "handover" in session_data

@pytest.mark.asyncio
async def test_multi_user_workflow():
    """Test workflow with multiple users and role-based access."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Create admin user
        admin_emp = "ADMIN_MULTI"
        admin_pwd = "admin123"
        
        await client.post("/auth/register", json={
            "employee_id": admin_emp,
            "password": admin_pwd,
            "role": "admin"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": admin_emp,
            "password": admin_pwd
        })
        admin_token = r.json()["access_token"]
        admin_headers = {"authorization": f"Bearer {admin_token}"}
        
        # Create simple user
        simple_emp = "SIMPLE_MULTI"
        simple_pwd = "simple123"
        
        await client.post("/auth/register", json={
            "employee_id": simple_emp,
            "password": simple_pwd,
            "role": "simple"
        })
        
        r = await client.post("/auth/login", json={
            "employee_id": simple_emp,
            "password": simple_pwd
        })
        simple_token = r.json()["access_token"]
        simple_headers = {"authorization": f"Bearer {simple_token}"}
        
        # Admin creates a session
        r = await client.post("/sessions/handout",
                            headers=admin_headers,
                            json={"threshold": 0.95, "notes": "Admin session"})
        admin_session_id = r.json()["session_id"]
        
        # Simple user creates a session
        r = await client.post("/sessions/handout",
                            headers=simple_headers,
                            json={"threshold": 0.90, "notes": "Simple session"})
        simple_session_id = r.json()["session_id"]
        
        # Admin can see all sessions
        r = await client.get("/sessions", headers=admin_headers)
        admin_sessions = r.json()
        admin_session_ids = [item["id"] for item in admin_sessions["items"]]
        
        # Simple user can only see their own sessions
        r = await client.get("/sessions", headers=simple_headers)
        simple_sessions = r.json()
        simple_session_ids = [item["id"] for item in simple_sessions["items"]]
        
        # Verify access control
        assert admin_session_id in admin_session_ids
        assert simple_session_id in admin_session_ids  # Admin sees all
        
        # Simple user should only see their own session
        simple_employee_ids = {item["employee_id"] for item in simple_sessions["items"]}
        assert simple_employee_ids == {simple_emp} or len(simple_employee_ids) == 0
        
        # Simple user cannot access admin's session
        r = await client.get(f"/sessions/{admin_session_id}", headers=simple_headers)
        assert r.status_code == 404
        
        # Admin can access simple user's session
        r = await client.get(f"/sessions/{simple_session_id}", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["employee_id"] == simple_emp

@pytest.mark.asyncio
async def test_error_recovery_workflow():
    """Test workflow with error conditions and recovery."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register and login
        emp_id = "ERROR_RECOVERY"
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
        
        # Create session
        r = await client.post("/sessions/handout",
                            headers=headers,
                            json={"threshold": 0.95, "notes": "Error test"})
        session_id = r.json()["session_id"]
        
        # Try to adjust before predict (should work but no prediction data)
        classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
            "screwdriver_minus", "oil_can_opener"
        ]
        annotations = [
            {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
            for c in classes
        ]
        
        r = await client.post(f"/sessions/{session_id}/handout/adjust",
                            headers=headers,
                            json={"annotations": annotations})
        assert r.status_code == 200  # Should work even without predict
        
        # Try to issue
        r = await client.post(f"/sessions/{session_id}/issue",
                            headers=headers,
                            json={"confirm": True})
        assert r.status_code == 200
        
        # Try invalid operations on issued session
        r = await client.post(f"/sessions/{session_id}/handout/predict",
                            headers=headers,
                            json={"image": "test", "threshold": 0.95})
        # Should handle gracefully (either 400 or 200 depending on implementation)
        assert r.status_code in [200, 400, 409]

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent operations on different sessions."""

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # Register user
        emp_id = "CONCURRENT_TEST"
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
        
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            r = await client.post("/sessions/handout",
                                headers=headers,
                                json={
                                    "threshold": 0.95,
                                    "notes": f"Concurrent session {i}"
                                })
            session_ids.append(r.json()["session_id"])
        
        # Perform operations on all sessions concurrently
        import asyncio
        
        async def process_session(session_id):
            # Run prediction
            await client.post(f"/sessions/{session_id}/handout/predict",
                            headers=headers,
                            json={"image": f"test_{session_id}", "threshold": 0.95})
            
            # Adjust annotations
            classes = [
                "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
                "nippers", "brace", "lock_pliers", "pliers", "shernitsa", 
                "screwdriver_minus", "oil_can_opener"
            ]
            annotations = [
                {"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} 
                for c in classes
            ]
            
            await client.post(f"/sessions/{session_id}/handout/adjust",
                            headers=headers,
                            json={"annotations": annotations})
            
            return session_id
        
        # Run all sessions concurrently
        results = await asyncio.gather(*[process_session(sid) for sid in session_ids])
        
        # Verify all sessions were processed
        assert len(results) == 3
        assert set(results) == set(session_ids)
        
        # Verify all sessions exist in the list
        r = await client.get("/sessions", headers=headers)
        listed_session_ids = [item["id"] for item in r.json()["items"]]
        
        for session_id in session_ids:
            assert session_id in listed_session_ids