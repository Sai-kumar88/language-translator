"""
Pydantic schemas for request validation and response models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy", description="Current health status")
    service: str = Field(
        default="Language Translator API",
        description="Name of the service",
    )


class LanguageItem(BaseModel):
    """Schema representing an individual supported language."""

    code: str = Field(description="ISO 639-1 / 639-2 language code")
    name: str = Field(description="Display name of the language")


class LanguagesResponse(BaseModel):
    """Response containing list of supported languages."""

    languages: List[LanguageItem] = Field(
        description="List of all supported regional languages"
    )


class TranslationRequest(BaseModel):
    """Request payload for text translation."""

    text: str = Field(
        ...,
        description="The text to be translated into the target language.",
        examples=["Welcome to our school"],
    )
    source_language: str = Field(
        default="en",
        description="Source language code (e.g., 'en' for English).",
        examples=["en"],
    )
    target_language: str = Field(
        ...,
        description="Target language code (e.g., 'kn' for Kannada, 'hi' for Hindi).",
        examples=["kn"],
    )

    @field_validator("text")
    @classmethod
    def validate_text_not_empty_or_whitespace(cls, value: str) -> str:
        """Ensure input text is neither empty nor solely whitespace."""
        if not value or not value.strip():
            raise ValueError("Text cannot be empty or contain only whitespace.")
        return value

    @field_validator("source_language", "target_language")
    @classmethod
    def normalize_language_codes(cls, value: str) -> str:
        """Normalize language codes to lowercase trimmed strings."""
        if not value or not value.strip():
            raise ValueError("Language code cannot be empty.")
        return value.strip().lower()


class TranslationResponse(BaseModel):
    """Successful translation response schema."""

    original_text: str = Field(description="The original input text")
    translated_text: str = Field(description="The translated text result")
    source_language: str = Field(description="Source language code used")
    target_language: str = Field(description="Target language code translated into")
    status: str = Field(default="success", description="Status of the operation")


class DocumentTranslationResponse(BaseModel):
    """Response schema for translated document files."""

    filename: str = Field(description="Uploaded file name")
    file_type: str = Field(description="File extension type, e.g. docx, txt, pdf")
    original_characters: int = Field(description="Total characters in extracted document")
    original_text: str = Field(description="Extracted original text")
    translated_text: str = Field(description="Complete translated document text")
    source_language: str = Field(description="Source language code")
    target_language: str = Field(description="Target language code")
    status: str = Field(default="success", description="Status of the operation")


class ErrorDetail(BaseModel):
    """Structured error detail representation."""

    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response payload."""

    detail: str = Field(description="Human-readable error description")
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error identifier",
    )
    details: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Optional list of specific field errors",
    )
