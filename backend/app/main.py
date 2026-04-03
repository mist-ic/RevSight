from __future__ import annotations

import os
from contextlib import asynccontextmanager
import logfire
import logging

import fastapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL, LOGFIRE_TOKEN, LANGCHAIN_TRACING_V2
from app.api.routes import reports, metrics, runs, stream, a2a, imports
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
        description=(
            "Revenue Command Copilot -- AI-powered pipeline health analysis. "
            "Built on LangGraph + Pydantic AI. "
            "MCP server available at /mcp (streamable-http). "
            "A2A Agent Card at /.well-known/agent.json."
        ),
        version="0.4.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL, "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Existing routes
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
    app.include_router(runs.router,    prefix="/api/runs",    tags=["runs"])
    app.include_router(stream.router,  prefix="/api/reports", tags=["stream"])

    # Phase 4: A2A + Import
    app.include_router(a2a.router)
    app.include_router(imports.router, prefix="/api/import",  tags=["import"])

    # Phase 4: MCP server mounted at /mcp
    try:
        from app.mcp_server import mcp
        app.mount("/mcp", mcp.streamable_http_app())
        logger.info("MCP server mounted at /mcp")
    except Exception as exc:
        logger.warning(f"MCP server not mounted: {exc}")

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "revsight-backend",
            "version": "0.4.0",
            "features": ["mcp", "a2a", "csv-import", "sse-streaming"],
        }

    return app


app = create_app()
