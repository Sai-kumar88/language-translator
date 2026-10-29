"""
Application Configuration Module.

Loads configuration from environment variables and provides centralized settings.
"""

from functools import lru_cache
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict


# Supported Indian regional languages mapped to their standard ISO 639-1 / 639-2 codes
SUPPORTED_TARGET_LANGUAGES: Dict[str, str] = {
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

# Supported source languages (extensible)
SUPPORTED_SOURCE_LANGUAGES: Dict[str, str] = {
    "en": "English",
}

# Mapping of lowercase full names and aliases to canonical ISO language codes
TARGET_LANGUAGE_NAME_TO_CODE: Dict[str, str] = {
    name.lower(): code for code, name in SUPPORTED_TARGET_LANGUAGES.items()
}
TARGET_LANGUAGE_NAME_TO_CODE["oriya"] = "or"

SOURCE_LANGUAGE_NAME_TO_CODE: Dict[str, str] = {
    name.lower(): code for code, name in SUPPORTED_SOURCE_LANGUAGES.items()
}


def resolve_target_language_code(lang_input: str) -> str | None:
    """Resolve target language from code (e.g. 'te') or full name (e.g. 'telugu'/'Telugu') to standard code."""
    if not lang_input:
        return None
    cleaned = lang_input.strip().lower()
    if cleaned in SUPPORTED_TARGET_LANGUAGES:
        return cleaned
    if cleaned in TARGET_LANGUAGE_NAME_TO_CODE:
        return TARGET_LANGUAGE_NAME_TO_CODE[cleaned]
    return None


def resolve_source_language_code(lang_input: str) -> str | None:
    """Resolve source language from code (e.g. 'en') or full name (e.g. 'english'/'English') to standard code."""
    if not lang_input:
        return None
    cleaned = lang_input.strip().lower()
    if cleaned in SUPPORTED_SOURCE_LANGUAGES:
        return cleaned
    if cleaned in SOURCE_LANGUAGE_NAME_TO_CODE:
        return SOURCE_LANGUAGE_NAME_TO_CODE[cleaned]
    return None


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General Application Settings
    APP_NAME: str = "Language Translator API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    API_PREFIX: str = ""
    CORS_ORIGINS: List[str] = ["*"]

    # Translation Constraints
    MAX_TEXT_LENGTH: int = 150000
    CHUNK_SIZE: int = 2500
    DEFAULT_SOURCE_LANGUAGE: str = "en"
    TRANSLATION_TIMEOUT_SECONDS: float = 60.0

    # Provider Configuration
    TRANSLATION_PROVIDER: str = "googletrans"
    GOOGLETRANS_SERVICE_URLS: List[str] = [
        "translate.google.com",
        "translate.googleapis.com",
    ]


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached settings instance."""
    return Settings()
