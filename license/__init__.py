"""
Money Radar — License Integration

Adds license middleware and routes to feeds.fun's FastAPI application.

Integration point: import this module in feeds.fun's app setup.
"""

from fastapi import FastAPI

from .middleware import LicenseMiddleware
from .routes import router


def setup_license(app: FastAPI) -> None:
    """Register license middleware and routes on a FastAPI app.

    Call this in feeds.fun's application.py:

        from license import setup_license
        setup_license(app)
    """
    # Add middleware (runs on every request)
    app.add_middleware(LicenseMiddleware)

    # Add routes
    app.include_router(router)
