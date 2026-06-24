"""
Money Radar — License Code Generator

Generates JWT-based license codes for user authorization.

Usage:
    python3 license_gen.py --user-id user001 --expiry 2026-12-31 --level pro
    python3 license_gen.py --user-id user001 --days 30 --level basic
    python3 license_gen.py --batch 10 --days 30 --level pro
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta, timezone
from typing import Optional


DEFAULT_SECRET = "money-radar-secret-change-me"


def b64url(data: bytes) -> str:
    """Base64url encode without padding."""
    return urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def hmac_sha256(key: str, message: str) -> bytes:
    """HMAC-SHA256 signature."""
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()


def generate_license(
    user_id: str,
    expiry_date: datetime,
    level: str = "pro",
    secret: str = DEFAULT_SECRET,
    license_id: Optional[str] = None,
) -> str:
    """Generate a JWT license code.

    Args:
        user_id: Unique user identifier
        expiry_date: When the license expires (UTC)
        level: Permission level (basic, pro, enterprise)
        secret: HMAC secret key
        license_id: Unique license ID (auto-generated if None)

    Returns:
        JWT string (xxxxx.yyyyy.zzzzz)
    """
    if license_id is None:
        license_id = str(uuid.uuid4())[:8]

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "exp": int(expiry_date.timestamp()),
        "iat": int(time.time()),
        "level": level,
        "lid": license_id,
    }

    header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac_sha256(secret, signing_input)
    signature_b64 = b64url(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_license(token: str, secret: str = DEFAULT_SECRET) -> Optional[dict]:
    """Verify and decode a license code.

    Args:
        token: JWT string
        secret: HMAC secret key

    Returns:
        Decoded payload dict if valid, None if invalid
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac_sha256(secret, signing_input)
        expected_sig_b64 = b64url(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None

        # Decode payload
        # Add back padding
        padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_bytes = urlsafe_b64decode(padded)
        payload = json.loads(payload_bytes)

        # Check expiry
        if payload.get("exp", 0) < time.time():
            return {"error": "expired", "exp": payload.get("exp")}

        return payload

    except Exception:
        return None


def urlsafe_b64decode(s: str) -> bytes:
    """Base64url decode with padding handling."""
    from base64 import urlsafe_b64decode as _decode

    padded = s + "=" * (4 - len(s) % 4)
    return _decode(padded)


def format_license_display(token: str) -> str:
    """Format license code for display (XXXX-XXXX-XXXX-XXXX)."""
    # Take first 16 chars of the token (before the dots) and format
    clean = token.replace(".", "")
    if len(clean) >= 16:
        return "-".join([clean[i : i + 4] for i in range(0, 16, 4)])
    return token


def main():
    parser = argparse.ArgumentParser(description="Money Radar License Generator")
    parser.add_argument("--user-id", default="default", help="User ID (default: default)")
    parser.add_argument("--expiry", help="Expiry date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="Days from now until expiry")
    parser.add_argument("--level", default="pro", choices=["basic", "pro", "enterprise"], help="Permission level")
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="HMAC secret key")
    parser.add_argument("--batch", type=int, help="Generate N licenses at once")
    parser.add_argument("--verify", help="Verify a license code")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Verify mode
    if args.verify:
        result = verify_license(args.verify, args.secret)
        if result:
            if "error" in result:
                print(f"LICENSE EXPIRED on {datetime.fromtimestamp(result['exp'], tz=timezone.utc).isoformat()}")
                sys.exit(1)
            else:
                print(f"LICENSE VALID")
                print(f"  User:   {result.get('sub')}")
                print(f"  Level:  {result.get('level')}")
                print(f"  ID:     {result.get('lid')}")
                print(f"  Expiry: {datetime.fromtimestamp(result['exp'], tz=timezone.utc).isoformat()}")
        else:
            print("LICENSE INVALID")
            sys.exit(1)
        return

    # Calculate expiry
    if args.expiry:
        expiry_date = datetime.strptime(args.expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    elif args.days:
        expiry_date = datetime.now(timezone.utc) + timedelta(days=args.days)
    else:
        print("ERROR: Either --expiry or --days is required")
        sys.exit(1)

    # Generate
    count = args.batch or 1
    results = []

    for i in range(count):
        user_id = f"{args.user_id}-{i+1:04d}" if args.batch else args.user_id
        token = generate_license(user_id, expiry_date, args.level, args.secret)
        results.append({"user_id": user_id, "token": token, "display": format_license_display(token)})

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        if count > 1:
            print(f"Generated {count} licenses (level={args.level}, expiry={expiry_date.date()}):\n")
        else:
            print(f"License generated (level={args.level}, expiry={expiry_date.date()}):\n")

        for r in results:
            print(f"  User:    {r['user_id']}")
            print(f"  License: {r['token']}")
            print(f"  Display: {r['display']}")
            print()


if __name__ == "__main__":
    main()
