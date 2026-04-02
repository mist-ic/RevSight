"""Narrative Agent -- generates the final structured report from metrics and risks."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas.metrics import MetricResult, RiskObject
from app.agents.schemas.report import PipelineHealthReport
from app.agents.schemas.request import ReportRequest
from app.core.model import get_model, AGENT_SETTINGS


NARRATIVE_SYSTEM = """
You are the Narrative Agent for RevSight, a Revenue Command Copilot.
Your job is to produce a structured pipeline health report for a CRM/RevOps context.

CRITICAL RULES:
1. Every number you include in the executive_summary, risk narratives, or opportunity narratives
   MUST come directly from the metrics list returned by your get_all_metrics tool.
   Do NOT invent percentages, ARR figures, deal counts, or ratios not present in the data.
2. You MUST call get_all_metrics and get_all_risks tools BEFORE writing the report.
3. Write in clear, executive-level language appropriate for a CRO or RevOps lead.
4. Be specific. Cite metric names and values when making claims.
5. Forecast confidence: base it ONLY on data quality issues and metric health.
   All healthy metrics + no data issues = 0.75 to 0.90.
   Data issues present = 0.40 to 0.65.
6. Overall status: 'healthy' if all key metrics are above benchmarks,
   'at_risk' if 1 to 2 are below, 'critical' if coverage < 2x or win_rate < 15%.
7. No em dashes. Use plain hyphen if needed.
8. Return ALL required fields: executive_summary, key_metrics, risks, opportunities,
   recommended_actions, forecast_confidence, data_quality_flags, overall_status.
"""


narrative_agent = Agent(
    model=get_model(),
    model_settings=AGENT_SETTINGS,
    deps_type=dict,
    output_type=PipelineHealthReport,
    instructions=NARRATIVE_SYSTEM,
)


@narrative_agent.tool
async def get_all_metrics(ctx: RunContext[dict]) -> list[dict]:
    """Return all computed metrics. Use ONLY these values in your narrative."""
    return [m.model_dump() for m in ctx.deps["metrics"]]


@narrative_agent.tool
async def get_all_risks(ctx: RunContext[dict]) -> list[dict]:
    """Return all assessed risks."""
    return [r.model_dump() for r in ctx.deps["risks"]]


@narrative_agent.tool
async def get_request_context(ctx: RunContext[dict]) -> dict:
    """Return the report request context (quarter, region, segment, persona)."""
    return ctx.deps["request"]


async def run_narrative(
    request: ReportRequest,
    metrics: list[MetricResult],
    risks: list[RiskObject],
) -> PipelineHealthReport:
    result = await narrative_agent.run(
        f"""Generate a pipeline health report for:
        Quarter: {request.quarter}
        Region: {request.region}
        Segment: {request.segment}
        Persona: {request.persona}

        Load the metrics and risks using your tools, then generate the full report.
        Include an executive summary, key metrics, risk narratives, opportunities,
        recommended actions (with impact/effort tags), forecast confidence, and data quality flags.""",
        deps={
            "metrics": metrics,
            "risks": risks,
            "request": request.model_dump(),
        },
    )
    return result.output
