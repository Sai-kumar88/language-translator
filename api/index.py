"""
Vercel Serverless Entrypoint for Language Translator API.

Exposes the FastAPI 'app' ASGI instance to Vercel's Python runtime.
"""

from app.main import app

# Vercel's Python Serverless Runtime requires the ASGI app instance
# to be exposed as 'app'.
__all__ = ["app"]
