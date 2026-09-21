"""
Unit tests for configuration and settings
"""

from app.core.config import settings

def test_settings_defaults():
    assert settings.APP_NAME == "Multilingual AI Document Assistant"
    assert settings.DATABASE_URL.startswith("sqlite+aiosqlite:///")
    assert settings.VECTOR_STORE_TYPE == "chroma"
    assert settings.EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-small"
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.LLM_PRIMARY_PROVIDER in ("gemini", "groq", "ollama")
    assert settings.ADMIN_TOKEN_EXPIRY_MINUTES == 480
