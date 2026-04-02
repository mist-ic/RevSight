from fastapi import APIRouter, Query
from app.db.connection import execute_query

router = APIRouter()


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
    return {"runs": rows, "limit": limit, "offset": offset}
