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


def test_ui_endpoint_returns_html():
    """Verify GET /ui serves static HTML frontend."""
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Language Translator" in response.text
    assert "VAPS Technosoft" in response.text


def test_static_assets_served():
    """Verify static HTML, CSS, and JS files directly under /static are accessible."""
    html_res = client.get("/static/index.html")
    assert html_res.status_code == 200
    assert "Language Translator" in html_res.text

    css_res = client.get("/static/style.css")
    assert css_res.status_code == 200
    assert "VAPS Technosoft" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "VAPS Technosoft" in js_res.text
