"""Ingestion Agent -- loads and normalizes pipeline data from PostgreSQL."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.schemas.request import ReportRequest
from app.agents.tools.sql_tools import run_raw_query


class IngestionResult(BaseModel):
    snapshot: dict
    deal_count: int
    account_count: int
    activity_count: int
    data_quality_issues: list[str]


ingestion_agent = Agent(
    model="openai:gpt-4o",
    deps_type=dict,
    output_type=IngestionResult,
    instructions="""
    You are the Ingestion Agent for RevSight.
    Your job is to load and normalize pipeline data for a given quarter, region, and segment.
    Use the provided tools to load the data. Do not invent any numbers or data.
    Report any data quality issues you observe (missing close dates, inconsistent stage names, etc).
    """,
)


@ingestion_agent.tool
async def load_pipeline_snapshot(
    ctx: RunContext[dict],
    scenario_id: str,
    quarter: str,
    region: str,
    segment: str,
) -> dict:
    """Load the full pipeline snapshot for the given filters."""
    rows = await run_raw_query(
        """
        SELECT
            stage_name,
            COUNT(*)        AS deal_count,
            SUM(arr)        AS total_arr,
            AVG(arr)        AS avg_arr,
            AVG(probability) AS avg_probability,
            SUM(CASE WHEN close_date IS NULL THEN 1 ELSE 0 END)           AS missing_close_dates,
            SUM(CASE WHEN close_date < NOW()::date THEN 1 ELSE 0 END)     AS past_close_dates,
            COUNT(DISTINCT account_id)                                     AS unique_accounts
        FROM opportunities
        WHERE scenario_id = $1 AND quarter = $2 AND region = $3 AND segment = $4
        GROUP BY stage_name
        """,
        scenario_id, quarter, region, segment,
    )
    return {"by_stage": rows, "scenario_id": scenario_id}


@ingestion_agent.tool
async def load_activity_summary(
    ctx: RunContext[dict],
    scenario_id: str,
    quarter: str,
    region: str,
    segment: str,
) -> dict:
    """Load activity counts by type for the pipeline."""
    rows = await run_raw_query(
        """
        SELECT a.type, COUNT(*) AS activity_count
        FROM activities a
        JOIN opportunities o ON a.opportunity_id = o.id
        WHERE o.scenario_id = $1 AND o.quarter = $2 AND o.region = $3 AND o.segment = $4
        GROUP BY a.type
        """,
        scenario_id, quarter, region, segment,
    )
    return {"by_type": rows}


async def run_ingestion(request: ReportRequest, db: object) -> IngestionResult:
    result = await ingestion_agent.run(
        f"""Load pipeline data for scenario={request.scenario_id},
        quarter={request.quarter}, region={request.region}, segment={request.segment}.
        Then load the activity summary. Report data quality issues.""",
        deps={"db": db, "request": request.model_dump()},
    )
    return result.output
