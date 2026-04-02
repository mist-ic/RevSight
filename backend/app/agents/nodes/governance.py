"""Governance node -- audit logging and HITL approval gate."""
from __future__ import annotations

import uuid
import json
import logging
from datetime import datetime, timezone

from app.agents.schemas.report import PipelineHealthReport
from app.agents.schemas.request import ReportRequest
from app.db.connection import execute_write
from app.config import REQUIRE_APPROVAL

logger = logging.getLogger(__name__)


async def run_governance(
    run_id: str,
    request: ReportRequest,
    report: PipelineHealthReport,
) -> dict:
    """
    Governance node: logs the proposed report to audit_actions and
    auto-approves in demo mode. Returns approval_status.
    """
    action_id = str(uuid.uuid4())

    try:
        await execute_write(
            """
            INSERT INTO audit_actions (id, run_id, action_type, payload, status, reviewed_by, reviewed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            action_id,
            run_id,
            "report_approval",
            json.dumps(report.model_dump()),
            "approved" if not REQUIRE_APPROVAL else "pending",
            "system" if not REQUIRE_APPROVAL else None,
            datetime.now(timezone.utc) if not REQUIRE_APPROVAL else None,
        )
    except Exception as e:
        logger.warning(f"Audit log failed (non-fatal): {e}")

    if REQUIRE_APPROVAL:
        # In production: would pause via interrupt() and wait for human input
        logger.info(f"Report {run_id} pending human approval")
        return {"approval_status": "pending", "action_id": action_id}

    logger.info(f"Report {run_id} auto-approved (demo mode)")
    return {"approval_status": "approved", "action_id": action_id}
