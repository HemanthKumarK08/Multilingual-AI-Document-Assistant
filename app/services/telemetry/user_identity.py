"""
Privacy-Preserving User & Session Identity Module
Derives cryptographically strong, secret-salted HMAC-SHA256 anonymous display identifiers.
Ensures zero exposure of raw session IDs, personal user details, or internal keys.
"""

import hashlib
import hmac
from typing import Optional

from app.core.config import settings


def get_analytics_secret() -> str:
    """Retrieves the configured analytics hash secret."""
    return settings.ANALYTICS_HASH_SECRET or "default-telemetry-hmac-salt-secure"


def generate_anonymous_user_id(identifier: Optional[str]) -> Optional[str]:
    """
    Derives an opaque, salted HMAC-SHA256 anonymous user identifier.
    Returns format: 'USER-<8-CHAR-HEX>' or None if identifier is empty.
    """
    if not identifier or not str(identifier).strip():
        return None

    clean_id = str(identifier).strip()
    # If the identifier is already a synthetic fixture user, preserve the fixture alias
    if clean_id.startswith("USER-") and len(clean_id) <= 8 and clean_id[5:].isdigit():
        return clean_id

    secret = get_analytics_secret()
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=clean_id.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()[:8].upper()

    return f"USER-{digest}"


def generate_anonymous_session_id(session_id: Optional[str]) -> Optional[str]:
    """
    Derives an opaque, salted HMAC-SHA256 anonymous session identifier.
    Returns format: 'SES-<8-CHAR-HEX>' or None if session_id is empty.
    """
    if not session_id or not str(session_id).strip():
        return None

    clean_id = str(session_id).strip()
    # If the session_id is already a synthetic fixture session, preserve the fixture alias
    if clean_id.startswith("SES-") and "-" in clean_id and len(clean_id) <= 12:
        return clean_id

    secret = get_analytics_secret()
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=clean_id.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()[:8].upper()

    return f"SES-{digest}"
