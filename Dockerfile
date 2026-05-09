# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Keeps Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Tell uv to use the system Python and not create a venv inside the container
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /app


# ── Dependencies layer ────────────────────────────────────────────────────────
# Copy only dependency files first so Docker can cache this layer independently
# from your source code. Re-runs only when pyproject.toml or uv.lock changes.
FROM base AS deps

COPY pyproject.toml uv.lock* ./

# Install core dependencies (no optional extras)
# Use --frozen to ensure uv.lock is respected exactly
RUN uv sync --frozen --no-install-project --no-dev


# ── Production image ──────────────────────────────────────────────────────────
FROM base AS production

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# ── Development image ─────────────────────────────────────────────────────────
FROM base AS development

COPY pyproject.toml uv.lock* ./

# Install all deps including dev extras
RUN uv sync --frozen --no-install-project --extra dev

COPY . .

EXPOSE 8000

# Reload enabled for local development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
