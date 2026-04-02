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


@router.post("", response_model=ReportResponse)
async def create_report(request: ReportRequest):
    """Kick off a new pipeline analysis run. Returns run_id immediately."""
    # If no scenario_id provided, derive from region+segment
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
    )


@router.get("/{run_id}", response_model=ReportResponse)
async def get_report(run_id: str):
    """Fetch a completed report by run_id."""
    row = await execute_one("SELECT * FROM runs WHERE id = $1", run_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")
    return ReportResponse(
        run_id=row["id"],
        status=row["status"],
        report=row.get("report_json"),
    )
