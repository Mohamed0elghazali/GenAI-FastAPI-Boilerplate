"""
agent/callbacks/handler.py
--------------------------
LangChain-compatible callback handler for tracking LLM usage:
token counts, latency, errors, and custom events.

If you are not using LangChain, the BaseCallbackHandler base class can be
swapped for a plain class — the interface stays the same.

Usage:
    from agent.callbacks.handler import UsageCallbackHandler

    handler = UsageCallbackHandler()
    llm.invoke(prompt, config={"callbacks": [handler]})
    print(handler.summary())
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from core.logger import get_logger

logger = get_logger(__name__)

# Try to import LangChain base; fall back to a plain stub so the project
# works even without LangChain installed.
try:
    from langchain_core.callbacks.base import BaseCallbackHandler as _LCBase  # type: ignore
    _BASE = _LCBase
except ImportError:
    class _BASE:  # type: ignore
        """Minimal stub when langchain_core is not installed."""


class UsageCallbackHandler(_BASE):
    """
    Tracks per-run LLM usage metrics and logs them as structured JSON.

    Attributes:
        total_prompt_tokens:      cumulative prompt tokens across all runs.
        total_completion_tokens:  cumulative completion tokens across all runs.
        total_llm_calls:          number of LLM calls made.
        total_errors:             number of errors encountered.
        total_latency_ms:         cumulative wall-clock time in milliseconds.
    """

    def __init__(self) -> None:
        super().__init__()
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_llm_calls: int = 0
        self.total_errors: int = 0
        self.total_latency_ms: float = 0.0
        self._run_start: dict[str, float] = {}  # run_id → start time

    # ── LangChain callback hooks ──────────────────────────────────────────

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._run_start[str(run_id)] = time.perf_counter()
        logger.debug(
            "LLM call started",
            extra={
                "run_id": str(run_id),
                "model": serialized.get("name", "unknown"),
                "num_prompts": len(prompts),
            },
        )

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        latency = self._finish_run(run_id)
        self.total_llm_calls += 1

        # Extract token usage when available (LangChain LLMResult)
        prompt_tokens = 0
        completion_tokens = 0
        try:
            usage = response.llm_output.get("usage", {}) if response.llm_output else {}
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        except AttributeError:
            pass

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        logger.info(
            "LLM call completed",
            extra={
                "run_id": str(run_id),
                "latency_ms": round(latency, 2),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        latency = self._finish_run(run_id)
        self.total_errors += 1
        logger.error(
            "LLM call failed",
            extra={
                "run_id": str(run_id),
                "latency_ms": round(latency, 2),
                "error": str(error),
            },
        )

    def on_chain_start(self, serialized: dict, inputs: dict, *, run_id: UUID, **kwargs: Any) -> None:
        self._run_start[str(run_id)] = time.perf_counter()

    def on_chain_end(self, outputs: dict, *, run_id: UUID, **kwargs: Any) -> None:
        self._finish_run(run_id)

    def on_chain_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        self._finish_run(run_id)
        self.total_errors += 1

    # ── Helpers ───────────────────────────────────────────────────────────

    def _finish_run(self, run_id: UUID) -> float:
        """Pop the start time for *run_id* and return elapsed ms."""
        start = self._run_start.pop(str(run_id), time.perf_counter())
        latency_ms = (time.perf_counter() - start) * 1000
        self.total_latency_ms += latency_ms
        return latency_ms

    def summary(self) -> dict[str, Any]:
        """Return a dict snapshot of all accumulated metrics."""
        return {
            "total_llm_calls": self.total_llm_calls,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_errors": self.total_errors,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "avg_latency_ms": round(
                self.total_latency_ms / self.total_llm_calls, 2
            ) if self.total_llm_calls else 0.0,
        }

    def reset(self) -> None:
        """Reset all counters (useful between requests in tests)."""
        self.__init__()
