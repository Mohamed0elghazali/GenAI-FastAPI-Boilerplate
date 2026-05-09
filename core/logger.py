"""
core/logger.py
--------------
Structured JSON logger for the entire project.
Every module should use get_logger(__name__) instead of print() or
the stdlib logging.getLogger() directly.

Features:
- JSON output with consistent fields
- Filters out noisy third-party loggers
- Injects app_env and service name into every record
- Log level controlled via settings.log_level

Usage:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("user request received", extra={"user_id": "123"})
"""

import logging
import json
import traceback
from datetime import datetime, timezone
from typing import Optional

from core.config import settings


# ── Noisy loggers to silence ─────────────────────────────────────────────────
_SUPPRESSED_LOGGERS = [
    "httpx",
    "httpcore",
    "uvicorn.access",
    "botocore",
    "boto3",
    "urllib3",
    "openai._base_client",
]


class _JSONFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.app_name,
            "env": settings.app_env,
        }

        # Include any extra fields passed via extra={}
        _standard_keys = logging.LogRecord.__dict__.keys() | {
            "message", "asctime", "args", "exc_info", "exc_text", "stack_info"
        }
        for key, value in record.__dict__.items():
            if key not in _standard_keys and not key.startswith("_"):
                payload[key] = value

        # Attach exception info if present
        if record.exc_info:
            payload["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(payload, default=str)


class _SuppressFilter(logging.Filter):
    """Drops records from loggers listed in _SUPPRESSED_LOGGERS."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not any(record.name.startswith(name) for name in _SUPPRESSED_LOGGERS)


def _configure_root_logger() -> None:
    """One-time root logger setup called on module import."""
    root = logging.getLogger()
    if root.handlers:
        return  # already configured

    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    handler.addFilter(_SuppressFilter())

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root.setLevel(level)
    root.addHandler(handler)

    # Silence suppressed loggers explicitly
    for name in _SUPPRESSED_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


_configure_root_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger that inherits the root JSON handler.

    Args:
        name: typically __name__ of the calling module.

    Returns:
        logging.Logger instance.
    """
    return logging.getLogger(name or settings.app_name)
