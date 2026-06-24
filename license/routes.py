"""
Money Radar — License API Routes

Endpoints:
    POST /api/license/validate — Validate a license code
    GET  /api/license/status   — Check current license status
"""

import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/license", tags=["license"])


def _get_secret() -> str:
    return os.environ.get("LICENSE_SECRET_KEY", "money-radar-secret-change-me")


def b64url_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def hmac_sha256(key: str, message: str) -> bytes:
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


def verify_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        secret = _get_secret()

        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac_sha256(secret, signing_input)
        expected_sig_b64 = b64url_encode(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None

        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_bytes = urlsafe_b64decode(padded)
        payload = json.loads(payload_bytes)

        if payload.get("exp", 0) < time.time():
            return {"error": "expired", "exp": payload.get("exp")}

        return payload

    except Exception:
        return None


class ValidateRequest(BaseModel):
    license_code: str


class ValidateResponse(BaseModel):
    valid: bool
    error: Optional[str] = None
    user_id: Optional[str] = None
    level: Optional[str] = None
    expires_at: Optional[int] = None
    days_remaining: Optional[int] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    authenticated: bool
    license_valid: bool
    user_id: Optional[str] = None
    level: Optional[str] = None
    expires_at: Optional[int] = None
    days_remaining: Optional[int] = None
    warning: Optional[str] = None


@router.post("/validate", response_model=ValidateResponse)
async def validate_license(req: ValidateRequest):
    """Validate a license code and return status."""
    payload = verify_token(req.license_code)

    if payload is None:
        return ValidateResponse(
            valid=False,
            error="invalid",
            message="授权码无效，请检查后重试。",
        )

    if "error" in payload and payload["error"] == "expired":
        return ValidateResponse(
            valid=False,
            error="expired",
            message="授权码已过期，请续订后继续使用。",
            expires_at=payload.get("exp"),
        )

    exp = payload.get("exp", 0)
    days_remaining = max(0, int((exp - time.time()) / 86400))

    return ValidateResponse(
        valid=True,
        user_id=payload.get("sub"),
        level=payload.get("level"),
        expires_at=exp,
        days_remaining=days_remaining,
        message="授权成功" if days_remaining > 7 else f"授权将在 {days_remaining} 天后过期",
    )


@router.get("/status", response_model=StatusResponse)
async def license_status(request: Request):
    """Check current license status from request context."""
    license_payload = getattr(request.state, "license", None)

    if license_payload is None:
        return StatusResponse(
            authenticated=False,
            license_valid=False,
            warning="未提供授权码",
        )

    if "error" in license_payload:
        return StatusResponse(
            authenticated=True,
            license_valid=False,
            warning="授权码已过期",
        )

    exp = license_payload.get("exp", 0)
    days_remaining = max(0, int((exp - time.time()) / 86400))

    warning = None
    if days_remaining <= 1:
        warning = "授权即将过期，请立即续订"
    elif days_remaining <= 3:
        warning = f"授权将在 {days_remaining} 天后过期"
    elif days_remaining <= 7:
        warning = f"授权将在 {days_remaining} 天后过期，建议续订"

    return StatusResponse(
        authenticated=True,
        license_valid=True,
        user_id=license_payload.get("sub"),
        level=license_payload.get("level"),
        expires_at=exp,
        days_remaining=days_remaining,
        warning=warning,
    )
