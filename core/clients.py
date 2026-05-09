"""
core/client.py
--------------
Central factory for all external connections: database and LLM clients.
Everything in the project should obtain connections through ClientFactory
rather than instantiating clients directly.

Usage:
    from core.client import ClientFactory

    llm = ClientFactory.get_llm()
    db  = ClientFactory.get_db()
    await ClientFactory.startup()   # call from FastAPI lifespan
    await ClientFactory.shutdown()  # call from FastAPI lifespan
"""

from __future__ import annotations

from typing import Any, Optional

from core.config import settings
from core.db_client import DatabaseClient
from core.llm_factory import LLMFactory
from core.logger import get_logger

logger = get_logger(__name__)


class ClientFactory:
    """
    Single entry point for all external clients.

    Clients are created lazily and cached as class-level singletons so the
    same instance is reused across the application lifetime.
    """

    _db: Optional[DatabaseClient] = None
    _llm: Optional[Any] = None

    # ── LLM ──────────────────────────────────────────────────────────────

    @classmethod
    def get_llm(
        cls,
        provider: str | None = None,
        model_id: str | None = None,
    ) -> Any:
        """
        Return a cached LangChain BaseChatModel.

        Defaults are read from settings (default_llm_provider, bedrock_model_id,
        openai_model_id, anthropic_model_id). Pass explicit args only when you
        need to override the configured defaults — doing so always creates a
        fresh (uncached) client.

        Args:
            provider: override settings.default_llm_provider.
            model_id: override the provider's default model ID from settings.

        Returns:
            BaseChatModel instance (supports .invoke / .ainvoke / .stream).
        """
        resolved_provider = provider or settings.default_llm_provider
        override = provider is not None or model_id is not None

        if cls._llm is None or override:
            cls._llm = LLMFactory.create(
                provider=resolved_provider,
                model_id=model_id,
            )
            logger.debug(
                "LLM client created",
                extra={"provider": resolved_provider, "model_id": model_id},
            )
        return cls._llm

    # ── Database ─────────────────────────────────────────────────────────

    @classmethod
    def get_db(cls) -> DatabaseClient:
        """
        Return the cached DatabaseClient instance.

        The client is configured from settings (database_url, db_pool_size,
        db_max_overflow, debug). connect() is called automatically during
        startup().
        """
        if cls._db is None:
            cls._db = DatabaseClient()
            logger.debug(
                "DB client created",
                extra={"url": settings.database_url},
            )
        return cls._db

    # ── Lifecycle (wire into FastAPI lifespan) ────────────────────────────

    @classmethod
    async def startup(cls) -> None:
        """Open all connections. Call from FastAPI lifespan startup."""
        logger.info("ClientFactory startup — opening connections")
        await cls.get_db().connect()

    @classmethod
    async def shutdown(cls) -> None:
        """Close all connections. Call from FastAPI lifespan shutdown."""
        logger.info("ClientFactory shutdown — closing connections")
        if cls._db:
            await cls._db.disconnect()
