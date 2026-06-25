#!/usr/bin/env python3
"""
Money Radar — License Generator CLI

Usage:
    python3 license_gen.py --user-id user001 --days 30 --level pro
    python3 license_gen.py --batch 10 --days 90 --level basic
    python3 license_gen.py --verify <token>
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Optional


DEFAULT_SECRET = os.environ.get("LICENSE_SECRET_KEY", "mr-secret-key-change-me")


def b64url_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def b64url_decode(s: str) -> bytes:
    padded = s + "=" * (4 - len(s) % 4)
    return urlsafe_b64decode(padded)


def hmac_sha256(key: str, message: str) -> bytes:
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


def generate_license(user_id: str, days: int = 30, level: str = "pro", secret: str = DEFAULT_SECRET) -> tuple:
    """Generate license. Returns (token, license_id)."""
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


def verify_license(token: str, secret: str = DEFAULT_SECRET) -> Optional[dict]:
    """Verify JWT. Returns payload or None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        expected_sig = b64url_encode(hmac_sha256(secret, f"{header_b64}.{payload_b64}"))
        if not hmac.compare_digest(signature_b64, expected_sig):
            return None

        payload = json.loads(b64url_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return {"error": "expired", "exp": payload.get("exp")}

        return payload
    except Exception:
        return None


def format_display(token: str) -> str:
    """Format for display: XXXX-XXXX-XXXX-XXXX."""
    clean = token.replace(".", "")[:16]
    return "-".join([clean[i:i+4] for i in range(0, len(clean), 4)])


def main():
    parser = argparse.ArgumentParser(description="Money Radar License Generator")
    parser.add_argument("--user-id", default="default", help="User ID")
    parser.add_argument("--days", type=int, default=30, help="Days until expiry")
    parser.add_argument("--level", default="pro", choices=["basic", "pro", "enterprise"])
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="HMAC secret key")
    parser.add_argument("--batch", type=int, help="Generate N licenses")
    parser.add_argument("--verify", help="Verify a license token")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Verify mode
    if args.verify:
        result = verify_license(args.verify, args.secret)
        if result:
            if "error" in result:
                print(f"EXPIRED on {datetime.fromtimestamp(result['exp'], tz=timezone.utc).isoformat()}")
                sys.exit(1)
            else:
                print(f"VALID")
                print(f"  User:   {result.get('sub')}")
                print(f"  Level:  {result.get('level')}")
                print(f"  ID:     {result.get('lid')}")
                print(f"  Expiry: {datetime.fromtimestamp(result['exp'], tz=timezone.utc).isoformat()}")
        else:
            print("INVALID")
            sys.exit(1)
        return

    # Generate
    count = args.batch or 1
    results = []

    for i in range(count):
        user_id = f"{args.user_id}-{i+1:04d}" if args.batch else args.user_id
        token, lid = generate_license(user_id, args.days, args.level, args.secret)
        results.append({"user_id": user_id, "token": token, "display": format_display(token), "license_id": lid})

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if count > 1:
            print(f"Generated {count} licenses (level={args.level}, days={args.days}):\n")
        else:
            print(f"License generated (level={args.level}, days={args.days}):\n")

        for r in results:
            print(f"  User:    {r['user_id']}")
            print(f"  License: {r['token']}")
            print(f"  Display: {r['display']}")
            print()


if __name__ == "__main__":
    main()
