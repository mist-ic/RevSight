from __future__ import annotations

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph import add_messages

from app.agents.schemas.request import ReportRequest
from app.agents.schemas.metrics import MetricResult, RiskObject
from app.agents.schemas.report import PipelineHealthReport


def add_metrics(left: list, right: list) -> list:
    return left + right


def add_risks(left: list, right: list) -> list:
    return left + right


class RevSightState(TypedDict):
    request: ReportRequest
    run_id: str
    raw_data: dict
    metrics: Annotated[list[MetricResult], add_metrics]
    risks: Annotated[list[RiskObject], add_risks]
    report: Optional[PipelineHealthReport]
    messages: Annotated[list, add_messages]
    guardrail_passed: bool
    narrative_retry_count: int
    approval_status: str  # "pending" | "approved" | "rejected"
