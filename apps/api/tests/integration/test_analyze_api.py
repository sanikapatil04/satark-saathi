from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db


async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    yield mock_session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_analyze_valid_message():
    payload = {
        "text": "Your bank KYC has expired. Your account will be blocked within 24 hours. Click this link immediately to update your account."
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "RED"
    assert data["risk_score"] >= 60
    assert data["category"] == "BANK_KYC"
    assert isinstance(data["red_flags"], list)
    assert len(data["red_flags"]) > 0
    assert "reason" in data
    assert "recommended_action" in data


def test_analyze_empty_message():
    payload = {"text": ""}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_whitespace_message():
    payload = {"text": "    \n\t  "}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_malformed_request():
    payload = {"invalid_field": "some text"}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_oversized_message():
    payload = {"text": "A" * 5001}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_internal_error_handling():
    payload = {"text": "Valid message text for analysis."}
    with patch(
        "app.api.v1.endpoints.analyze.AnalyzerService.analyze_text",
        side_effect=Exception("Database connection failed or raw SQL crash"),
    ):
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Database connection failed" not in data["detail"]
        assert "internal error" in data["detail"].lower()
