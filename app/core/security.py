"""
Security and Authentication Utility Module
Implements PBKDF2 password hashing, HMAC-SHA256 session token generation and verification.
"""

import hmac
import hashlib
import secrets
import time
import base64
import json
from app.core.config import settings

PBKDF2_ITERATIONS = 100_000

def hash_password(password: str, salt: str | None = None) -> str:
    """Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    )
    return f"{salt}:{key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plaintext password against a stored salt:hash string."""
    try:
        salt, expected_hex = hashed.split(":", 1)
        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(actual_key.hex(), expected_hex)
    except Exception:
        return False

def create_access_token(subject: str, role: str = "admin", expires_minutes: int | None = None) -> str:
    """Generates a cryptographically signed HMAC-SHA256 session token."""
    if expires_minutes is None:
        expires_minutes = settings.ADMIN_TOKEN_EXPIRY_MINUTES

    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + (expires_minutes * 60),
        "nonce": secrets.token_hex(8),
    }

    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    signature = hmac.new(
        settings.ADMIN_TOKEN_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"

def verify_access_token(token: str) -> dict | None:
    """Verifies and decodes an HMAC-SHA256 session token."""
    try:
        if "." not in token:
            return None
        payload_b64, signature = token.split(".", 1)

        # Verify signature
        expected_sig = hmac.new(
            settings.ADMIN_TOKEN_SECRET.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            return None

        # Add padding back if necessary
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)

        # Verify expiration
        if int(time.time()) > payload.get("exp", 0):
            return None

        return payload
    except Exception:
        return None
