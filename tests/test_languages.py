"""
Automated unit tests for Supported Languages endpoint.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

EXPECTED_LANGUAGES = {
    "kn": "Kannada",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
}


def test_supported_languages_status_and_structure():
    """Verify GET /languages returns 200 OK and list of languages."""
    response = client.get("/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert isinstance(data["languages"], list)
    assert len(data["languages"]) == len(EXPECTED_LANGUAGES)


def test_supported_languages_contain_all_required_languages():
    """Verify all 11 configured Indian regional languages are present."""
    response = client.get("/languages")
    assert response.status_code == 200
    languages = response.json()["languages"]
    returned_codes = {lang["code"]: lang["name"] for lang in languages}

    for code, name in EXPECTED_LANGUAGES.items():
        assert code in returned_codes, f"Language code '{code}' ({name}) missing from response"
        assert returned_codes[code] == name, f"Mismatch in name for code '{code}': expected '{name}', got '{returned_codes[code]}'"
