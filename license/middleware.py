"""
Money Radar — License Validation Middleware for FastAPI

Intercepts all requests and checks for valid license.
Excluded paths: /api/license/validate, /health, /docs, /openapi.json
"""

import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from functools import lru_cache
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# Paths that don't require license validation
EXCLUDED_PATHS = {
    "/api/license/validate",
    "/api/license/status",
    "/health",
    "/healthz",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Cookie name for storing license
LICENSE_COOKIE_NAME = "mr_license"

# Header name
LICENSE_HEADER_NAME = "X-License-Code"


@lru_cache(maxsize=1)
def _get_secret() -> str:
    """Get license secret from environment."""
    import os

    return os.environ.get("LICENSE_SECRET_KEY", "money-radar-secret-change-me")


def b64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def hmac_sha256(key: str, message: str) -> bytes:
    """HMAC-SHA256 signature."""
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


def verify_license_token(token: str) -> Optional[dict]:
    """Verify JWT license token.

    Returns:
        Payload dict if valid, None if invalid or expired
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        secret = _get_secret()

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac_sha256(secret, signing_input)
        expected_sig_b64 = b64url_encode(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None

        # Decode payload
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_bytes = urlsafe_b64decode(padded)
        payload = json.loads(payload_bytes)

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return {"error": "expired", "exp": payload.get("exp")}

        return payload

    except Exception:
        return None


def extract_license_from_request(request: Request) -> Optional[str]:
    """Extract license code from request (header, cookie, or query param)."""
    # 1. Check header
    license_code = request.headers.get(LICENSE_HEADER_NAME)
    if license_code:
        return license_code

    # 2. Check cookie
    license_code = request.cookies.get(LICENSE_COOKIE_NAME)
    if license_code:
        return license_code

    # 3. Check query param (for initial setup)
    license_code = request.query_params.get("license")
    if license_code:
        return license_code

    return None


class LicenseMiddleware(BaseHTTPMiddleware):
    """Middleware that validates license codes on all requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip excluded paths
        path = request.url.path
        if path in EXCLUDED_PATHS or path.startswith("/static/"):
            return await call_next(request)

        # Skip if license validation is disabled
        import os

        if os.environ.get("LICENSE_DISABLED", "").lower() in ("true", "1", "yes"):
            return await call_next(request)

        # Extract license
        license_code = extract_license_from_request(request)

        if not license_code:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "license_required",
                    "message": "授权码 required. Provide via X-License-Code header or mr_license cookie.",
                },
            )

        # Verify
        payload = verify_license_token(license_code)

        if payload is None:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "license_invalid",
                    "message": "授权码无效，请检查后重试。",
                },
            )

        if "error" in payload and payload["error"] == "expired":
            return JSONResponse(
                status_code=401,
                content={
                    "error": "license_expired",
                    "message": "授权码已过期，请续订后继续使用。",
                    "expired_at": payload.get("exp"),
                },
            )

        # Add license info to request state
        request.state.license = payload

        # Continue to next middleware/handler
        response = await call_next(request)

        # If license is valid and was provided via query param, set cookie
        if request.query_params.get("license"):
            response.set_cookie(
                key=LICENSE_COOKIE_NAME,
                value=license_code,
                max_age=86400 * 365,  # 1 year
                httponly=True,
                samesite="lax",
            )

        return response
