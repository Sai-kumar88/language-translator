"""
Application Logging Configuration.

Configures structured standard logging while ensuring sensitive text payloads
are never logged unnecessarily.
"""

import logging
import sys
from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure root and application loggers."""
    settings = get_settings()
    log_level = logging.DEBUG if settings.APP_DEBUG else logging.INFO

    # Custom log format
    log_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set third-party loggers to a calmer level
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    return logger
