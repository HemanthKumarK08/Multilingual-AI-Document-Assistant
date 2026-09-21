"""
Unit tests for PBKDF2 password hashing and HMAC-SHA256 tokens
"""

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)

def test_password_hashing():
    raw_pwd = "SuperSecretPassword123"
    hashed = hash_password(raw_pwd)

    assert ":" in hashed
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_access_token_creation_and_verification():
    username = "test_admin"
    token = create_access_token(subject=username, role="admin", expires_minutes=60)

    assert "." in token
    payload = verify_access_token(token)

    assert payload is not None
    assert payload["sub"] == username
    assert payload["role"] == "admin"

def test_tampered_token_rejected():
    token = create_access_token(subject="admin", role="admin")
    parts = token.split(".")
    tampered_token = f"{parts[0]}xyz.{parts[1]}"

    assert verify_access_token(tampered_token) is None
