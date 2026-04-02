"""Narrative Agent -- generates the final structured report from metrics and risks."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas.metrics import MetricResult, RiskObject
from app.agents.schemas.report import PipelineHealthReport
from app.agents.schemas.request import ReportRequest


NARRATIVE_SYSTEM = """
You are the Narrative Agent for RevSight, a Revenue Command Copilot.
Your job is to produce a structured pipeline health report for a CRM/RevOps context.

CRITICAL RULES:
1. Every number you include in the executive_summary, risk narratives, or opportunity narratives
   MUST come directly from the metrics list passed to you. Do NOT invent percentages, ARR figures,
   deal counts, or ratios not present in the data.
2. Write in clear, executive-level language appropriate for a CRO or RevOps lead.
3. Be specific. Cite metric names and values when making claims.
4. Forecast confidence: base this ONLY on data quality issues and metric health.
   High data quality + healthy metrics = 0.75-0.90. Issues present = 0.40-0.65.
5. Overall status: 'healthy' if all key metrics are above benchmarks,
   'at_risk' if 1-2 are below, 'critical' if coverage < 2x or win_rate < 15%.
6. No em dashes. Use plain hyphen if needed.
"""


narrative_agent = Agent(
    model="openai:gpt-4o",
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
