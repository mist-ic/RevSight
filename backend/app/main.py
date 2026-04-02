from __future__ import annotations

import os
from contextlib import asynccontextmanager
import logfire
import logging

import fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL, LOGFIRE_TOKEN, LANGCHAIN_TRACING_V2
from app.api.routes import reports, metrics, runs, stream
from app.db.connection import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure Logfire
    if LOGFIRE_TOKEN:
        logfire.configure(token=LOGFIRE_TOKEN)
        logfire.instrument_fastapi(app)
    else:
        logfire.configure(send_to_logfire=False)

    # Configure LangSmith
    if LANGCHAIN_TRACING_V2 == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

    # Init DB connection pool
    await init_db()
    logger.info("RevSight backend started")
    yield
    logger.info("RevSight backend shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="RevSight API",
        description="Revenue Command Copilot -- AI-powered pipeline health analysis",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
    app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
    app.include_router(stream.router, prefix="/api/reports", tags=["stream"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "revsight-backend"}

    return app


app = create_app()
