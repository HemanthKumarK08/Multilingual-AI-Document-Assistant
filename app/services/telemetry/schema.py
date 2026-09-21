"""
Telemetry Schema and Contract Constants (Phase 7)
Defines versioned telemetry metadata, allowed domains, and strict privacy boundary rules.
"""

from typing import Set

SCHEMA_VERSION: str = "1.0"

SUPPORTED_EVENT_TYPES: Set[str] = {
    "query_completed",
    "retrieval_completed",
    "rag_response",
    "error",
}

SUPPORTED_LANGUAGES: Set[str] = {
    "en",
    "hi",
    "kn",
    "te",
    "mixed",
    "unknown",
}

SUPPORTED_SCRIPTS: Set[str] = {
    "latin",
    "devanagari",
    "kannada",
    "telugu",
    "mixed",
    "unknown",
}

SUPPORTED_PROVIDERS: Set[str] = {
    "gemini",
    "ollama",
    "mock",
    "unknown",
}

# Forbidden keys that must NEVER be present in any telemetry payload
FORBIDDEN_FIELD_NAMES: Set[str] = {
    "query",
    "raw_query",
    "query_text",
    "user_query",
    "normalized_query",
    "prompt",
    "raw_prompt",
    "system_prompt",
    "answer",
    "answer_text",
    "generated_answer",
    "response_text",
    "generated_variants",
    "variants_text",
    "passage",
    "passages",
    "content",
    "text_content",
    "document_text",
    "chunk_text",
    "email",
    "phone",
    "token",
    "api_key",
    "password",
    "secret",
    "authorization",
    "cookie",
}

# Prohibited substring patterns in string values
PROHIBITED_VALUE_PATTERNS = [
    r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",  # Email pattern
    r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b",                      # Standalone Indian phone pattern
    r"\bAIza[0-9A-Za-z-_]{35}\b",                            # Google API Key pattern
    r"\bBearer\s+[A-Za-z0-9\-\._~\+\/]+=*\b",               # Bearer Token pattern
]
