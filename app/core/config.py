"""
Central Application Configuration Module
Uses Pydantic Settings to load and validate environment variables with safe defaults.
"""

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of the Project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # --- Application Metadata ---
    APP_NAME: str = "Multilingual AI Document Assistant"
    APP_ENV: Literal["development", "testing", "production"] = "development"
    APP_DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- Relational Application Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # --- Vector Store & Embeddings (Phase 4) ---
    VECTOR_STORE_TYPE: Literal["chroma", "faiss"] = "chroma"
    VECTOR_STORE_PROVIDER: str = "chroma"
    VECTOR_STORE_PATH: str = "./data/vector_store"
    VECTOR_STORE_PERSIST_DIRECTORY: str = "data/vector_store"
    VECTOR_COLLECTION_NAME: str = "document_chunks"
    VECTOR_STORE_COLLECTION_NAME: str = "document_chunks"
    VECTOR_STORE_DISTANCE_METRIC: str = "cosine"
    VECTOR_INDEX_VERSION: int = 1

    EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 8
    EMBEDDING_NORMALIZE: bool = True
    EMBEDDING_MAX_LENGTH: int = 512
    EMBEDDING_MODEL_CACHE_DIR: str | None = None

    SIMILARITY_THRESHOLD: float = 0.65
    TOP_K_CHUNKS: int = 5

    # --- Retrieval Engine (Phase 5 & 6) ---
    RETRIEVAL_TOP_K: int = 8
    RETRIEVAL_DENSE_TOP_K: int = 12
    RETRIEVAL_LEXICAL_TOP_K: int = 12
    RETRIEVAL_FINAL_TOP_K: int = 5
    RETRIEVAL_MIN_SCORE: float = 0.0
    RETRIEVAL_ENABLE_LEXICAL: bool = True
    RETRIEVAL_ENABLE_RERANKING: bool = True
    RETRIEVAL_RERANKER_TYPE: Literal["heuristic", "none"] = "heuristic"
    RETRIEVAL_DENSE_WEIGHT: float = 0.70
    RETRIEVAL_LEXICAL_WEIGHT: float = 0.30
    RETRIEVAL_MAX_CONTEXT_CHUNKS: int = 5
    RETRIEVAL_MAX_CONTEXT_CHARACTERS: int = 6000

    # --- Multilingual & Query Expansion Settings (Phase 6) ---
    RETRIEVAL_ENABLE_QUERY_EXPANSION: bool = True
    RETRIEVAL_MAX_QUERY_VARIANTS: int = 4
    RETRIEVAL_MAX_EXPANSION_TERMS: int = 8
    RETRIEVAL_ENABLE_TRANSLITERATION: bool = True
    RETRIEVAL_VARIANT_WEIGHT: float = 0.85

    # --- Grounded RAG & Evidence Gating (Phase 5) ---
    RAG_MIN_EVIDENCE_SCORE: float = 0.35
    RAG_MIN_EVIDENCE_CHUNKS: int = 1
    RAG_REQUIRE_SOURCE_CITATIONS: bool = True
    RAG_ALLOW_PARTIAL_ANSWER: bool = False
    RAG_FALLBACK_MESSAGE: str = "Information Not Found in the provided documents."

    # --- LLM Generation Engine ---
    LLM_PROVIDER: Literal["gemini", "groq", "ollama", "mock"] = "gemini"
    LLM_PRIMARY_PROVIDER: Literal["gemini", "groq", "ollama", "mock"] = "gemini"
    LLM_FALLBACK_PROVIDER: Literal["gemini", "groq", "ollama", "mock"] = "ollama"
    LLM_MODEL_NAME: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 512
    LLM_TIMEOUT_SECONDS: int = 60

    # API Keys (Loaded from environment, never committed)
    GEMINI_API_KEY: str = Field(default="", repr=False)
    GROQ_API_KEY: str = Field(default="", repr=False)

    # Local Ollama Settings (Offline Mode)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL_NAME: str = "llama3.2:3b-instruct-q4_K_M"

    # --- Security & Authentication ---
    ADMIN_TOKEN_SECRET: str = Field(
        default="dev-insecure-secret-key-change-in-production-min32chars",
        repr=False
    )
    ADMIN_TOKEN_EXPIRY_MINUTES: int = 480
    ADMIN_DEFAULT_USERNAME: str = "admin"
    ADMIN_DEFAULT_PASSWORD: str = Field(default="admin_password_change_me", repr=False)

    # --- Logging & Telemetry (Phase 7) ---
    LOG_LEVEL: str = "INFO"
    TELEMETRY_ENABLED: bool = True
    TELEMETRY_DIRECTORY: str = "./data/telemetry"
    TELEMETRY_LOG_ROTATION_MB: int = 25

    # --- PySpark Big Data Engine (Phase 7) ---
    SPARK_MASTER: str = "local[*]"
    SPARK_APP_NAME: str = "InstitutionalDocAnalytics"
    SPARK_DRIVER_MEMORY: str = "2g"
    SPARK_SHUFFLE_PARTITIONS: int = 4

    @property
    def telemetry_path(self) -> Path:
        return PROJECT_ROOT / "data" / "telemetry"

    @property
    def telemetry_raw_path(self) -> Path:
        return self.telemetry_path / "raw"

    @property
    def telemetry_validated_path(self) -> Path:
        return self.telemetry_path / "validated"

    @property
    def telemetry_rejected_path(self) -> Path:
        return self.telemetry_path / "rejected"

    @property
    def telemetry_parquet_path(self) -> Path:
        return self.telemetry_path / "parquet"

    @property
    def telemetry_analytics_path(self) -> Path:
        return self.telemetry_path / "analytics"

    @property
    def absolute_db_path(self) -> Path:
        if self.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
            raw_path = self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
            if raw_path.startswith("./"):
                return (PROJECT_ROOT / raw_path[2:]).resolve()
            return Path(raw_path).resolve()
        return PROJECT_ROOT / "data" / "app.db"

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @property
    def DATA_DIRECTORY(self) -> Path:
        return PROJECT_ROOT / "data"


# Global Singleton Settings Instance
settings = Settings()

