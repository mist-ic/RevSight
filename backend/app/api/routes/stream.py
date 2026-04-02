"""SSE streaming endpoint for real-time agent step updates."""
from __future__ import annotations

import json
import uuid
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.agents.schemas.request import ReportRequest
from app.agents.graph import compiled_graph, run_pipeline
from app.core.audit import create_run

router = APIRouter()

SCENARIO_MAP = {
    "na_enterprise": "na_healthy",
    "emea_smb": "emea_undercovered",
    "apac_enterprise": "apac_dataquality",
}


@router.post("/stream")
async def stream_report(request: ReportRequest):
    """
    SSE endpoint streaming agent execution steps.
    Events: step, tool_start, tool_end, token, done, error
    """
    if not request.scenario_id:
        key = f"{request.region.lower()}_{request.segment.lower()}"
        request = request.model_copy(
            update={"scenario_id": SCENARIO_MAP.get(key, "na_healthy")}
        )

    run_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[str, None]:
        yield f"data: {json.dumps({'type': 'run_started', 'run_id': run_id})}\n\n"

        try:
            await create_run(run_id, request.model_dump())

            from app.agents.state import RevSightState
            initial_state: RevSightState = {
                "request": request,
                "run_id": run_id,
                "raw_data": {},
                "metrics": [],
                "risks": [],
                "report": None,
                "messages": [],
                "guardrail_passed": True,
                "narrative_retry_count": 0,
                "approval_status": "pending",
            }

            async for event in compiled_graph.astream_events(
                initial_state,
                config={"configurable": {"thread_id": run_id}},
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chain_start" and event.get("name") not in ("LangGraph", ""):
                    yield f"data: {json.dumps({'type': 'step', 'node': event['name']})}\n\n"

                elif kind == "on_tool_start":
                    yield f"data: {json.dumps({'type': 'tool_start', 'name': event['name'], 'input': str(event['data'].get('input', ''))[:200]})}\n\n"

                elif kind == "on_tool_end":
                    yield f"data: {json.dumps({'type': 'tool_end', 'name': event['name'], 'output': str(event['data'].get('output', ''))[:500]})}\n\n"

                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                await asyncio.sleep(0)  # yield to event loop

            # Fetch the final report from DB and emit it
            from app.db.connection import execute_one
            row = await execute_one("SELECT report_json FROM runs WHERE id = $1", run_id)
            report = row.get("report_json") if row else None
            yield f"data: {json.dumps({'type': 'done', 'run_id': run_id, 'report': report})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return EventSourceResponse(event_generator())
