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
    pub = s.public_app_url.rstrip("/")
    if pub and pub not in origins:
        origins.append(pub)
    return origins


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
    title="Worldcup 2026 game",
    version="2.4.1",
    description="World Cup 2026 prediction game",
    lifespan=lifespan,
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


@app.get("/api/health")
async def health_check():
    redis_ok = await redis_ping()
    return {"status": "ok", "redis": "ok" if redis_ok else "unavailable"}
