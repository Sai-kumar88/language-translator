"""
Automated unit and integration tests for POST /translate endpoint.

Uses mock translation providers to verify behavior deterministically without
consuming external service quotas or requiring internet access.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.translation_service import (
    BaseTranslationProvider,
    ProviderRateLimitException,
    ProviderTimeoutException,
    ProviderUnavailableException,
    TranslationService,
    get_translation_service,
)
from app.core.config import Settings


class MockSuccessProvider(BaseTranslationProvider):
    """Mock provider returning simulated translations for Indian languages."""

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        mock_dictionary = {
            "kn": "ನಮ್ಮ ಶಾಲೆಗೆ ಸುಸ್ವಾಗತ",
            "hi": "हमारे विद्यालय में आपका स्वागत है",
            "ta": "எங்கள் பள்ளிக்கு வரவேற்கிறோம்",
            "te": "మా పాఠశాలకు స్వాగతం",
            "ml": "ഞങ്ങളുടെ സ്കൂളിലേക്ക് സ്വാഗതം",
            "mr": "आमच्या शाळेत आपले स्वागत आहे",
            "bn": "আমাদের বিদ্যালয়ে স্বাগতম",
            "gu": "અમારી શાળામાં આપનું સ્વાગત છે",
            "pa": "ਸਾਡੇ ਸਕੂਲ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ",
            "or": "ଆମ ବିଦ୍ୟାଳୟକୁ ସ୍ୱାଗତ",
            "ur": "ہمارے اسکول میں خوش آمدید",
        }
        return mock_dictionary.get(target_lang, f"[{target_lang}] {text}")


class MockFailingProvider(BaseTranslationProvider):
    """Mock provider simulating an upstream service failure."""

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        raise ProviderUnavailableException("Upstream translation service connection failed.")


class MockRateLimitedProvider(BaseTranslationProvider):
    """Mock provider simulating upstream HTTP 429 rate limit."""

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        raise ProviderRateLimitException("Upstream translation service rate limit exceeded (429 Too Many Requests).")


class MockTimeoutProvider(BaseTranslationProvider):
    """Mock provider simulating network or processing timeout."""

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        raise ProviderTimeoutException("Upstream translation provider timed out.")


@pytest.fixture
def client_with_mock_provider():
    """Fixture providing a TestClient with MockSuccessProvider."""
    service = TranslationService(provider=MockSuccessProvider())
    app.dependency_overrides[get_translation_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_translate_success_kannada(client_with_mock_provider):
    """Verify valid translation to Kannada produces expected response format."""
    payload = {
        "text": "Welcome to our school",
        "source_language": "en",
        "target_language": "kn",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["original_text"] == "Welcome to our school"
    assert data["translated_text"] == "ನಮ್ಮ ಶಾಲೆಗೆ ಸುಸ್ವಾಗತ"
    assert data["source_language"] == "en"
    assert data["target_language"] == "kn"
    assert data["status"] == "success"


def test_translate_success_all_supported_languages(client_with_mock_provider):
    """Verify translation works for all 11 supported target regional languages."""
    languages = ["kn", "hi", "ta", "te", "ml", "mr", "bn", "gu", "pa", "or", "ur"]
    for lang in languages:
        payload = {
            "text": "Welcome to our school",
            "source_language": "en",
            "target_language": lang,
        }
        response = client_with_mock_provider.post("/translate", json=payload)
        assert response.status_code == 200, f"Failed for language: {lang}"
        data = response.json()
        assert data["target_language"] == lang
        assert data["status"] == "success"
        assert len(data["translated_text"]) > 0


def test_translate_rejects_empty_text(client_with_mock_provider):
    """Verify empty text string is rejected with HTTP 400."""
    payload = {
        "text": "",
        "source_language": "en",
        "target_language": "kn",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()


def test_translate_rejects_whitespace_text(client_with_mock_provider):
    """Verify whitespace-only string is rejected with HTTP 400."""
    payload = {
        "text": "     \n\t   ",
        "source_language": "en",
        "target_language": "kn",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "whitespace" in data["detail"].lower() or "empty" in data["detail"].lower()


def test_translate_rejects_unsupported_target_language(client_with_mock_provider):
    """Verify unsupported target language (e.g., 'fr') is rejected with HTTP 400."""
    payload = {
        "text": "Welcome to our school",
        "source_language": "en",
        "target_language": "fr",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "unsupported target language" in data["detail"].lower()


def test_translate_rejects_unsupported_source_language(client_with_mock_provider):
    """Verify unsupported source language (e.g., 'de') is rejected with HTTP 400."""
    payload = {
        "text": "Willkommen in unserer Schule",
        "source_language": "de",
        "target_language": "kn",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "unsupported source language" in data["detail"].lower()


def test_translate_rejects_excessively_long_text():
    """Verify text exceeding maximum limit is rejected with HTTP 400."""
    custom_settings = Settings(MAX_TEXT_LENGTH=50)
    service = TranslationService(provider=MockSuccessProvider(), settings=custom_settings)
    app.dependency_overrides[get_translation_service] = lambda: service

    with TestClient(app) as client:
        payload = {
            "text": "A" * 51,
            "source_language": "en",
            "target_language": "kn",
        }
        response = client.post("/translate", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "exceeds maximum allowed limit" in data["detail"]

    app.dependency_overrides.clear()


def test_translate_handles_provider_failure():
    """Verify upstream provider failure returns HTTP 502 and does NOT return fake translation."""
    service = TranslationService(provider=MockFailingProvider())
    app.dependency_overrides[get_translation_service] = lambda: service

    with TestClient(app) as client:
        payload = {
            "text": "Welcome to our school",
            "source_language": "en",
            "target_language": "kn",
        }
        response = client.post("/translate", json=payload)
        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert "translated_text" not in data  # Never produce fake translation
        assert "unavailable" in data["detail"].lower() or "failed" in data["detail"].lower()

    app.dependency_overrides.clear()


def test_translate_handles_provider_rate_limit():
    """Verify upstream 429 rate limit returns HTTP 503 and does NOT return fake translation."""
    service = TranslationService(provider=MockRateLimitedProvider())
    app.dependency_overrides[get_translation_service] = lambda: service

    with TestClient(app) as client:
        payload = {
            "text": "Welcome to our school",
            "source_language": "en",
            "target_language": "kn",
        }
        response = client.post("/translate", json=payload)
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "translated_text" not in data
        assert "rate limit" in data["detail"].lower()

    app.dependency_overrides.clear()


def test_translate_handles_provider_timeout():
    """Verify upstream provider timeout returns HTTP 504 and does NOT return fake translation."""
    service = TranslationService(provider=MockTimeoutProvider())
    app.dependency_overrides[get_translation_service] = lambda: service

    with TestClient(app) as client:
        payload = {
            "text": "Welcome to our school",
            "source_language": "en",
            "target_language": "kn",
        }
        response = client.post("/translate", json=payload)
        assert response.status_code == 504
        data = response.json()
        assert "detail" in data
        assert "translated_text" not in data
        assert "timed out" in data["detail"].lower()

    app.dependency_overrides.clear()


def test_translate_multiline_raw_text(client_with_mock_provider):
    """Verify that multi-line text with raw unescaped newlines is parsed successfully."""
    multiline_raw = (
        '{\n'
        '  "text": "First paragraph.\\nSecond paragraph with multiple lines.\\nThird line.",\n'
        '  "source_language": "en",\n'
        '  "target_language": "kn"\n'
        '}'
    ).encode("utf-8")
    response = client_with_mock_provider.post(
        "/translate",
        content=multiline_raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "First paragraph" in data["original_text"]


def test_translate_large_chunked_text(client_with_mock_provider):
    """Verify that very large text (over 40,000 characters) is split into chunks and translated successfully."""
    # Create ~44,000 characters of text
    large_text = ("Welcome to our school. We provide quality education. " * 30 + "\n\n") * 15
    payload = {
        "text": large_text,
        "source_language": "en",
        "target_language": "kn",
    }
    response = client_with_mock_provider.post("/translate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["translated_text"]) > 0


def test_translate_word_document(client_with_mock_provider):
    """Verify translating an uploaded Word (.docx) document."""
    import io
    import docx

    doc = docx.Document()
    doc.add_heading("Welcome Letter", level=1)
    doc.add_paragraph("Welcome to our school.")
    buf = io.BytesIO()
    doc.save(buf)

    response = client_with_mock_provider.post(
        "/translate/document",
        files={"file": ("test_doc.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"source_language": "en", "target_language": "kn"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_type"] == "docx"
    assert "Welcome" in data["original_text"]


def test_translate_word_document_download(client_with_mock_provider):
    """Verify downloading translated Word (.docx) document."""
    import io
    import docx

    doc = docx.Document()
    doc.add_paragraph("Welcome to our school.")
    buf = io.BytesIO()
    doc.save(buf)

    response = client_with_mock_provider.post(
        "/translate/document/download",
        files={"file": ("school.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"source_language": "en", "target_language": "kn"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "attachment" in response.headers["content-disposition"]


def test_translate_text_file(client_with_mock_provider):
    """Verify translating an uploaded text (.txt) file."""
    txt_content = b"Welcome to our school. We provide quality education."
    response = client_with_mock_provider.post(
        "/translate/document",
        files={"file": ("sample.txt", txt_content, "text/plain")},
        data={"source_language": "en", "target_language": "kn"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_type"] == "txt"
    assert "Welcome" in data["original_text"]


def test_translate_accepts_full_language_names(client_with_mock_provider):
    """Verify translating with full language names like 'Telugu', 'Kannada', 'Hindi', 'English'."""
    full_name_tests = [
        ("Telugu", "te"),
        ("telugu", "te"),
        ("Kannada", "kn"),
        ("kannada", "kn"),
        ("Hindi", "hi"),
        ("Tamil", "ta"),
        ("Malayalam", "ml"),
    ]
    for name_input, expected_code in full_name_tests:
        payload = {
            "text": "Welcome to our school",
            "source_language": "English",
            "target_language": name_input,
        }
        response = client_with_mock_provider.post("/translate", json=payload)
        assert response.status_code == 200, f"Failed for full name: {name_input}"
        data = response.json()
        assert data["target_language"] == expected_code
        assert data["source_language"] == "en"
        assert data["status"] == "success"



