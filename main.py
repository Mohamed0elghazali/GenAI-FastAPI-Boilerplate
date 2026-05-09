"""
main.py
-------
FastAPI application entry point.
Registers all routers and wires lifecycle events for DB / client startup.
"""

import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from api.ask.routes import ask_router
from api.auth.routes import auth_router
from api.chat.routes import chat_router
from core.client import ClientFactory
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up", extra={"env": settings.app_env})
    await ClientFactory.startup()
    yield
    logger.info("Application shutting down")
    await ClientFactory.shutdown()


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(ask_router,  prefix="/api/v1")


# ── Middleware ────────────────────────────────────────────────────────────────

@app.middleware("http")
async def request_id_and_timer(request: Request, call_next):
    request_id = str(uuid4())
    start = time.time()
    request.state.request_id = request_id

    response: Response = await call_next(request)

    process_time = round(time.time() - start, 5)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)

    logger.info(
        "Request handled",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_s": process_time,
        },
    )
    return response


# ── Base routes ───────────────────────────────────────────────────────────────

@app.get("/", tags=["Meta"])
def home():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health", tags=["Meta"])
def health():
    return {"status": "healthy", "env": settings.app_env}


@app.get("/metrics", tags=["Meta"])
def metrics():
    return {"uptime": "OK", "requests": "N/A"}


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
    )
