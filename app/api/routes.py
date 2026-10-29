"""
API Router endpoints for Language Translator.

Provides endpoints for:
- GET /health: Health check status
- GET /languages: List of all supported Indian regional languages
- POST /translate: Translate English text into regional languages
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from app.core.config import (
    SUPPORTED_TARGET_LANGUAGES,
    resolve_source_language_code,
    resolve_target_language_code,
)
from app.schemas.translator import (
    DocumentTranslationResponse,
    ErrorResponse,
    HealthResponse,
    LanguageItem,
    LanguagesResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.services.translation_service import (
    TranslationService,
    TranslationServiceException,
    create_translated_docx,
    extract_text_from_file,
    get_translation_service,
)

router = APIRouter(tags=["Translation"])


@router.get(
    "/",
    summary="API Root Index",
    description="Welcome endpoint providing API status and navigation links.",
    status_code=status.HTTP_200_OK,
)
async def api_root():
    """Welcome and API discovery endpoint."""
    return {
        "service": "Language Translator API - VAPS Technosoft",
        "version": "1.0.0",
        "status": "healthy",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "endpoints": {
            "health": "/health",
            "supported_languages": "/languages",
            "translate": "/translate [POST]",
            "translate_document": "/translate/document [POST multipart/form-data]",
            "translate_document_download": "/translate/document/download [POST multipart/form-data]",
        },
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verify whether the Language Translator API service is running.",
    status_code=status.HTTP_200_OK,
)
async def health_check() -> HealthResponse:
    """Return the health status of the service."""
    return HealthResponse(
        status="healthy",
        service="Language Translator API",
    )


@router.get(
    "/languages",
    response_model=LanguagesResponse,
    summary="Supported Regional Languages",
    description="Return all supported Indian regional languages and their ISO codes.",
    status_code=status.HTTP_200_OK,
)
async def get_supported_languages() -> LanguagesResponse:
    """Return all configured Indian regional languages."""
    languages_list = [
        LanguageItem(code=code, name=name)
        for code, name in SUPPORTED_TARGET_LANGUAGES.items()
    ]
    return LanguagesResponse(languages=languages_list)


@router.post(
    "/translate",
    response_model=TranslationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or unsupported language."},
        502: {"model": ErrorResponse, "description": "Upstream translation provider unavailable."},
        503: {"model": ErrorResponse, "description": "Translation provider rate limit reached."},
        504: {"model": ErrorResponse, "description": "Translation provider timed out."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
    summary="Translate Text",
    description=(
        "Translate English input text into a specified Indian regional language. "
        "Returns the translated text or an informative error."
    ),
    status_code=status.HTTP_200_OK,
)
async def translate_text(
    request: TranslationRequest,
    service: TranslationService = Depends(get_translation_service),
) -> TranslationResponse:
    """Translate English text into a target Indian regional language."""
    try:
        translated_result = await service.translate(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
        )

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_result,
            source_language=resolve_source_language_code(request.source_language) or request.source_language.strip().lower(),
            target_language=resolve_target_language_code(request.target_language) or request.target_language.strip().lower(),
            status="success",
        )

    except TranslationServiceException as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        # Prevent exposing internal Python exception details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal server error occurred during translation.",
        ) from exc


@router.post(
    "/translate/document",
    response_model=DocumentTranslationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file format or empty document."},
        502: {"model": ErrorResponse, "description": "Upstream translation provider unavailable."},
        503: {"model": ErrorResponse, "description": "Translation provider rate limit reached."},
        504: {"model": ErrorResponse, "description": "Translation provider timed out."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
    },
    summary="Translate Document (Word, PDF, Text)",
    description=(
        "Upload a Word document (.docx), PDF (.pdf), or Text (.txt) file to translate "
        "its contents into an Indian regional language."
    ),
    status_code=status.HTTP_200_OK,
)
async def translate_document(
    file: UploadFile = File(..., description="Upload Word (.docx), PDF (.pdf), or Text (.txt) file"),
    source_language: str = Form("en", description="Source language code (e.g., 'en')"),
    target_language: str = Form(..., description="Target Indian language code (e.g., 'kn', 'hi', 'ta')"),
    service: TranslationService = Depends(get_translation_service),
) -> DocumentTranslationResponse:
    """Extract text from uploaded document and translate it into target regional language."""
    try:
        content = await file.read()
        extracted_text, file_type = extract_text_from_file(file.filename or "uploaded.docx", content)

        translated_result = await service.translate(
            text=extracted_text,
            source_language=source_language,
            target_language=target_language,
        )

        return DocumentTranslationResponse(
            filename=file.filename or "uploaded_document",
            file_type=file_type,
            original_characters=len(extracted_text),
            original_text=extracted_text,
            translated_text=translated_result,
            source_language=resolve_source_language_code(source_language) or source_language.strip().lower(),
            target_language=resolve_target_language_code(target_language) or target_language.strip().lower(),
            status="success",
        )

    except TranslationServiceException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the document.",
        ) from exc


@router.post(
    "/translate/document/download",
    summary="Translate Document and Download as Word (.docx)",
    description=(
        "Upload a Word document (.docx), PDF (.pdf), or Text (.txt) file and download "
        "the translated document directly as a Microsoft Word (.docx) file."
    ),
    status_code=status.HTTP_200_OK,
)
async def translate_document_and_download(
    file: UploadFile = File(..., description="Upload Word (.docx), PDF (.pdf), or Text (.txt) file"),
    source_language: str = Form("en", description="Source language code (e.g., 'en')"),
    target_language: str = Form(..., description="Target Indian language code (e.g., 'kn', 'hi', 'ta')"),
    service: TranslationService = Depends(get_translation_service),
) -> Response:
    """Translate document and return downloadable Word (.docx) file."""
    try:
        content = await file.read()
        extracted_text, _ = extract_text_from_file(file.filename or "uploaded.docx", content)

        translated_result = await service.translate(
            text=extracted_text,
            source_language=source_language,
            target_language=target_language,
        )

        base_name = file.filename.rsplit(".", 1)[0] if file.filename and "." in file.filename else "translated"
        docx_bytes = create_translated_docx(translated_result, title=f"Translated - {base_name}")

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="translated_{base_name}.docx"'},
        )

    except TranslationServiceException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the translated document.",
        ) from exc
