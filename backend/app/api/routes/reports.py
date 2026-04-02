from fastapi import APIRouter
from app.db.connection import execute_one
from app.agents.graph import run_pipeline
from app.agents.schemas.request import ReportRequest
from pydantic import BaseModel
import uuid

router = APIRouter()


class ReportResponse(BaseModel):
    run_id: str
    status: str
    report: dict | None = None
    region: str | None = None
    segment: str | None = None
    quarter: str | None = None
    persona: str | None = None


@router.post("", response_model=ReportResponse)
async def create_report(request: ReportRequest):
    """Kick off a new pipeline analysis run. Returns when complete."""
    if not request.scenario_id:
        key = f"{request.region.lower()}_{request.segment.lower()}"
        scenario_map = {
            "na_enterprise": "na_healthy",
            "emea_smb": "emea_undercovered",
            "apac_enterprise": "apac_dataquality",
        }
        request = request.model_copy(update={"scenario_id": scenario_map.get(key, "na_healthy")})

    final_state = await run_pipeline(request)
    report = final_state.get("report")
    return ReportResponse(
        run_id=final_state["run_id"],
        status=final_state.get("approval_status", "done"),
        report=report.model_dump() if report else None,
        region=request.region,
        segment=request.segment,
        quarter=request.quarter,
        persona=str(request.persona.value if hasattr(request.persona, "value") else request.persona),
    )


@router.get("/{run_id}", response_model=ReportResponse)
async def get_report(run_id: str):
    """Fetch a completed report by run_id."""
    row = await execute_one("SELECT * FROM runs WHERE id = $1", run_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")

    # report_json is JSONB from postgres -- already a dict when fetched via asyncpg
    report_data = row.get("report_json")

    return ReportResponse(
        run_id=row["id"],
        status=row["status"],
        report=report_data,
        region=row.get("region"),
        segment=row.get("segment"),
        quarter=row.get("quarter"),
        persona=row.get("persona"),
    )
