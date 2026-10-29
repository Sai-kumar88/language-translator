"""
Translation Service and Provider Abstraction Layer.

Defines the pluggable translation provider interface and implements the
GoogleTrans provider with robust error handling, timeout management,
and security logging.
"""

import abc
import asyncio
import io
import logging
import re
import time
from typing import List, Optional, Sequence, Tuple
import docx
import httpx
import pypdf
from googletrans import Translator

from app.core.config import (
    SUPPORTED_SOURCE_LANGUAGES,
    SUPPORTED_TARGET_LANGUAGES,
    Settings,
    get_settings,
    resolve_source_language_code,
    resolve_target_language_code,
)

logger = logging.getLogger("app.translation_service")


# Custom Service Exceptions
class TranslationServiceException(Exception):
    """Base exception for translation service errors."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "TRANSLATION_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class UnsupportedLanguageException(TranslationServiceException):
    """Raised when an unsupported source or target language code is requested."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="UNSUPPORTED_LANGUAGE")


class UnsupportedFileFormatException(TranslationServiceException):
    """Raised when an unsupported file type is uploaded."""

    def __init__(self, message: str = "Unsupported file format. Please upload Word (.docx), PDF (.pdf), or Text (.txt) files."):
        super().__init__(message, status_code=400, error_code="UNSUPPORTED_FILE_FORMAT")


class TextTooLongException(TranslationServiceException):
    """Raised when the text exceeds the maximum allowable character length."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="TEXT_TOO_LONG")


class EmptyTextException(TranslationServiceException):
    """Raised when the text is empty or contains only whitespace."""

    def __init__(self, message: str = "Text cannot be empty or contain only whitespace."):
        super().__init__(message, status_code=400, error_code="EMPTY_TEXT")


class ProviderRateLimitException(TranslationServiceException):
    """Raised when the external translation provider is rate-limited (HTTP 429)."""

    def __init__(self, message: str = "Translation service provider rate limit reached. Please try again later."):
        super().__init__(message, status_code=503, error_code="PROVIDER_RATE_LIMITED")


class ProviderTimeoutException(TranslationServiceException):
    """Raised when the external translation provider request times out."""

    def __init__(self, message: str = "Translation request timed out while communicating with provider."):
        super().__init__(message, status_code=504, error_code="PROVIDER_TIMEOUT")


class ProviderUnavailableException(TranslationServiceException):
    """Raised when the upstream translation provider is unreachable or failed."""

    def __init__(self, message: str = "Translation service provider is temporarily unavailable."):
        super().__init__(message, status_code=502, error_code="PROVIDER_UNAVAILABLE")


# Pluggable Provider Interface
class BaseTranslationProvider(abc.ABC):
    """Abstract Base Class for translation providers.

    Allows replacing googletrans with other providers (e.g., Google Cloud Translate,
    Azure Translator, Bhashini, AWS Translate) without altering application routes.
    """

    @abc.abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        """Translate text from source_lang to target_lang.

        :param text: Text to translate.
        :param source_lang: Normalized source language code.
        :param target_lang: Normalized target language code.
        :param timeout: Request timeout in seconds.
        :return: Translated text string.
        """
        pass


class GoogleTransProvider(BaseTranslationProvider):
    """Translation provider implementation using the googletrans library.

    Note:
    googletrans interfaces with unofficial Google Translate web endpoints.
    As such, availability is not guaranteed in production environments
    and upstream rate limits (HTTP 429) may be encountered under high traffic
    or from datacenter IPs.
    """

    def __init__(self, service_urls: Optional[Sequence[str]] = None):
        self.service_urls = list(
            service_urls
            or ["translate.google.com", "translate.googleapis.com"]
        )

    async def _translate_via_google_client(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> Optional[str]:
        """Perform translation via Google's direct client endpoint."""
        url = "https://clients5.google.com/translate_a/t"
        params = {
            "client": "dict-chrome-ex",
            "sl": source_lang,
            "tl": target_lang,
            "q": text,
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return str(data[0])
                if isinstance(data, str):
                    return data
            elif resp.status_code == 429:
                raise ProviderRateLimitException()
            elif resp.status_code in (500, 502, 503, 504):
                raise ProviderUnavailableException(f"Google service returned status {resp.status_code}.")
        return None

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float,
    ) -> str:
        """Perform translation using googletrans with client fallback and strict error handling.

        Never falls back to returning the original or fake text when upstream fails.
        """
        last_error: Optional[Exception] = None

        # 1. Attempt standard googletrans Translator
        try:
            async with Translator(
                service_urls=self.service_urls,
                timeout=timeout,
                raise_exception=True,
            ) as translator:
                coro = translator.translate(
                    text,
                    dest=target_lang,
                    src=source_lang,
                )
                result = await asyncio.wait_for(coro, timeout=timeout)

            if hasattr(result, "_response") and getattr(result._response, "status_code", 200) != 200:
                status = result._response.status_code
                if status == 429:
                    raise ProviderRateLimitException()
                raise ProviderUnavailableException(
                    f"Upstream provider returned status {status}."
                )

            translated_text = getattr(result, "text", None)
            if translated_text and translated_text != text:
                return str(translated_text)

        except (ProviderRateLimitException, ProviderTimeoutException):
            raise
        except (asyncio.TimeoutError, httpx.TimeoutException, TimeoutError) as exc:
            logger.warning("Translation request timed out after %.2f seconds", timeout)
            raise ProviderTimeoutException() from exc
        except Exception as exc:
            last_error = exc
            logger.info("googletrans primary web endpoint rejected request (%s), attempting Google client endpoint...", type(exc).__name__)

        # 2. Attempt Google client endpoint
        try:
            client_result = await self._translate_via_google_client(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                timeout=timeout,
            )
            if client_result:
                return client_result
        except (ProviderRateLimitException, ProviderTimeoutException, ProviderUnavailableException):
            raise
        except Exception as exc:
            logger.warning("Google client endpoint encountered an error: %s", type(exc).__name__)
            last_error = exc

        # If both attempts failed
        if isinstance(last_error, (asyncio.TimeoutError, httpx.TimeoutException)) or (last_error and "timeout" in str(last_error).lower()):
            raise ProviderTimeoutException()
        raise ProviderUnavailableException("Upstream translation provider encountered an error.")


def split_text_into_chunks(text: str, max_chunk_size: int = 2500) -> List[str]:
    """Intelligently split large text into manageable chunks respecting paragraphs and sentences."""
    if len(text) <= max_chunk_size:
        return [text]

    paragraphs = text.split("\n")
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for para in paragraphs:
        if len(para) > max_chunk_size:
            # Paragraph exceeds max chunk size; split by sentence boundary
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sentence in sentences:
                if current_length + len(sentence) + 1 > max_chunk_size and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
        else:
            if current_length + len(para) + 1 > max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(para)
            current_length += len(para) + 1

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return [c for c in chunks if c.strip()]


def extract_text_from_file(filename: str, content: bytes) -> Tuple[str, str]:
    """Extract plain text from uploaded Word (.docx), PDF (.pdf), or Text (.txt) file.

    Returns tuple of (extracted_text, file_type).
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext in ("docx", "doc"):
        try:
            doc = docx.Document(io.BytesIO(content))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        paragraphs.append(" | ".join(cells))
            extracted = "\n\n".join(paragraphs).strip()
            if not extracted:
                raise EmptyTextException("The uploaded Word document contains no readable text.")
            return extracted, "docx"
        except Exception as exc:
            if isinstance(exc, TranslationServiceException):
                raise
            raise UnsupportedFileFormatException(f"Failed to read Word document: {str(exc)}") from exc

    elif ext == "pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            extracted = "\n\n".join(pages).strip()
            if not extracted:
                raise EmptyTextException("The uploaded PDF document contains no readable text.")
            return extracted, "pdf"
        except Exception as exc:
            if isinstance(exc, TranslationServiceException):
                raise
            raise UnsupportedFileFormatException(f"Failed to read PDF document: {str(exc)}") from exc

    elif ext in ("txt", "text", "md", "csv"):
        try:
            extracted = content.decode("utf-8", errors="replace").strip()
            if not extracted:
                raise EmptyTextException("The uploaded text file is empty.")
            return extracted, "txt"
        except Exception as exc:
            raise UnsupportedFileFormatException("Failed to decode text file as UTF-8.") from exc

    else:
        raise UnsupportedFileFormatException(
            f"Unsupported file type '.{ext}'. Supported formats are Word (.docx), PDF (.pdf), and Text (.txt)."
        )


def create_translated_docx(translated_text: str, title: str = "Translated Document") -> bytes:
    """Create a Word (.docx) document from translated text and return bytes."""
    doc = docx.Document()
    doc.add_heading(title, 0)
    for paragraph in translated_text.split("\n\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# Service Coordinator
class TranslationService:
    """Orchestrates translation requests, validation, chunking, and provider execution."""

    def __init__(
        self,
        provider: BaseTranslationProvider,
        settings: Optional[Settings] = None,
    ):
        self.provider = provider
        self.settings = settings or get_settings()

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Validate inputs, chunk large content if needed, and execute translation."""
        # Validate text is non-empty
        cleaned_text = text.strip() if text else ""
        if not cleaned_text:
            raise EmptyTextException()

        # Validate text length against maximum capacity
        if len(text) > self.settings.MAX_TEXT_LENGTH:
            raise TextTooLongException(
                f"Text length ({len(text)} characters) exceeds maximum allowed limit of {self.settings.MAX_TEXT_LENGTH}."
            )

        # Validate and resolve source language (supports code e.g. 'en' or full name e.g. 'English')
        resolved_src = resolve_source_language_code(source_language)
        if not resolved_src:
            supported_srcs = ", ".join(f"'{k}' ({v})" for k, v in SUPPORTED_SOURCE_LANGUAGES.items())
            raise UnsupportedLanguageException(
                f"Unsupported source language '{source_language}'. Supported source languages: {supported_srcs}."
            )
        norm_source = resolved_src

        # Validate and resolve target language (supports code e.g. 'te' or full name e.g. 'telugu'/'Telugu')
        resolved_tgt = resolve_target_language_code(target_language)
        if not resolved_tgt:
            supported_targets = ", ".join(f"'{k}' ({v})" for k, v in SUPPORTED_TARGET_LANGUAGES.items())
            raise UnsupportedLanguageException(
                f"Unsupported target language '{target_language}'. Supported regional languages: {supported_targets}."
            )
        norm_target = resolved_tgt

        start_time = time.monotonic()
        logger.info(
            "Translating text: length=%d chars, source='%s', target='%s'",
            len(text),
            norm_source,
            norm_target,
        )

        try:
            chunks = split_text_into_chunks(text, max_chunk_size=self.settings.CHUNK_SIZE)
            if len(chunks) <= 1:
                translated = await self.provider.translate(
                    text=chunks[0] if chunks else text,
                    source_lang=norm_source,
                    target_lang=norm_target,
                    timeout=self.settings.TRANSLATION_TIMEOUT_SECONDS,
                )
            else:
                logger.info(
                    "Splitting large text (%d chars) into %d chunks for translation",
                    len(text),
                    len(chunks),
                )
                semaphore = asyncio.Semaphore(4)

                async def translate_single_chunk(idx: int, chunk: str) -> Tuple[int, str]:
                    async with semaphore:
                        res = await self.provider.translate(
                            text=chunk,
                            source_lang=norm_source,
                            target_lang=norm_target,
                            timeout=self.settings.TRANSLATION_TIMEOUT_SECONDS,
                        )
                        return (idx, res)

                tasks = [translate_single_chunk(i, ch) for i, ch in enumerate(chunks)]
                chunk_results = await asyncio.gather(*tasks)
                chunk_results.sort(key=lambda x: x[0])
                translated = "\n\n".join(r[1] for r in chunk_results)

            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "Translation completed: source='%s', target='%s', duration=%.2fms",
                norm_source,
                norm_target,
                duration_ms,
            )
            return translated

        except TranslationServiceException as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "Translation failed [%s]: source='%s', target='%s', duration=%.2fms",
                exc.error_code,
                norm_source,
                norm_target,
                duration_ms,
            )
            raise


# Dependency Injection Factory
_service_instance: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Retrieve or initialize the TranslationService singleton dependency."""
    global _service_instance
    if _service_instance is None:
        settings = get_settings()
        provider = GoogleTransProvider(service_urls=settings.GOOGLETRANS_SERVICE_URLS)
        _service_instance = TranslationService(provider=provider, settings=settings)
    return _service_instance
