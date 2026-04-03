"""
CSV Import endpoint.

POST /api/import/opportunities  -- import a CSV of opportunities
POST /api/import/activities     -- import a CSV of activities

CSV format for opportunities (header required):
  id, account_id, name, stage, amount, close_date, owner_id, region, segment, quarter

CSV format for activities (header required):
  id, opportunity_id, type, subject, date, outcome
"""
from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.db.connection import get_pool

router = APIRouter(tags=["import"])


# --------------------------------------------------------------------------- #
# Response models
# --------------------------------------------------------------------------- #

class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
    message: str


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _parse_csv(content: bytes) -> tuple[list[str], list[dict]]:
    """Decode bytes, parse CSV, return (headers, rows)."""
    text = content.decode("utf-8-sig")  # handle BOM
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    rows = [dict(row) for row in reader]
    return list(headers), rows


def _coerce_str(val: str | None) -> str | None:
    if val is None or val.strip() == "":
        return None
    return val.strip()


def _coerce_date(val: str | None) -> date | None:
    if not val or not val.strip():
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _coerce_float(val: str | None) -> float | None:
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", ""))
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Opportunities import
# --------------------------------------------------------------------------- #

OPPORTUNITY_REQUIRED = {"name", "stage", "region", "segment", "quarter"}
OPPORTUNITY_CANONICAL_STAGES = {
    "discovery", "demo", "proposal", "negotiation", "closed won", "closed lost",
}


@router.post("/opportunities", response_model=ImportResult)
async def import_opportunities(
    file: Annotated[UploadFile, File(description="CSV file of opportunities")],
    upsert: bool = Query(default=True, description="Upsert on id conflict (default: True)"),
):
    """
    Import or upsert opportunities from a CSV file.

    Required columns: name, stage, region, segment, quarter
    Optional columns: id, account_id, owner_id, amount, close_date

    Stages are fuzzy-matched to canonical names:
    Discovery, Demo, Proposal, Negotiation, Closed Won, Closed Lost
    """
    content = await file.read()
    headers, rows = _parse_csv(content)

    missing = OPPORTUNITY_REQUIRED - {h.lower().strip() for h in headers}
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required columns: {', '.join(sorted(missing))}",
        )

    pool = await get_pool()
    imported = 0
    skipped = 0
    errors: list[str] = []

    async with pool.acquire() as conn:
        for i, row in enumerate(rows, start=2):  # row 1 is header
            try:
                row_lower = {k.lower().strip(): v for k, v in row.items()}

                opp_id = _coerce_str(row_lower.get("id")) or str(uuid.uuid4())
                name = _coerce_str(row_lower.get("name"))
                stage = _coerce_str(row_lower.get("stage")) or "Discovery"
                region = _coerce_str(row_lower.get("region"))
                segment = _coerce_str(row_lower.get("segment"))
                quarter = _coerce_str(row_lower.get("quarter"))
                amount = _coerce_float(row_lower.get("amount"))
                close_date = _coerce_date(row_lower.get("close_date"))
                account_id = _coerce_str(row_lower.get("account_id"))
                owner_id = _coerce_str(row_lower.get("owner_id"))

                if not name:
                    errors.append(f"Row {i}: missing 'name' value -- skipped")
                    skipped += 1
                    continue

                # Fuzzy stage matching
                stage_lower = (stage or "").lower().strip()
                if stage_lower not in OPPORTUNITY_CANONICAL_STAGES:
                    # Try prefix match
                    matched = next(
                        (s for s in OPPORTUNITY_CANONICAL_STAGES if stage_lower.startswith(s[:4])),
                        "Discovery",
                    )
                    stage = matched.title()

                if upsert:
                    await conn.execute(
                        """
                        INSERT INTO opportunities
                            (id, account_id, name, stage, amount, close_date, owner_id, region, segment, quarter)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (id) DO UPDATE SET
                            name       = EXCLUDED.name,
                            stage      = EXCLUDED.stage,
                            amount     = EXCLUDED.amount,
                            close_date = EXCLUDED.close_date,
                            region     = EXCLUDED.region,
                            segment    = EXCLUDED.segment,
                            quarter    = EXCLUDED.quarter
                        """,
                        opp_id, account_id, name, stage, amount, close_date,
                        owner_id, region, segment, quarter,
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO opportunities
                            (id, account_id, name, stage, amount, close_date, owner_id, region, segment, quarter)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                        opp_id, account_id, name, stage, amount, close_date,
                        owner_id, region, segment, quarter,
                    )

                imported += 1

            except Exception as e:
                errors.append(f"Row {i}: {e}")
                skipped += 1

    # Refresh the materialized view so charts pick up new data immediately
    if imported > 0:
        try:
            async with pool.acquire() as conn:
                await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_pipeline_metrics")
        except Exception:
            pass  # non-blocking

    return ImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors[:20],  # cap at 20 error messages
        message=f"Imported {imported} opportunities, skipped {skipped}.",
    )


# --------------------------------------------------------------------------- #
# Activities import
# --------------------------------------------------------------------------- #

@router.post("/activities", response_model=ImportResult)
async def import_activities(
    file: Annotated[UploadFile, File(description="CSV file of activities")],
):
    """
    Import activities from a CSV file.

    Required columns: opportunity_id, type
    Optional columns: id, subject, date, outcome
    """
    content = await file.read()
    headers, rows = _parse_csv(content)

    if "opportunity_id" not in {h.lower().strip() for h in headers}:
        raise HTTPException(status_code=400, detail="CSV must have an 'opportunity_id' column")

    pool = await get_pool()
    imported = 0
    skipped = 0
    errors: list[str] = []

    async with pool.acquire() as conn:
        for i, row in enumerate(rows, start=2):
            try:
                row_lower = {k.lower().strip(): v for k, v in row.items()}
                act_id = _coerce_str(row_lower.get("id")) or str(uuid.uuid4())
                opp_id = _coerce_str(row_lower.get("opportunity_id"))
                act_type = _coerce_str(row_lower.get("type")) or "Call"
                subject = _coerce_str(row_lower.get("subject"))
                act_date = _coerce_date(row_lower.get("date"))
                outcome = _coerce_str(row_lower.get("outcome"))

                if not opp_id:
                    errors.append(f"Row {i}: missing 'opportunity_id' -- skipped")
                    skipped += 1
                    continue

                await conn.execute(
                    """
                    INSERT INTO activities (id, opportunity_id, type, subject, date, outcome)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    act_id, opp_id, act_type, subject, act_date, outcome,
                )
                imported += 1

            except Exception as e:
                errors.append(f"Row {i}: {e}")
                skipped += 1

    return ImportResult(
        imported=imported,
        skipped=skipped,
        errors=errors[:20],
        message=f"Imported {imported} activities, skipped {skipped}.",
    )
