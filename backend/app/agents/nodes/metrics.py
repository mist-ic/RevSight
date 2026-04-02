"""Metrics Agent -- computes deterministic pipeline metrics via SQL."""
from __future__ import annotations

from pydantic_ai import Agent, RunContext

from app.agents.schemas.metrics import MetricResult
from app.agents.schemas.request import ReportRequest
from app.agents.tools.sql_tools import run_metric_query
from app.agents.tools.metric_tools import (
    compute_pipeline_coverage,
    compute_win_rate,
    compute_avg_velocity,
    compute_slippage,
    compute_stale_deals,
)
from app.core.model import get_model, AGENT_SETTINGS


metrics_agent = Agent(
    model=get_model(),
    model_settings=AGENT_SETTINGS,
    deps_type=dict,
    output_type=list[MetricResult],
    instructions="""
    You are the Metrics Agent for RevSight.
    Your job is to compute all pipeline health metrics by calling SQL tools.
    You MUST call each of: coverage, conversion, velocity, slippage, and aging queries.
    NEVER invent or estimate numeric values. Only report numbers returned by the tools.
    Return a list of MetricResult objects, one per metric.
    """,
)


@metrics_agent.tool
async def query_coverage(ctx: RunContext[dict]) -> list[dict]:
    """Execute the pipeline coverage SQL query."""
    p = ctx.deps["params"]
    return await run_metric_query("coverage", p)


@metrics_agent.tool
async def query_conversion(ctx: RunContext[dict]) -> list[dict]:
    """Execute the stage conversion rate SQL query."""
    p = ctx.deps["params"]
    return await run_metric_query("conversion", p)


@metrics_agent.tool
async def query_velocity(ctx: RunContext[dict]) -> list[dict]:
    """Execute the deal velocity SQL query."""
    p = ctx.deps["params"]
    return await run_metric_query("velocity", p)


@metrics_agent.tool
async def query_slippage(ctx: RunContext[dict]) -> list[dict]:
    """Execute the close date slippage SQL query."""
    p = ctx.deps["params"]
    return await run_metric_query("slippage", p)


@metrics_agent.tool
async def query_aging(ctx: RunContext[dict]) -> list[dict]:
    """Execute the deal aging SQL query."""
    p = ctx.deps["params"]
    return await run_metric_query("aging", p)


async def run_metrics(request: ReportRequest) -> list[MetricResult]:
    params = {
        "scenario_id": request.scenario_id,
        "quarter": request.quarter,
        "region": request.region,
        "segment": request.segment,
    }
    result = await metrics_agent.run(
        f"""Compute all pipeline metrics for scenario={request.scenario_id},
        quarter={request.quarter}, region={request.region}, segment={request.segment}.
        Run all 5 queries: coverage, conversion, velocity, slippage, aging.
        Then return MetricResult objects for: pipeline_coverage, win_rate,
        avg_deal_velocity, close_date_slippage, stale_deals.""",
        deps={"params": params},
    )
    return result.output
