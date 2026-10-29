# English-to-Indian Regional Language Translator REST API

A professional, modular, and scalable Language Translator REST API built with **Python 3.12** and **FastAPI** for **VAPS Technosoft**.

The service provides real-time translation of English text into **11 Indian regional languages** with an extensible architecture designed to add additional languages or swap translation providers seamlessly.

---

## Table of Contents
- [1. Supported Languages](#1-supported-languages)
- [2. Project Architecture & Directory Structure](#2-project-architecture--directory-structure)
- [3. Technology Stack](#3-technology-stack)
- [4. Environment Setup & Installation](#4-environment-setup--installation)
- [5. Running the Application](#5-running-the-application)
- [6. API Endpoints & Usage](#6-api-endpoints--usage)
  - [A. Health Check (`GET /health`)](#a-health-check-get-health)
  - [B. Supported Languages (`GET /languages`)](#b-supported-languages-get-languages)
  - [C. Translate Text (`POST /translate`)](#c-translate-text-post-translate)
- [7. Interactive API Documentation (Swagger & ReDoc)](#7-interactive-api-documentation-swagger--redoc)
- [8. Testing with Postman](#8-testing-with-postman)
- [9. Automated Testing (pytest)](#9-automated-testing-pytest)
- [10. Error Handling & HTTP Status Codes](#10-error-handling--http-status-codes)
- [11. Provider Limitations & Production Guidance](#11-provider-limitations--production-guidance)
- [12. Docker Deployment](#12-docker-deployment)
- [13. Future Authentication Roadmap](#13-future-authentication-roadmap)

---

## 1. Supported Languages

| Language | ISO Code | Language Family | Accepted Inputs |
| :--- | :--- | :--- | :--- |
| **Kannada** | `kn` | Dravidian | `"kn"`, `"kannada"`, `"Kannada"` |
| **Hindi** | `hi` | Indo-Aryan | `"hi"`, `"hindi"`, `"Hindi"` |
| **Tamil** | `ta` | Dravidian | `"ta"`, `"tamil"`, `"Tamil"` |
| **Telugu** | `te` | Dravidian | `"te"`, `"telugu"`, `"Telugu"` |
| **Malayalam** | `ml` | Dravidian | `"ml"`, `"malayalam"`, `"Malayalam"` |
| **Marathi** | `mr` | Indo-Aryan | `"mr"`, `"marathi"`, `"Marathi"` |
| **Bengali** | `bn` | Indo-Aryan | `"bn"`, `"bengali"`, `"Bengali"` |
| **Gujarati** | `gu` | Indo-Aryan | `"gu"`, `"gujarati"`, `"Gujarati"` |
| **Punjabi** | `pa` | Indo-Aryan | `"pa"`, `"punjabi"`, `"Punjabi"` |
| **Odia** | `or` | Indo-Aryan | `"or"`, `"odia"`, `"oriya"` |
| **Urdu** | `ur` | Indo-Aryan | `"ur"`, `"urdu"`, `"Urdu"` |

> **Note:** The API accepts **both language codes** (`"te"`, `"kn"`, etc.) and **full language names** (`"Telugu"`, `"Kannada"`, etc.), case-insensitively. The source language also accepts both `"en"` and `"English"`.

---

## 2. Project Architecture & Directory Structure

The project strictly follows clean architecture principles, cleanly separating routing, business logic, validation schemas, and configuration:

```
language-translator-api/
├── app/
│   ├── __init__.py               # Package marker and version
│   ├── main.py                   # FastAPI app factory, lifespan, CORS & exception handlers
│   ├── api/
│   │   ├── __init__.py           # API package initialization
│   │   └── routes.py             # Route handlers (/health, /languages, /translate)
│   ├── schemas/
│   │   ├── __init__.py           # Schemas package export
│   │   └── translator.py         # Pydantic models with input sanitization & validation
│   ├── services/
│   │   ├── __init__.py           # Services package export
│   │   └── translation_service.py # Provider abstraction, GoogleTrans provider & service layer
│   └── core/
│       ├── __init__.py           # Core package initialization
│       ├── config.py             # Pydantic Settings & environment variable configuration
│       └── logging_config.py     # Safe logging without exposing confidential text payloads
├── tests/
│   ├── __init__.py               # Test suite package
│   ├── test_health.py            # Automated tests for GET /health
│   ├── test_languages.py         # Automated tests for GET /languages
│   └── test_translate.py         # Automated tests for POST /translate (with mocked provider)
├── .env.example                  # Template configuration file
├── .gitignore                    # Git ignore file for Python, caches, and secrets
├── Dockerfile                    # Containerization specification for Python 3.12
├── postman_collection.json       # Postman v2.1 collection for manual and automated API testing
├── pytest.ini                    # Pytest configuration settings
├── requirements.txt              # Pinned, verified dependencies
└── README.md                     # Comprehensive project documentation
```

---

## 3. Technology Stack

- **Language:** Python 3.12 (Verified with 3.12.9 64-bit)
- **Web Framework:** FastAPI (v0.115+)
- **ASGI Server:** Uvicorn (v0.30+ with uvloop/httptools support)
- **Validation & Serialization:** Pydantic v2 & Pydantic-Settings
- **Translation Engine:** `googletrans==4.0.2` (Verified and isolated behind `BaseTranslationProvider`)
- **HTTP Client:** HTTPX (async client with HTTP/2 support)
- **Automated Testing:** Pytest (v8+) & Pytest-Asyncio with FastAPI `TestClient`
- **Environment Management:** python-dotenv

---

## 4. Environment Setup & Installation

### Step 1: Clone or Navigate to the Project Directory
```bash
cd "c:\Users\lokesh\Language - Tranalator"
```

### Step 2: Create a Python 3.12 Virtual Environment
On Windows (PowerShell / Command Prompt):
```powershell
py -3.12 -m venv venv
.\venv\Scripts\activate
```
On macOS / Linux:
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```powershell
Copy-Item .env.example .env
```
Default configuration values:
```env
APP_NAME="Language Translator API"
APP_ENV=development
APP_DEBUG=false
APP_HOST=127.0.0.1
APP_PORT=8000
API_PREFIX=
CORS_ORIGINS=["*"]

MAX_TEXT_LENGTH=5000
DEFAULT_SOURCE_LANGUAGE=en
TRANSLATION_TIMEOUT_SECONDS=10.0

TRANSLATION_PROVIDER=googletrans
GOOGLETRANS_SERVICE_URLS=["translate.google.com","translate.googleapis.com"]
```

---

## 5. Running the Application

Start the development server with live reload:
```bash
python -m uvicorn app.main:app --reload
```
Alternatively:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Server endpoints will be accessible at:
- **Base URL:** `http://127.0.0.1:8000`
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Supported Languages:** [http://127.0.0.1:8000/languages](http://127.0.0.1:8000/languages)

---

## 6. API Endpoints & Usage

### A. Health Check (`GET /health`)
Verifies that the API service is operational.

**Request:**
```http
GET /health HTTP/1.1
Host: 127.0.0.1:8000
```
**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "Language Translator API"
}
```

---

### B. Supported Languages (`GET /languages`)
Lists all supported regional Indian languages and their codes.

**Request:**
```http
GET /languages HTTP/1.1
Host: 127.0.0.1:8000
```
**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/languages"
```
**Response (200 OK):**
```json
{
  "languages": [
    {"code": "kn", "name": "Kannada"},
    {"code": "hi", "name": "Hindi"},
    {"code": "ta", "name": "Tamil"},
    {"code": "te", "name": "Telugu"},
    {"code": "ml", "name": "Malayalam"},
    {"code": "mr", "name": "Marathi"},
    {"code": "bn", "name": "Bengali"},
    {"code": "gu", "name": "Gujarati"},
    {"code": "pa", "name": "Punjabi"},
    {"code": "or", "name": "Odia"},
    {"code": "ur", "name": "Urdu"}
  ]
}
```

---

### C. Translate Text (`POST /translate`)
Translates English text into one of the supported Indian regional languages.

**Request:**
```http
POST /translate HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "text": "Welcome to our school",
  "source_language": "en",
  "target_language": "kn"
}
```

**cURL Example (Kannada):**
```bash
curl -X POST "http://127.0.0.1:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to our school",
    "source_language": "en",
    "target_language": "kn"
  }'
```

**cURL Example (Hindi):**
```bash
curl -X POST "http://127.0.0.1:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to our school",
    "source_language": "en",
    "target_language": "hi"
  }'
```

**Successful Response (200 OK):**
```json
{
  "original_text": "Welcome to our school",
  "translated_text": "ನಮ್ಮ ಶಾಲೆಗೆ ಸುಸ್ವಾಗತ",
  "source_language": "en",
  "target_language": "kn",
  "status": "success"
}
```

---

### D. Translate Document (`POST /translate/document`)
Upload a Word document (`.docx`), PDF (`.pdf`), or Text file (`.txt`) to translate its entire contents into an Indian regional language. Large documents are automatically chunked into manageable batches.

**Request:**
`POST /translate/document` (`multipart/form-data`)

**Form Parameters:**
- `file`: The `.docx`, `.pdf`, or `.txt` file to translate
- `source_language`: Source language code (e.g. `en`)
- `target_language`: Target regional language code (e.g. `kn`, `hi`, `ta`)

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/translate/document" \
  -F "file=@sample_school_letter.docx" \
  -F "source_language=en" \
  -F "target_language=kn"
```

**Response (200 OK):**
```json
{
  "filename": "sample_school_letter.docx",
  "file_type": "docx",
  "original_characters": 39811,
  "original_text": "Welcome to our school...",
  "translated_text": "ನಮ್ಮ ಶಾಲೆಗೆ ಸುಸ್ವಾಗತ...",
  "source_language": "en",
  "target_language": "kn",
  "status": "success"
}
```

---

### E. Translate & Download Word Document (`POST /translate/document/download`)
Upload a Word document (`.docx`), PDF (`.pdf`), or Text file (`.txt`) and download the translated output directly as a Microsoft Word (`.docx`) file.

**Request:**
`POST /translate/document/download` (`multipart/form-data`)

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/translate/document/download" \
  -F "file=@report.docx" \
  -F "source_language=en" \
  -F "target_language=hi" \
  --output translated_report.docx
```

---

## 7. Interactive API Documentation (Swagger & ReDoc)

Once running, interactive documentation is available automatically:
- **Swagger Interactive Testing:** Navigate to `http://127.0.0.1:8000/docs`. You can execute requests directly in the browser and inspect headers, request schemas, and response formats.
- **ReDoc Technical Reference:** Navigate to `http://127.0.0.1:8000/redoc`.

---

## 8. Testing with Postman

A ready-to-import Postman Collection is provided in the repository: `postman_collection.json`.

### How to Import:
1. Open Postman.
2. Click **Import** (top left).
3. Select or drag-and-drop `postman_collection.json`.
4. The collection **"Language Translator API - VAPS Technosoft"** will appear in your workspace.
5. Set the collection variable `baseUrl` to `http://127.0.0.1:8000` (set by default).

### Included Requests in the Collection:
1. `Health Check` (`GET {{baseUrl}}/health`)
2. `Get Supported Languages` (`GET {{baseUrl}}/languages`)
3. `Translate - English to Kannada` (`POST {{baseUrl}}/translate`)
4. `Translate - English to Hindi` (`POST {{baseUrl}}/translate`)
5. `Translate - English to Tamil` (`POST {{baseUrl}}/translate`)
6. `Translate - English to Telugu` (`POST {{baseUrl}}/translate`)
7. `Translate - Error - Empty Text (400)` (Validation error test)
8. `Translate - Error - Unsupported Language (400)` (Validation error test)

---

## 9. Automated Testing (pytest)

The project includes an automated test suite with mocked translation providers to ensure deterministic test execution without depending on external network access or consuming quotas.

### Run All Tests:
```bash
pytest -v
```

### Run Tests with Short Output:
```bash
pytest
```

### Covered Test Cases:
1. `test_health.py::test_health_check_success`: Verifies HTTP 200 and expected payload structure.
2. `test_languages.py::test_supported_languages_status_and_structure`: Verifies list schema and count.
3. `test_languages.py::test_supported_languages_contain_all_required_languages`: Verifies all 11 Indian regional languages (`kn`, `hi`, `ta`, `te`, `ml`, `mr`, `bn`, `gu`, `pa`, `or`, `ur`).
4. `test_translate.py::test_translate_success_kannada`: Verifies Kannada translation response format.
5. `test_translate.py::test_translate_success_all_supported_languages`: Verifies translation across all 11 regional languages.
6. `test_translate.py::test_translate_rejects_empty_text`: Confirms empty strings return HTTP 400.
7. `test_translate.py::test_translate_rejects_whitespace_text`: Confirms whitespace-only strings return HTTP 400.
8. `test_translate.py::test_translate_rejects_unsupported_target_language`: Confirms non-supported target codes return HTTP 400.
9. `test_translate.py::test_translate_rejects_unsupported_source_language`: Confirms non-supported source codes return HTTP 400.
10. `test_translate.py::test_translate_rejects_excessively_long_text`: Confirms text over `MAX_TEXT_LENGTH` returns HTTP 400.
11. `test_translate.py::test_translate_handles_provider_failure`: Confirms upstream failures return HTTP 502 (Bad Gateway) without fake results.
12. `test_translate.py::test_translate_handles_provider_rate_limit`: Confirms upstream 429 returns HTTP 503 (Service Unavailable).
13. `test_translate.py::test_translate_handles_provider_timeout`: Confirms provider timeouts return HTTP 504 (Gateway Timeout).

---

## 10. Error Handling & HTTP Status Codes

The API employs strict error handling to guarantee that internal tracebacks and Python error details are never exposed to clients:

| Status Code | Description | Example Trigger |
| :--- | :--- | :--- |
| **`400 Bad Request`** | Client input validation error | Empty/whitespace text, unsupported source or target language, text exceeding max character limit. |
| **`502 Bad Gateway`** | Upstream provider failure | External translation service connection drop or invalid response. |
| **`503 Service Unavailable`** | Upstream rate limit | Google Translate HTTP 429 (Too Many Requests / IP rate limit). |
| **`504 Gateway Timeout`** | Upstream timeout | External provider exceeded `TRANSLATION_TIMEOUT_SECONDS`. |
| **`500 Internal Server Error`** | Unhandled internal exception | Catastrophic failure (traceback logged securely on server, sanitized message returned to client). |

**Sample Error Response (400 Bad Request - Unsupported Language):**
```json
{
  "detail": "Unsupported target language 'fr'. Supported regional languages: 'kn' (Kannada), 'hi' (Hindi), 'ta' (Tamil), 'te' (Telugu), 'ml' (Malayalam), 'mr' (Marathi), 'bn' (Bengali), 'gu' (Gujarati), 'pa' (Punjabi), 'or' (Odia), 'ur' (Urdu)."
}
```

**Sample Error Response (400 Bad Request - Empty Text):**
```json
{
  "detail": "Text cannot be empty or contain only whitespace.",
  "error_code": "VALIDATION_ERROR"
}
```

---

## 11. Provider Limitations & Production Guidance

### GoogleTrans Initial Prototype Caveats
- `googletrans==4.0.2` queries Google Translate's unofficial web scraper endpoints (`translate.googleapis.com` / `translate.google.com`).
- **No SLA:** Google does not provide an SLA or uptime guarantee for web-scraping endpoints.
- **IP Rate Limits (HTTP 429):** Datacenter or cloud server IP addresses (AWS, GCP, Azure, DigitalOcean) are frequently rate-limited by Google's anti-bot protections.
- **Fail-Safe Design:** This service is intentionally designed **never to return fake or dummy translations** when upstream rate limits or errors occur. If upstream returns 429, the API correctly returns HTTP 503 instead of masking the failure.

### Swapping to Production Providers (e.g. Bhashini, Google Cloud, Azure)
Because the translation engine is decoupled behind `BaseTranslationProvider` (in `app/services/translation_service.py`), migrating to an enterprise API requires only implementing a new provider class:
```python
class GoogleCloudTranslateProvider(BaseTranslationProvider):
    async def translate(self, text: str, source_lang: str, target_lang: str, timeout: float) -> str:
        # Call official Google Cloud Translation API via gRPC or REST
        ...
```
No modifications to API routes or validation schemas are needed.

---

## 12. Docker Deployment

### Step 1: Build Docker Image
```bash
docker build -t vaps-language-translator:latest .
```

### Step 2: Run Container
```bash
docker run -d -p 8000:8000 --name language-translator vaps-language-translator:latest
```

### Step 3: Check Health Status
```bash
curl http://localhost:8000/health
```

---

## 13. Vercel Deployment

Deploying this FastAPI service on Vercel is fully pre-configured using `vercel.json` and the serverless entrypoint `api/index.py`:

### Method 1: Deploy with Vercel CLI
```bash
# 1. Install Vercel CLI (if needed)
npm install -g vercel

# 2. Login and deploy
vercel
```
Follow the interactive prompts (accept defaults). When prompted for production deployment:
```bash
vercel --prod
```

### Method 2: Deploy via GitHub
1. Commit and push this project to a GitHub repository.
2. Go to [vercel.com](https://vercel.com), click **"Add New Project"**, and select your repository.
3. Vercel will automatically detect `vercel.json`, `requirements.txt`, and `api/index.py`.
4. (Optional) In **Environment Variables**, you can set `TRANSLATION_TIMEOUT_SECONDS=15.0`.
5. Click **"Deploy"**.

Once deployed, your live endpoints will be instantly accessible:
- Swagger UI: `https://<your-vercel-domain>/docs`
- Health check: `https://<your-vercel-domain>/health`
- Supported languages: `https://<your-vercel-domain>/languages`
- Translate text: `POST https://<your-vercel-domain>/translate`
- Translate document: `POST https://<your-vercel-domain>/translate/document`

---

## 14. Future Authentication Roadmap

For the initial prototype, authentication has been omitted to simplify development and testing. Before deploying to public production, one of the following standard patterns should be added:

1. **API Key Authentication:**
   - Inject a custom FastAPI dependency `Security(APIKeyHeader(name="X-API-Key"))`.
   - Validate against keys stored in Redis or database.
2. **OAuth2 with JWT (JSON Web Tokens):**
   - Use `fastapi.security.OAuth2PasswordBearer` to validate signed JWT tokens from VAPS Technosoft's identity provider (e.g., Keycloak or Azure AD).
3. **API Gateway Rate Limiting:**
   - Place an API Gateway (e.g., Kong, NGINX, or AWS API Gateway) in front of the service to enforce per-client rate limits and IP whitelisting.

---

## 15. License & Credits

Developed for **VAPS Technosoft**.
All rights reserved.
