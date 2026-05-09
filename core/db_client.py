"""
core/db_client.py
-----------------
Async database client wrapper.
Replace the stub body with your ORM of choice (SQLAlchemy, Tortoise, etc.)

Usage:
    from core.db_client import DatabaseClient

    db = DatabaseClient()
    await db.connect()
    session = db.engine   # or db.session_factory, depending on your ORM
    await db.disconnect()
"""

from __future__ import annotations

from typing import Any, Optional

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class DatabaseClient:
    """
    Thin wrapper around the async DB engine / session factory.

    Lifecycle:
        - Call connect() once at app startup (wired via ClientFactory.startup).
        - Call disconnect() once at app shutdown (wired via ClientFactory.shutdown).
        - Access the engine / session factory via the .engine property.

    SQLAlchemy example (uncomment to use):
        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        async def connect(self) -> None:
            self._engine = create_async_engine(
                self._url,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                echo=settings.debug,
            )
            self._session_factory = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )

        async def disconnect(self) -> None:
            await self._engine.dispose()
    """

    def __init__(self) -> None:
        self._url = settings.database_url
        self._engine: Any = None
        self._session_factory: Any = None
        logger.info("DatabaseClient initialised", extra={"url": self._masked_url()})

    # ── Helpers ───────────────────────────────────────────────────────────

    def _masked_url(self) -> str:
        """Return the DB URL with the password replaced by ***."""
        if "://" in self._url and "@" in self._url:
            prefix, rest = self._url.split("@", 1)
            scheme_user, _ = prefix.rsplit(":", 1)
            return f"{scheme_user}:***@{rest}"
        return self._url or "(not set)"

    # ── Lifecycle ─────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Open the connection pool. Called once at app startup."""
        # TODO: replace with real engine creation (see docstring above)
        logger.info("Database connection pool opened")

    async def disconnect(self) -> None:
        """Close the connection pool. Called once at app shutdown."""
        # TODO: await self._engine.dispose()
        logger.info("Database connection pool closed")

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def engine(self) -> Any:
        """The raw async engine. Raises if connect() has not been called."""
        if self._engine is None:
            raise RuntimeError(
                "DatabaseClient is not connected. Call connect() first."
            )
        return self._engine

    @property
    def session_factory(self) -> Any:
        """The async session factory. Raises if connect() has not been called."""
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseClient is not connected. Call connect() first."
            )
        return self._session_factory
