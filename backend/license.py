"""
Money Radar — License Backend Module

Provides:
- License code generation (JWT)
- License validation middleware for FastAPI
- Per-user data API endpoints
- Database operations for license management
"""

import hashlib
import hmac
import json
import os
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

import psycopg
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel


# ===== JWT Helpers =====

def b64url_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def b64url_decode(s: str) -> bytes:
    padded = s + "=" * (4 - len(s) % 4)
    return urlsafe_b64decode(padded)


def hmac_sha256(key: str, message: str) -> bytes:
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


@lru_cache(maxsize=1)
def get_secret() -> str:
    return os.environ.get("LICENSE_SECRET_KEY", "mr-secret-key-change-me")


def generate_license(
    user_id: str,
    days: int = 30,
    level: str = "pro",
    secret: Optional[str] = None,
) -> tuple[str, str]:
    """Generate a license code. Returns (token, license_id)."""
    secret = secret or get_secret()
    license_id = str(uuid.uuid4())[:8]

    header = b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64url_encode(json.dumps({
        "sub": user_id,
        "exp": int(time.time()) + days * 86400,
        "iat": int(time.time()),
        "level": level,
        "lid": license_id,
    }, separators=(",", ":")).encode())

    sig = b64url_encode(hmac_sha256(secret, f"{header}.{payload}"))
    token = f"{header}.{payload}.{sig}"
    return token, license_id


def verify_license(token: str, secret: Optional[str] = None) -> Optional[dict]:
    """Verify JWT and return payload, or None if invalid."""
    secret = secret or get_secret()
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        expected_sig = b64url_encode(hmac_sha256(secret, f"{header_b64}.{payload_b64}"))
        if not hmac.compare_digest(signature_b64, expected_sig):
            return None

        # Decode payload
        payload = json.loads(b64url_decode(payload_b64))

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return {"error": "expired", "exp": payload.get("exp")}

        return payload
    except Exception:
        return None


def hash_code(code: str) -> str:
    """SHA256 hash of license code for database storage."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


# ===== Database Operations =====

def get_db_connection():
    """Get PostgreSQL connection from environment."""
    host = os.environ.get("FFUN_POSTGRESQL__HOST", "postgresql")
    user = os.environ.get("FFUN_POSTGRESQL__USER", "ffun")
    password = os.environ.get("FFUN_POSTGRESQL__PASSWORD", "ffun")
    database = os.environ.get("FFUN_POSTGRESQL__DATABASE", "ffun")
    return psycopg.connect(f"postgresql://{user}:{password}@{host}/{database}")


def init_license_db():
    """Create license tables if they don't exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Licenses table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mr_licenses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    code_hash VARCHAR(64) NOT NULL UNIQUE,
                    user_id UUID NOT NULL DEFAULT gen_random_uuid(),
                    level VARCHAR(20) NOT NULL DEFAULT 'basic',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    revoked_at TIMESTAMPTZ,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # User feeds table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mr_user_feeds (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    feed_url TEXT NOT NULL,
                    feed_title TEXT,
                    feed_description TEXT,
                    subscribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, feed_url)
                )
            """)

            # User rules table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mr_user_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    required_tags TEXT[] NOT NULL DEFAULT '{}',
                    excluded_tags TEXT[] NOT NULL DEFAULT '{}',
                    score INTEGER NOT NULL DEFAULT 10,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)

            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mr_licenses_code_hash ON mr_licenses(code_hash)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mr_licenses_user_id ON mr_user_feeds(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mr_user_feeds_user_id ON mr_user_feeds(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mr_user_rules_user_id ON mr_user_rules(user_id)")

        conn.commit()
        print("License tables initialized.")
    finally:
        conn.close()


def store_license(token: str, user_id: str, level: str, expires_at: datetime):
    """Store license in database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mr_licenses (code_hash, user_id, level, status, expires_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (code_hash) DO NOTHING",
                (hash_code(token), user_id, level, "active", expires_at)
            )
        conn.commit()
    finally:
        conn.close()


def validate_license_db(token: str) -> Optional[dict]:
    """Validate license against database (check revoked status)."""
    payload = verify_license(token)
    if not payload:
        return None
    if "error" in payload:
        return payload

    # Check database for revocation
    code_hash = hash_code(token)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM mr_licenses WHERE code_hash = %s", (code_hash,))
            row = cur.fetchone()
            if row and row[0] == "revoke":
                return {"error": "revoked"}
    finally:
        conn.close()

    return payload


def get_user_id_from_license(token: str) -> Optional[str]:
    """Extract user_id from license token."""
    payload = verify_license(token)
    if not payload or "error" in payload:
        return None
    return payload.get("sub")


# ===== API Routes =====

router = APIRouter(prefix="/api/license", tags=["license"])


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


class UserFeedRequest(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None


class UserRuleRequest(BaseModel):
    required_tags: list[str]
    excluded_tags: list[str] = []
    score: int = 10


@router.post("/validate", response_model=ValidateResponse)
async def validate_license(req: ValidateRequest):
    """Validate a license code."""
    payload = verify_license(req.license_code)

    if payload is None:
        return ValidateResponse(valid=False, error="invalid", message="授权码无效，请检查后重试。")

    if "error" in payload:
        if payload["error"] == "expired":
            return ValidateResponse(
                valid=False, error="expired",
                message="授权码已过期，请续订后继续使用。",
                expires_at=payload.get("exp"),
            )
        return ValidateResponse(valid=False, error=payload["error"], message="授权码异常。")

    # Store in database if not exists
    user_id = payload.get("sub")
    level = payload.get("level", "basic")
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    store_license(req.license_code, user_id, level, expires_at)

    days_remaining = max(0, int((payload["exp"] - time.time()) / 86400))

    return ValidateResponse(
        valid=True,
        user_id=user_id,
        level=level,
        expires_at=payload["exp"],
        days_remaining=days_remaining,
        message="授权成功" if days_remaining > 7 else f"授权将在 {days_remaining} 天后过期",
    )


@router.get("/status")
async def license_status(request: Request):
    """Check current license status from request."""
    license_code = request.headers.get("X-License-Code")
    if not license_code:
        return {"valid": False, "error": "missing"}

    payload = verify_license(license_code)
    if not payload:
        return {"valid": False, "error": "invalid"}
    if "error" in payload:
        return {"valid": False, "error": payload["error"]}

    days_remaining = max(0, int((payload["exp"] - time.time()) / 86400))
    return {
        "valid": True,
        "user_id": payload.get("sub"),
        "level": payload.get("level"),
        "days_remaining": days_remaining,
    }


# ===== Per-User Data Endpoints =====

@router.post("/user/feeds")
async def get_user_feeds(request: Request):
    """Get user's subscribed feeds."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, feed_url, feed_title, feed_description FROM mr_user_feeds WHERE user_id = %s ORDER BY subscribed_at DESC",
                (user_id,)
            )
            rows = cur.fetchall()
            feeds = [
                {"id": str(r[0]), "url": r[1], "title": r[2], "description": r[3]}
                for r in rows
            ]
            return {"feeds": feeds}
    finally:
        conn.close()


@router.post("/user/feeds/add")
async def add_user_feed(request: Request, body: UserFeedRequest):
    """Add a feed to user's subscriptions."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mr_user_feeds (user_id, feed_url, feed_title, feed_description) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id, feed_url) DO NOTHING RETURNING id",
                (user_id, body.url, body.title, body.description)
            )
            row = cur.fetchone()
            conn.commit()
            return {"success": True, "id": str(row[0]) if row else None}
    finally:
        conn.close()


@router.post("/user/feeds/remove")
async def remove_user_feed(request: Request, body: dict):
    """Remove a feed from user's subscriptions."""
    user_id = getattr(request.state, "user_id", None)
    feed_id = body.get("feed_id")
    if not user_id or not feed_id:
        raise HTTPException(400, "Missing user_id or feed_id")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mr_user_feeds WHERE id = %s AND user_id = %s", (feed_id, user_id))
            conn.commit()
            return {"success": True}
    finally:
        conn.close()


@router.post("/user/rules")
async def get_user_rules(request: Request):
    """Get user's scoring rules."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, required_tags, excluded_tags, score FROM mr_user_rules WHERE user_id = %s ORDER BY score DESC",
                (user_id,)
            )
            rows = cur.fetchall()
            rules = [
                {"id": str(r[0]), "requiredTags": r[1], "excludedTags": r[2], "score": r[3]}
                for r in rows
            ]
            return {"rules": rules}
    finally:
        conn.close()


@router.post("/user/rules/add")
async def add_user_rule(request: Request, body: UserRuleRequest):
    """Add a scoring rule for user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(401, "Unauthorized")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mr_user_rules (user_id, required_tags, excluded_tags, score) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, body.required_tags, body.excluded_tags, body.score)
            )
            row = cur.fetchone()
            conn.commit()
            return {"success": True, "id": str(row[0])}
    finally:
        conn.close()


@router.post("/user/rules/delete")
async def delete_user_rule(request: Request, body: dict):
    """Delete a user's scoring rule."""
    user_id = getattr(request.state, "user_id", None)
    rule_id = body.get("rule_id")
    if not user_id or not rule_id:
        raise HTTPException(400, "Missing user_id or rule_id")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM mr_user_rules WHERE id = %s AND user_id = %s", (rule_id, user_id))
            conn.commit()
            return {"success": True}
    finally:
        conn.close()


# ===== Middleware =====

class LicenseMiddleware:
    """ASGI middleware that validates license on every request."""

    EXCLUDED_PATHS = {
        "/api/license/validate",
        "/api/license/status",
        "/health",
        "/healthz",
        "/docs",
        "/openapi.json",
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")

        # Skip excluded paths
        if path in self.EXCLUDED_PATHS or path.startswith("/static/"):
            return await self.app(scope, receive, send)

        # Extract license from headers
        license_code = None
        for name, value in scope.get("headers", []):
            if name == b"x-license-code":
                license_code = value.decode("utf-8")
                break

        # Also check cookie
        if not license_code:
            for name, value in scope.get("headers", []):
                if name == b"cookie":
                    cookies = value.decode("utf-8")
                    for cookie in cookies.split(";"):
                        cookie = cookie.strip()
                        if cookie.startswith("mr_license="):
                            license_code = cookie.split("=", 1)[1]
                            break

        if not license_code:
            # Return 401
            response = JSONResponse(
                status_code=401,
                content={"error": "license_required", "message": "请输入授权码"},
            )
            return await response(scope, receive, send)

        # Validate
        payload = verify_license(license_code)
        if not payload:
            response = JSONResponse(
                status_code=401,
                content={"error": "license_invalid", "message": "授权码无效"},
            )
            return await response(scope, receive, send)

        if "error" in payload:
            response = JSONResponse(
                status_code=401,
                content={"error": "license_expired", "message": "授权码已过期，请续订"},
            )
            return await response(scope, receive, send)

        # Inject user_id into request state
        user_id = payload.get("sub")
        scope["state"] = scope.get("state", {})
        scope["state"]["user_id"] = user_id
        scope["state"]["license"] = payload

        return await self.app(scope, receive, send)


# ===== Integration Helper =====

def setup_license(app):
    """Call this to register license middleware and routes on a FastAPI app."""
    # Init database tables
    try:
        init_license_db()
    except Exception as e:
        print(f"Warning: Could not init license DB: {e}")

    # Add middleware
    app.add_middleware(LicenseMiddleware)

    # Add routes
    app.include_router(router)
