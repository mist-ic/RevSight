"""LangGraph graph definition -- the main orchestration pipeline."""
from __future__ import annotations

import time
import json
import uuid
import logging
from hashlib import md5

from langgraph.graph import StateGraph, END

from app.agents.state import RevSightState
from app.agents.schemas.request import ReportRequest
from app.agents.nodes.ingestion import run_ingestion
from app.agents.nodes.metrics import run_metrics
from app.agents.nodes.risk import run_risk_assessment
from app.agents.nodes.narrative import run_narrative
from app.agents.nodes.governance import run_governance
from app.core.guardrails import check_numeric_consistency
from app.core.audit import create_run, complete_run, fail_run, log_agent_step

logger = logging.getLogger(__name__)

MAX_NARRATIVE_RETRIES = 2


# ─── Node Functions ───────────────────────────────────────────────────────────

async def ingest_node(state: RevSightState) -> dict:
    t0 = time.monotonic()
    logger.info(f"[{state['run_id']}] Ingestion started")
    result = await run_ingestion(state["request"], db=None)
    duration = int((time.monotonic() - t0) * 1000)
    await log_agent_step(state["run_id"], "ingestion", duration)
    return {
        "raw_data": result.model_dump(),
        "messages": [{"role": "system", "content": "Ingestion complete"}],
    }


async def metrics_node(state: RevSightState) -> dict:
    t0 = time.monotonic()
    logger.info(f"[{state['run_id']}] Metrics computation started")
    metrics = await run_metrics(state["request"])
    duration = int((time.monotonic() - t0) * 1000)
    await log_agent_step(
        state["run_id"], "metrics", duration,
        output_hash=md5(json.dumps([m.model_dump() for m in metrics]).encode()).hexdigest(),
    )
    return {
        "metrics": metrics,
        "messages": [{"role": "system", "content": f"Computed {len(metrics)} metrics"}],
    }


async def risk_node(state: RevSightState) -> dict:
    t0 = time.monotonic()
    logger.info(f"[{state['run_id']}] Risk assessment started")
    risks = await run_risk_assessment(state["request"], state["metrics"])
    duration = int((time.monotonic() - t0) * 1000)
    await log_agent_step(state["run_id"], "risk", duration)
    return {
        "risks": risks,
        "messages": [{"role": "system", "content": f"Identified {len(risks)} risks"}],
    }


async def narrative_node(state: RevSightState) -> dict:
    t0 = time.monotonic()
    logger.info(f"[{state['run_id']}] Narrative generation started")
    report = await run_narrative(state["request"], state["metrics"], state["risks"])
    duration = int((time.monotonic() - t0) * 1000)
    await log_agent_step(state["run_id"], "narrative", duration)

    passed, issues = check_numeric_consistency(report, state["metrics"])
    return {
        "report": report,
        "guardrail_passed": passed,
        "messages": [{"role": "system", "content": f"Narrative done. Guardrail: {'pass' if passed else 'fail'}"}],
    }


async def governance_node(state: RevSightState) -> dict:
    t0 = time.monotonic()
    logger.info(f"[{state['run_id']}] Governance check started")
    result = await run_governance(state["run_id"], state["request"], state["report"])
    duration = int((time.monotonic() - t0) * 1000)
    await log_agent_step(state["run_id"], "governance", duration)
    return {
        "approval_status": result["approval_status"],
        "messages": [{"role": "system", "content": f"Governance: {result['approval_status']}"}],
    }


# ─── Conditional Edges ────────────────────────────────────────────────────────

def guardrail_router(state: RevSightState) -> str:
    """Route back to narrative if guardrail failed, otherwise to governance."""
    if not state.get("guardrail_passed", True):
        retry_count = sum(1 for m in state.get("messages", [])
                          if "Narrative done" in str(m.get("content", "")))
        if retry_count <= MAX_NARRATIVE_RETRIES:
            logger.warning(f"[{state['run_id']}] Guardrail failed, retrying narrative (attempt {retry_count})")
            return "narrative"
    return "governance"


def governance_router(state: RevSightState) -> str:
    return END if state.get("approval_status") == "approved" else END


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(RevSightState)

    graph.add_node("ingest", ingest_node)
    graph.add_node("compute_metrics", metrics_node)
    graph.add_node("assess_risks", risk_node)
    graph.add_node("generate_narrative", narrative_node)
    graph.add_node("governance", governance_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "compute_metrics")
    graph.add_edge("compute_metrics", "assess_risks")
    graph.add_edge("assess_risks", "generate_narrative")
    graph.add_conditional_edges("generate_narrative", guardrail_router, {
        "narrative": "generate_narrative",
        "governance": "governance",
    })
    graph.add_edge("governance", END)

    return graph


compiled_graph = build_graph().compile()


async def run_pipeline(request: ReportRequest) -> RevSightState:
    """Entry point: run the full pipeline and return final state."""
    run_id = str(uuid.uuid4())
    await create_run(run_id, request.model_dump())

    initial_state: RevSightState = {
        "request": request,
        "run_id": run_id,
        "raw_data": {},
        "metrics": [],
        "risks": [],
        "report": None,
        "messages": [],
        "guardrail_passed": True,
        "approval_status": "pending",
    }

    try:
        final_state = await compiled_graph.ainvoke(initial_state)
        if final_state.get("report"):
            await complete_run(run_id, final_state["report"].model_dump())
        return final_state
    except Exception as e:
        await fail_run(run_id, str(e))
        raise
