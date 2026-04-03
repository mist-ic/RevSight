"""
A2A Agent Card and task endpoint.

Published at:
  GET  /.well-known/agent.json   -- Agent Card (A2A v0.3.0 spec)
  POST /a2a                      -- Task submission endpoint

The Agent Card describes RevSight as an A2A-compatible agent that can:
  - analyze-pipeline:   Analyze a sales pipeline for a given scenario
  - generate-report:    Generate a structured QBR-ready PipelineHealthReport
  - assess-risk:        Identify and classify pipeline risks

In demo mode (no OAuth), the security field is left as an empty requirement,
meaning the endpoint is open. Production deployments should add OAuth2
clientCredentials flow.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["a2a"])


# --------------------------------------------------------------------------- #
# Agent Card (A2A v0.3.0)
# --------------------------------------------------------------------------- #

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "RevSight Revenue Copilot",
    "description": (
        "An AI-powered revenue operations agent that analyzes sales pipeline health, "
        "detects risks, and generates structured QBR-ready reports. "
        "All metrics are computed deterministically from SQL; the LLM only narrates. "
        "Built on LangGraph + Pydantic AI with a numeric consistency guardrail."
    ),
    "url": "https://revsight-backend-ski7hmysfa-el.a.run.app/a2a",
    "documentationUrl": "https://github.com/mist-ic/RevSight",
    "preferredTransport": "HTTP+JSON",
    "version": "1.0.0",
    "provider": {
        "organization": "mist-ic",
        "url": "https://github.com/mist-ic",
    },
    "capabilities": {
        "streaming": True,
        "pushNotifications": False,
        "stateTransitionHistory": True,
    },
    "securitySchemes": {
        "oauth2": {
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "https://revsight-backend-ski7hmysfa-el.a.run.app/auth/token",
                    "scopes": {
                        "pipeline.read":   "Read pipeline data and metrics",
                        "report.generate": "Trigger report generation",
                    },
                }
            },
        }
    },
    "security": [],  # open in demo mode; set [{"oauth2": ["pipeline.read", "report.generate"]}] in prod
    "defaultInputModes": ["application/json"],
    "defaultOutputModes": ["application/json", "text/event-stream"],
    "skills": [
        {
            "id": "analyze-pipeline",
            "name": "Analyze Pipeline",
            "description": (
                "Run a full 5-node LangGraph pipeline to analyze a sales pipeline for a "
                "given quarter, region, and segment. Returns a structured PipelineHealthReport."
            ),
            "tags": ["revenue-operations", "pipeline", "forecasting"],
            "examples": [
                "Analyze the NA Enterprise pipeline for Q3-2026",
                "What is the pipeline health for EMEA SMB this quarter?",
            ],
            "inputModes": ["application/json"],
            "outputModes": ["application/json", "text/event-stream"],
        },
        {
            "id": "generate-report",
            "name": "Generate QBR Report",
            "description": (
                "Generate a structured JSON report with executive summary, KPIs, risk assessment, "
                "and recommended actions. All numbers are SQL-computed and guardrail-validated."
            ),
            "tags": ["qbr", "reporting", "executive-summary"],
            "examples": [
                "Generate a QBR report for the APAC Enterprise Q3-2026 pipeline",
            ],
            "inputModes": ["application/json"],
            "outputModes": ["application/json"],
        },
        {
            "id": "assess-risk",
            "name": "Assess Pipeline Risk",
            "description": (
                "Identify coverage gaps, conversion drop-offs, deal aging, and data quality issues. "
                "Returns a list of classified risks with severity, narrative, and linked metric IDs."
            ),
            "tags": ["risk", "coverage", "deal-aging"],
            "examples": [
                "What are the risks in the EMEA pipeline?",
                "Flag any coverage or data quality issues in APAC Q3",
            ],
            "inputModes": ["application/json"],
            "outputModes": ["application/json"],
        },
    ],
}


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@router.get("/.well-known/agent.json", include_in_schema=False)
async def agent_card():
    """A2A Agent Card endpoint (v0.3.0 spec)."""
    return JSONResponse(content=AGENT_CARD)


@router.post("/a2a")
async def a2a_task(payload: dict):
    """
    A2A task submission endpoint.

    Accepts a task payload and returns a task acknowledgement.
    For actual report generation, clients should use POST /api/reports/stream
    which provides SSE streaming of the full agent pipeline.

    Expected payload:
      {
        "skill": "analyze-pipeline" | "generate-report" | "assess-risk",
        "input": {
          "scenario_id": "na_healthy" | "emea_undercovered" | "apac_dataquality",
          "quarter": "Q3-2026",
          "region": "NA" | "EMEA" | "APAC",
          "segment": "Enterprise" | "SMB",
          "persona": "cro" | "revops" | "engineer"
        }
      }
    """
    task_id = f"tsk_{uuid.uuid4().hex[:12]}"
    skill = payload.get("skill", "analyze-pipeline")
    input_data = payload.get("input", {})

    return {
        "taskId": task_id,
        "state": "submitted",
        "skill": skill,
        "message": (
            f"Task accepted. To stream the full agent pipeline, POST to "
            f"/api/reports/stream with the same input parameters. "
            f"Task ID: {task_id}"
        ),
        "links": {
            "stream": "/api/reports/stream",
            "status": f"/api/runs",
            "docs": "/docs",
        },
        "input_echo": input_data,
    }
