"""
core/utils.py
-------------
Shared helper functions used across the project.
Keep this file focused on pure, stateless utilities.
Anything that needs config/clients belongs in its own module.
"""

from __future__ import annotations

import hashlib
import re
import time
import uuid
from typing import Any
from functools import wraps

# ── Identity helpers ──────────────────────────────────────────────────────────

def generate_id() -> str:
    """Return a new UUID4 string."""
    return str(uuid.uuid4())


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """Return a hex digest of *value* using the given algorithm."""
    h = hashlib.new(algorithm)
    h.update(value.encode())
    return h.hexdigest()


# ── String helpers ────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert *text* to a URL-safe lowercase slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate *text* to *max_length* characters, appending *suffix* if cut."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def strip_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into a single space."""
    return re.sub(r"\s+", " ", text).strip()


# ── Dict / data helpers ───────────────────────────────────────────────────────

def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten a nested dict into a single-level dict with dotted keys.

    Example:
        {"a": {"b": 1}} → {"a.b": 1}
    """
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def remove_none_values(d: dict) -> dict:
    """Return a shallow copy of *d* with all None-valued keys removed."""
    return {k: v for k, v in d.items() if v is not None}


# ── Timing helpers ────────────────────────────────────────────────────────────

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'[INFO] Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result
    return timeit_wrapper

# ── Token / text estimation ───────────────────────────────────────────────────

def estimate_tokens(text: str, chars_per_token: int = 4) -> int:
    """
    Rough token count estimate (1 token ≈ 4 characters for English text).
    Use a proper tokenizer for accurate counts.
    """
    return max(1, len(text) // chars_per_token)

