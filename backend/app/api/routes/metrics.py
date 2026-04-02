from fastapi import APIRouter
from app.db.connection import execute_query

router = APIRouter()


@router.get("/pipeline")
async def get_pipeline_metrics(
    scenario_id: str = "na_healthy",
    quarter: str = "Q3-2026",
    region: str = "NA",
    segment: str = "Enterprise",
):
    """Return raw pipeline metrics aggregated by stage for chart rendering."""
    rows = await execute_query(
        """
        SELECT stage_name, deal_count, total_arr, avg_probability, avg_age_days, missing_close_dates
        FROM mv_pipeline_metrics
        WHERE scenario_id = $1 AND quarter = $2 AND region = $3 AND segment = $4
        ORDER BY
            CASE stage_name
                WHEN 'Discovery'   THEN 1
                WHEN 'Demo'        THEN 2
                WHEN 'Proposal'    THEN 3
                WHEN 'Negotiation' THEN 4
                ELSE 5
            END
        """,
        scenario_id, quarter, region, segment,
    )
    return {"metrics": rows, "scenario_id": scenario_id}
