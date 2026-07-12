"""
DSRA V2 — Application Settings
================================
Single source of truth for all configuration.
Loaded from environment variables via Pydantic BaseSettings.
All secrets come from environment — never from code.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Design decisions:
    - Pydantic BaseSettings gives us type validation + .env file support
    - lru_cache() ensures we create this once (singleton pattern)
    - All secrets are Optional strings that raise at startup if missing in production
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_version: str = "2.0.0"
    app_secret_key: str = Field(..., min_length=32)

    # ── API Server ───────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_workers: int = Field(default=1, ge=1)
    api_reload: bool = False

    # ── Database ─────────────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "dsra_v2"
    postgres_user: str = "dsra_user"
    postgres_password: str = Field(..., min_length=8)
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=200)

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection URL."""
        url = (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.app_env == "production" or "neon.tech" in self.postgres_host:
            url += "?ssl=require"
        return url

    @property
    def sync_database_url(self) -> str:
        """Sync PostgreSQL URL for Alembic migrations."""
        url = (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.app_env == "production" or "neon.tech" in self.postgres_host:
            url += "?sslmode=require"
        return url

    # ── LLM ──────────────────────────────────────────────────────────
    gemini_api_key: str = Field(..., min_length=20)
    gemini_default_model: str = Field(...)
    gemini_fallback_model: str = Field(...)
    gemini_max_retries: int = Field(default=3, ge=1, le=10)
    gemini_request_timeout: int = Field(default=120, ge=10, le=600)

    # ── Source APIs ───────────────────────────────────────────────────
    google_cse_api_key: str | None = None
    google_cse_cx: str | None = None
    pubmed_api_key: str | None = None



    # ── JWT ───────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=60, ge=5)
    jwt_refresh_token_expire_days: int = Field(default=30, ge=1)



    # ── Export ────────────────────────────────────────────────────────
    export_base_dir: str = "./data/exports"
    export_max_file_age_days: int = Field(default=30, ge=1)

    # ── Research Defaults ─────────────────────────────────────────────
    default_max_iterations: int = Field(default=3, ge=1, le=10)
    default_max_revisions: int = Field(default=2, ge=1, le=5)
    default_research_depth: int = Field(default=2, ge=1, le=3)
    default_max_sources_per_query: int = Field(default=10, ge=1, le=50)
    evidence_dedup_threshold: float = Field(default=0.92, ge=0.5, le=1.0)
    critique_approval_threshold: float = Field(default=7.0, ge=0.0, le=10.0)
    gap_coverage_threshold: float = Field(default=0.6, ge=0.0, le=1.0)

    # ── Logging ───────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # ── CORS ──────────────────────────────────────────────────────────
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="cors_origins"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parses the comma-separated string into a list for FastAPI."""
        # If it's formatted like a JSON array, try to clean it
        raw = self.cors_origins_str
        if raw.startswith("[") and raw.endswith("]"):
            import json
            try:
                return json.loads(raw.replace("'", '"'))
            except Exception:
                pass
        return [i.strip() for i in raw.strip("[]'\"").split(",") if i.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Enforce stricter rules in production."""
        if self.app_env == "production":
            if self.app_debug:
                raise ValueError("DEBUG must be False in production.")
            if self.api_reload:
                raise ValueError("API reload must be False in production.")
            if "change-this" in self.app_secret_key:
                raise ValueError("Set a real secret key in production.")
            if "change-this" in self.jwt_secret_key:
                raise ValueError("Set a real JWT secret key in production.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the singleton Settings instance.
    Uses lru_cache to ensure the Settings object is created only once,
    even in async contexts with concurrent requests.
    """
    return Settings()  # type: ignore[call-arg]
