"""
Automated unit tests for Health Check endpoint.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_success():
    """Verify GET /health returns 200 OK and expected JSON payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Language Translator API"


def test_root_endpoint_success():
    """Verify GET / returns 200 OK and index discovery links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "documentation" in data
    assert "endpoints" in data
