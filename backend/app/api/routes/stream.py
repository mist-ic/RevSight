"""SSE streaming endpoint for real-time agent step updates."""
from __future__ import annotations

import json
import uuid
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.agents.schemas.request import ReportRequest
from app.agents.graph import compiled_graph
from app.core.audit import create_run, complete_run, fail_run

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
    Yields plain dicts -- EventSourceResponse wraps them in data: prefix.
    """
    if not request.scenario_id:
        key = f"{request.region.lower()}_{request.segment.lower()}"
        request = request.model_copy(
            update={"scenario_id": SCENARIO_MAP.get(key, "na_healthy")}
        )

    run_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[dict, None]:
        yield {"data": json.dumps({"type": "run_started", "run_id": run_id})}

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

            final_state = None

            async for event in compiled_graph.astream_events(
                initial_state,
                config={"configurable": {"thread_id": run_id}},
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_chain_start" and event.get("name") not in ("LangGraph", ""):
                    yield {"data": json.dumps({"type": "step", "node": event["name"]})}

                elif kind == "on_tool_start":
                    yield {"data": json.dumps({
                        "type": "tool_start",
                        "name": event["name"],
                        "input": str(event["data"].get("input", ""))[:200],
                    })}

                elif kind == "on_tool_end":
                    yield {"data": json.dumps({
                        "type": "tool_end",
                        "name": event["name"],
                        "output": str(event["data"].get("output", ""))[:500],
                    })}

                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    if chunk:
                        yield {"data": json.dumps({"type": "token", "content": chunk})}

                elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                    # Final state comes out here
                    final_state = event["data"].get("output")

                await asyncio.sleep(0)

            # Persist and emit done event
            report = None
            if final_state and final_state.get("report"):
                report = final_state["report"].model_dump()
                await complete_run(run_id, report)
            else:
                await fail_run(run_id, "No report generated")

            yield {"data": json.dumps({"type": "done", "run_id": run_id, "report": report})}

        except Exception as e:
            import traceback
            traceback.print_exc()
            await fail_run(run_id, str(e))
            yield {"data": json.dumps({"type": "error", "message": str(e)})}

    return EventSourceResponse(event_generator())
