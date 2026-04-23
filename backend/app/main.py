import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — register all models with SQLAlchemy mapper
from app.database import Base, engine
from app.db_schema import ensure_schema
from app.routers import admin, auth, matches, predictions, rankings, subgroups, venues
from app.services.score_poller import start_polling, stop_polling

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema()
    start_polling()
    yield
    stop_polling()


app = FastAPI(
    title="WK Poule",
    version="1.0.0",
    description="World Cup 2026 Prediction Site",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(rankings.router, prefix="/api", tags=["rankings"])
app.include_router(subgroups.router, prefix="/api/subgroups", tags=["subgroups"])
app.include_router(venues.router, prefix="/api", tags=["venues"])


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
