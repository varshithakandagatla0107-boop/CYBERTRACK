"""CYBERTRACK FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db
from app.routers import (
    accounts, alerts, analytics, audit, auth, clusters,
    dashboard, data, export, investigations, network,
    priorities, settings, transactions, trails,
)
from app.seed import seed_users


# Project root (works regardless of CWD)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_users()
    # Auto-load the demonstration case on first start
    # so the prototype is immediately demonstrable.
    from app.db.database import get_connection
    from app.engine.pipeline import load_dataset
    from app.demo import case as demo_case
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM datasets LIMIT 1"
    ).fetchone()
    if existing is None:
        try:
            df = demo_case.generate_demo_case()
            load_dataset(df,
                         name=demo_case.case_metadata()["name"],
                         source="demo")
        except Exception:
            pass
    yield


app = FastAPI(
    title="CYBERTRACK — PS-35 Mule Account Tracing",
    description=(
        "Prototype: transaction data → hidden network → "
        "money trail → explainable risk → investigation "
        "priority. Synthetic demonstration data only."),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                    "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth, data, dashboard, accounts,
                transactions, network, trails, priorities,
                clusters, alerts, investigations, audit,
                analytics, export, settings):
    app.include_router(router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "cybertrack"}


# Serve the built frontend when present (production mode).
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(
        directory=str(FRONTEND_DIST), html=True),
        name="frontend")
else:
    import logging
    logging.warning(
        f"Frontend build not found at {FRONTEND_DIST}. "
        "Run 'npm run build' in frontend/ to enable static serving."
    )