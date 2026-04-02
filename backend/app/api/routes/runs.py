from datetime import datetime, date
import decimal
from uuid import UUID
from fastapi import APIRouter, Query
from app.db.connection import execute_query

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


@router.get("")
async def list_runs(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
):
    """Return paginated run history."""
    rows = await execute_query(
        """
        SELECT id, persona, quarter, region, segment, scenario_id,
               status, created_at, completed_at
        FROM runs
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )
    return {"runs": [_coerce_row(r) for r in rows], "limit": limit, "offset": offset}
