"""
FastAPI Application Entrypoint for Language Translator API.

VAPS Technosoft - Language Translator REST API.
"""

from contextlib import asynccontextmanager
import json
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging

# Setup centralized logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    settings = get_settings()
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_application() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.APP_NAME} - VAPS Technosoft",
        description=(
            "A professional, modular, and scalable Language Translator REST API "
            "designed to translate English text into Indian regional languages (Kannada, "
            "Hindi, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, Punjabi, "
            "Odia, and Urdu)."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Lenient JSON parser middleware for handling multi-line paragraphs pasted into Swagger
    class LenientJsonASGIMiddleware:
        """Allow lenient JSON parsing (strict=False) to accept multi-line paragraphs pasted into Swagger."""

        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                headers = dict(scope.get("headers", []))
                content_type = headers.get(b"content-type", b"").decode("latin-1")
                if "application/json" in content_type:
                    body = bytearray()
                    while True:
                        message = await receive()
                        body.extend(message.get("body", b""))
                        if not message.get("more_body", False):
                            break
                    try:
                        json.loads(body)
                    except Exception:
                        try:
                            data = json.loads(body.decode("utf-8", errors="replace"), strict=False)
                            body = json.dumps(data).encode("utf-8")
                        except Exception:
                            pass

                    async def custom_receive():
                        return {"type": "http.request", "body": bytes(body), "more_body": False}

                    await self.app(scope, custom_receive, send)
                    return
            await self.app(scope, receive, send)

    app.add_middleware(LenientJsonASGIMiddleware)

    # Custom exception handler for validation errors to ensure clean responses
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first_error = exc.errors()[0] if exc.errors() else None
        msg = first_error.get("msg") if first_error else "Validation error in request."
        # Strip ValueError prefix if present
        if msg.startswith("Value error, "):
            msg = msg.replace("Value error, ", "")

        if "json decode error" in msg.lower():
            msg = (
                "Invalid JSON syntax in request body. If you pasted multi-line text or paragraphs, "
                "ensure internal quotation marks are escaped (\\\") and the JSON format remains valid."
            )

        logger.warning("Request validation error on %s: %s", request.url.path, msg)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": msg,
                "error_code": "VALIDATION_ERROR",
            },
        )

    # Custom exception handler for HTTPExceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTP exception on %s [%d]: %s",
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
            },
        )

    # Fallback exception handler to never leak internal Python traces
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s: %s",
            request.url.path,
            type(exc).__name__,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please contact system administrator.",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )

    # Register API routes
    app.include_router(router, prefix=settings.API_PREFIX)

    return app


app = create_application()
