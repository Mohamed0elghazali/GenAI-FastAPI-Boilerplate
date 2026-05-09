"""
core/config.py
--------------
Loads environment variables from .env and exposes them as a typed
Settings class using pydantic-settings.

Usage:
    from core.config import settings
    print(settings.bedrock_api_key)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "GenAI Backend"
    app_env: str = "development"          # development | staging | production
    debug: bool = False
    log_level: str = "INFO"

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # ── LLM / AI providers ───────────────────────────────────────────────
    default_llm_provider: str = "bedrock"  # bedrock | openai | anthropic | auto

    # Shared model params
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048

    # AWS Bedrock — auth via boto3 credential chain (env vars or IAM role)
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_api_key: str = ""
    bedrock_model_id: str = "amazon.nova-lite-v1:0"

    # OpenAI
    openai_api_key: str = ""
    openai_model_id: str = "gpt-4o-mini"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model_id: str = "claude-3-5-haiku-20241022"

    # ── Auth ─────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Vector store ─────────────────────────────────────────────────────
    vector_store_url: str = ""
    vector_store_collection: str = "default"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — always use this instead of instantiating directly."""
    return Settings()


# Convenience singleton imported everywhere
settings: Settings = get_settings()
