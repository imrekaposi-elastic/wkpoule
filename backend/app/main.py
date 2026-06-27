import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — register all models with SQLAlchemy mapper
from app.config import get_settings
from app.database import Base, engine
from app.db_schema import ensure_admin_access, ensure_schema
from app.logging_config import configure_logging
from app.routers import admin, auth, matches, predictions, rankings, subgroups, teams, venues
from app.cache.helpers import reset_main_event_loop, set_main_event_loop
from app.cache.redis_client import close_redis, init_redis, redis_ping
from app.cache.service import reset_cache_service
from app.services.prediction_milestones import backfill_milestones_for_existing_users
from app.services.score_poller import start_polling, stop_polling
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# DB client spans → Elastic service map edge from wkpoule-api to postgresql (requires opentelemetry-instrument).
SQLAlchemyInstrumentor().instrument(engine=engine)
# Outbound httpx spans → weatherapi + football-data.org dependencies on wkpoule-api.
HTTPXClientInstrumentor().instrument()

configure_logging()
logger = logging.getLogger("wkpoule.api")


def _cors_allow_origins() -> list[str]:
    s = get_settings()
    if s.cors_origins.strip():
        return [x.strip() for x in s.cors_origins.split(",") if x.strip()]
    origins = ["http://localhost:5173", "http://localhost:3000"]
    for url in (s.public_app_url, s.public_api_url):
        pub = url.rstrip("/")
        if pub and pub not in origins:
            origins.append(pub)
    return origins


def _openapi_servers() -> list[dict[str, str]]:
    s = get_settings()
    servers: list[dict[str, str]] = []
    api_url = s.public_api_url.rstrip("/")
    if api_url:
        servers.append({"url": api_url, "description": "Public API"})
    if api_url != "http://localhost:8000":
        servers.append({"url": "http://localhost:8000", "description": "Local development"})
    return servers


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_main_event_loop(asyncio.get_running_loop())
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    backfill_milestones_for_existing_users()
    ensure_admin_access()
    await init_redis()
    start_polling()
    yield
    stop_polling()
    await close_redis()
    reset_cache_service()
    reset_main_event_loop()


app = FastAPI(
    title="WK Poule API",
    version="2.7.0",
    description=(
        "World Cup 2026 prediction game API. "
        "Authenticate with `POST /api/auth/login`, then send `Authorization: Bearer <access_token>` "
        "on protected routes. See `/docs` for the interactive reference or read `docs/AGENTS.md` "
        "in the repository for agent-oriented workflows (login, resolve matches, post predictions)."
    ),
    lifespan=lifespan,
    servers=_openapi_servers(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_ns = time.perf_counter_ns()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ns = time.perf_counter_ns() - start_ns
        status_code = response.status_code if response else 500
        client_ip = request.client.host if request.client else None
        logger.info(
            "http request completed",
            extra={
                "event.action": "http_request",
                "event.category": "web",
                "event.duration": duration_ns,
                "http.request.method": request.method,
                "http.response.status_code": status_code,
                "url.path": request.url.path,
                "url.query": request.url.query,
                "user_agent.original": request.headers.get("user-agent"),
                "client.ip": client_ip,
                "source.ip": client_ip,
            },
        )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(rankings.router, prefix="/api", tags=["rankings"])
app.include_router(subgroups.router, prefix="/api/subgroups", tags=["subgroups"])
app.include_router(venues.router, prefix="/api", tags=["venues"])
app.include_router(teams.router, prefix="/api", tags=["teams"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "WK Poule API",
        "version": "2.7.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/health",
        "agent_guide": "https://github.com/imrekaposi-elastic/wkpoule/blob/main/docs/AGENTS.md",
    }


@app.get("/api/health", tags=["health"])
async def health_check():
    """Liveness/readiness probe. No authentication required."""
    redis_ok = await redis_ping()
    return {"status": "ok", "redis": "ok" if redis_ok else "unavailable"}
