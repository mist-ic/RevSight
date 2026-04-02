"""Risk Agent -- classifies pipeline risks from metrics using heuristics + LLM."""
from __future__ import annotations

import uuid
from pydantic_ai import Agent, RunContext

from app.agents.schemas.metrics import MetricResult, RiskObject, RiskSeverity
from app.agents.schemas.request import ReportRequest
from app.core.model import get_model, AGENT_SETTINGS


RISK_THRESHOLDS = {
    "pipeline_coverage_low": 3.0,       # below 3x = risk
    "pipeline_coverage_critical": 2.0,  # below 2x = critical
    "stale_deals_threshold": 10,         # more than 10 stale deals
    "slippage_threshold": 5,             # more than 5 slipped deals
    "win_rate_low": 20.0,               # below 20% win rate
}


def _build_heuristic_risks(metrics: list[MetricResult]) -> list[RiskObject]:
    """Rule-based risk detection before LLM narrative enrichment."""
    risks: list[RiskObject] = []
    metric_map = {m.metric_id: m for m in metrics}

    coverage = metric_map.get("pipeline_coverage")
    if coverage:
        if coverage.value < RISK_THRESHOLDS["pipeline_coverage_critical"]:
            risks.append(RiskObject(
                risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                title="Critical Pipeline Coverage Shortfall",
                severity=RiskSeverity.HIGH,
                rationale=f"Pipeline coverage is {coverage.value:.1f}x vs 3x target. "
                           "Significant miss risk unless new pipeline is added immediately.",
                linked_metric_ids=["pipeline_coverage"],
                recommendation="Immediate SDR blitz needed. Review TAM and increase outbound cadence by 40%.",
            ))
        elif coverage.value < RISK_THRESHOLDS["pipeline_coverage_low"]:
            risks.append(RiskObject(
                risk_id=f"risk_{uuid.uuid4().hex[:8]}",
                title="Pipeline Coverage Below Target",
                severity=RiskSeverity.MEDIUM,
                rationale=f"Pipeline coverage is {coverage.value:.1f}x vs 3x benchmark.",
                linked_metric_ids=["pipeline_coverage"],
                recommendation="Increase top-of-funnel activity and review stage conversion bottlenecks.",
            ))

    stale = metric_map.get("stale_deals")
    if stale and stale.value > RISK_THRESHOLDS["stale_deals_threshold"]:
        risks.append(RiskObject(
            risk_id=f"risk_{uuid.uuid4().hex[:8]}",
            title="High Volume of Stale Deals",
            severity=RiskSeverity.MEDIUM,
            rationale=f"{int(stale.value)} deals have been in their current stage for over 45 days.",
            linked_metric_ids=["stale_deals"],
            recommendation="Conduct deal review on all stale opportunities. "
                           "Disqualify or re-engage within 2 weeks.",
        ))

    slippage = metric_map.get("close_date_slippage")
    if slippage and slippage.value > RISK_THRESHOLDS["slippage_threshold"]:
        risks.append(RiskObject(
            risk_id=f"risk_{uuid.uuid4().hex[:8]}",
            title="Close Date Slippage Detected",
            severity=RiskSeverity.MEDIUM,
            rationale=f"{int(slippage.value)} opportunities have passed their close date without resolution.",
            linked_metric_ids=["close_date_slippage"],
            recommendation="Update close dates or disqualify. Flag for manager review.",
        ))

    win_rate = metric_map.get("win_rate")
    if win_rate and win_rate.value < RISK_THRESHOLDS["win_rate_low"]:
        risks.append(RiskObject(
            risk_id=f"risk_{uuid.uuid4().hex[:8]}",
            title="Below-Benchmark Win Rate",
            severity=RiskSeverity.MEDIUM if win_rate.value >= 15 else RiskSeverity.HIGH,
            rationale=f"Win rate is {win_rate.value:.1f}% vs 25% benchmark.",
            linked_metric_ids=["win_rate"],
            recommendation="Analyze lost deal reasons. Review competitive positioning and late-stage discounting.",
        ))

    return risks


risk_agent = Agent(
    model=get_model(),
    model_settings=AGENT_SETTINGS,
    deps_type=dict,
    output_type=list[RiskObject],
    instructions="""
    You are the Risk Assessment Agent for RevSight.
    You receive pre-computed heuristic risks and a list of pipeline metrics.
    Your job is to:
    1. Review the heuristic risks and validate them
    2. Check for any additional patterns in the metrics that indicate risk
    3. Return the final list of RiskObjects with refined rationale and recommendations
    CRITICAL: ONLY reference metric values that appear in the provided metrics list.
    Do NOT invent numbers. Every number you mention must come from the metrics.
    """,
)


@risk_agent.tool
async def get_metrics_summary(ctx: RunContext[dict]) -> list[dict]:
    """Return all computed metrics for risk analysis."""
    return [m.model_dump() for m in ctx.deps["metrics"]]


@risk_agent.tool
async def get_heuristic_risks(ctx: RunContext[dict]) -> list[dict]:
    """Return the pre-computed heuristic risks."""
    return [r.model_dump() for r in ctx.deps["heuristic_risks"]]


async def run_risk_assessment(
    request: ReportRequest,
    metrics: list[MetricResult],
) -> list[RiskObject]:
    heuristic_risks = _build_heuristic_risks(metrics)

    result = await risk_agent.run(
        f"""Assess pipeline risks for scenario={request.scenario_id},
        quarter={request.quarter}, region={request.region}, segment={request.segment}.
        Review the heuristic risks and metrics. Return the refined risk list.""",
        deps={
            "metrics": metrics,
            "heuristic_risks": heuristic_risks,
            "request": request.model_dump(),
        },
    )
    return result.output
