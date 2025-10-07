import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app

@pytest.mark.asyncio
async def test_healthz():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_predict_contract():
    """Test predict endpoint contract and response format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        body = {"image": "base64-abc", "threshold": 0.98}
        r = await client.post("/predict", json=body)
        assert r.status_code == 200
        data = r.json()

        # Basic fields
        assert "classes_catalog" in data
        assert isinstance(data["classes_catalog"], list)
        assert len(data["classes_catalog"]) == 11

        assert "detections" in data
        assert isinstance(data["detections"], list)

        assert "not_found" in data
        assert isinstance(data["not_found"], list)

        assert "summary" in data
        assert isinstance(data["summary"], dict)

        # Each detection corresponds to the contract
        for det in data["detections"]:
            assert {"detection_id", "class", "confidence", "is_passed_conf_treshold", "box"} <= det.keys()
            assert isinstance(det["detection_id"], str)
            assert isinstance(det["class"], str)
            assert isinstance(det["confidence"], (int, float))
            assert isinstance(det["is_passed_conf_treshold"], bool)
            assert isinstance(det["box"], list) and len(det["box"]) == 4
            # Coordinates are normalized [0..1]
            assert all(isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in det["box"])

        # Classes of detections must be from the catalog
        det_classes = [d["class"] for d in data["detections"]]
        assert set(det_classes).issubset(set(data["classes_catalog"]))

        # Summary согласован с детектами
        assert data["summary"]["expected_total"] == 11
        assert data["summary"]["found_candidates"] == len(data["detections"])
        assert data["summary"]["not_found_count"] == len(data["not_found"])
        # passed_above_threshold и requires_manual_count — не строго проверяем, только наличие
        assert "passed_above_threshold" in data["summary"]
        assert "requires_manual_count" in data["summary"]

@pytest.mark.asyncio
async def test_predict_adjust_validation_ok():
    """Test predict/adjust endpoint with valid 11 annotations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ровно 11 аннотаций, по одному на класс
        classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", "screwdriver_minus", "oil_can_opener"
        ]
        annotations = [{"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} for c in classes]

        r = await client.post("/predict/adjust", json={"annotations": annotations})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["count"] == 11

@pytest.mark.asyncio
async def test_predict_adjust_validation_fails_on_duplicates():
    """Test predict/adjust endpoint with duplicate classes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Duplicate one class and remove another
        classes = [
            "screwdriver_plus", "wrench_adjustable", "offset_cross", "ring_wrench_3_4",
            "nippers", "brace", "lock_pliers", "pliers", "shernitsa", "screwdriver_minus", "oil_can_opener"
        ]
        classes[1] = classes[0]  # make a duplicate
        annotations = [{"class": c, "box": [0.5, 0.5, 0.2, 0.1], "source": "manual"} for c in classes]

        r = await client.post("/predict/adjust", json={"annotations": annotations})
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is False

        # Текст ошибок может отличаться — ищем ключевые слова
        issues_text = " ".join(body.get("issues", [])).lower()
        assert any(kw in issues_text for kw in ["duplicate", "duplicates", "missing", "exactly once"])