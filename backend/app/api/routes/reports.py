from datetime import datetime, date
import decimal
import json as _json
from uuid import UUID
from fastapi import APIRouter, Query
from app.db.connection import execute_query, execute_one
from app.agents.graph import run_pipeline
from app.agents.schemas.request import ReportRequest
from pydantic import BaseModel

router = APIRouter()


def _coerce_row(row: dict) -> dict:
    result = {}
    for k, v in row.items():
        if isinstance(v, UUID):
            result[k] = str(v)
        elif isinstance(v, (datetime, date)):
            result[k] = v.isoformat()
        elif isinstance(v, decimal.Decimal):
            result[k] = float(v)
        else:
            result[k] = v
    return result


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
    row = await execute_one("SELECT * FROM runs WHERE id = $1::uuid", run_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")

    row = _coerce_row(dict(row))

    # asyncpg JSONB comes back as string with SELECT * -- parse it
    raw = row.get("report_json")
    if isinstance(raw, str):
        try:
            report_data = _json.loads(raw)
        except Exception:
            report_data = None
    else:
        report_data = raw

    return ReportResponse(
        run_id=row["id"],
        status=row["status"],
        report=report_data,
        region=row.get("region"),
        segment=row.get("segment"),
        quarter=row.get("quarter"),
        persona=row.get("persona"),
    )
