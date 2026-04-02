"""Run/step audit logging helpers."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from app.db.connection import execute_write

logger = logging.getLogger(__name__)


async def create_run(run_id: str, request: dict) -> None:
    try:
        await execute_write(
            """
            INSERT INTO runs (id, persona, quarter, region, segment, scenario_id, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'running')
            """,
            run_id,
            request.get("persona"),
            request.get("quarter"),
            request.get("region"),
            request.get("segment"),
            request.get("scenario_id"),
        )
    except Exception as e:
        logger.warning(f"Failed to create run record: {e}")


async def complete_run(run_id: str, report_json: dict) -> None:
    try:
        await execute_write(
            """
            UPDATE runs
            SET status = 'done', report_json = $2, completed_at = $3
            WHERE id = $1
            """,
            run_id,
            json.dumps(report_json),
            datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.warning(f"Failed to complete run record: {e}")


async def fail_run(run_id: str, error: str) -> None:
    try:
        await execute_write(
            "UPDATE runs SET status = 'failed', completed_at = $2 WHERE id = $1",
            run_id,
            datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.warning(f"Failed to mark run as failed: {e}")


async def log_agent_step(
    run_id: str,
    agent_name: str,
    duration_ms: int,
    input_hash: str = "",
    output_hash: str = "",
) -> None:
    try:
        await execute_write(
            """
            INSERT INTO agent_steps (id, run_id, agent_name, input_hash, output_hash, duration_ms)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            str(uuid.uuid4()),
            run_id,
            agent_name,
            input_hash,
            output_hash,
            duration_ms,
        )
    except Exception as e:
        logger.warning(f"Failed to log agent step: {e}")
