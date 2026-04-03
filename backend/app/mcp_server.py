"""
RevSight MCP Server

Exposes the RevSight PostgreSQL database as a read-only MCP server.
Mounted on the main FastAPI app at /mcp via streamable-http transport.

Tools:
  run_select(sql, limit)            -- execute any read-only SELECT
  list_revops_metrics(scenario_id)  -- return pre-computed pipeline metrics
  get_pipeline_summary(scenario_id) -- high-level pipeline health for a scenario

Resources:
  schema://tables                   -- all tables in the database
  schema://columns/{schema}/{table} -- columns for a specific table
  metrics://pipeline                -- available pre-computed metric names

Usage (standalone):
  cd backend && uv run python -m app.mcp_server

Usage (via HTTP, e.g. Claude Desktop or curl):
  cd backend && uv run python -m app.mcp_server --transport streamable-http
"""
from __future__ import annotations

import json
import os
import re

from mcp.server.fastmcp import FastMCP

from app.db.connection import get_pool

# --------------------------------------------------------------------------- #
# Instantiate the FastMCP server
# --------------------------------------------------------------------------- #

mcp = FastMCP(
    name="revsight-mcp",
    instructions=(
        "You are connected to the RevSight Revenue Copilot database. "
        "You can inspect the schema, run read-only SELECT queries, and retrieve "
        "pre-computed pipeline metrics for any scenario. "
        "Always inspect the schema or metrics list before running raw SQL. "
        "Only SELECT statements are permitted -- any write attempt will be rejected."
    ),
)


# --------------------------------------------------------------------------- #
# Guard: only allow SELECT queries
# --------------------------------------------------------------------------- #

_BANNED = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|"
    r"copy|vacuum|reindex|cluster|lock|call|do)\b",
    re.IGNORECASE,
)


def _assert_readonly(sql: str) -> None:
    stripped = sql.strip()
    if not re.match(r"^\s*select\b", stripped, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    if _BANNED.search(stripped):
        raise ValueError("Query contains disallowed keywords.")


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #

@mcp.tool()
async def run_select(sql: str, limit: int = 200) -> list[dict]:
    """
    Execute a read-only SELECT query against the RevSight database.

    Args:
        sql:   A valid PostgreSQL SELECT statement.
        limit: Maximum number of rows to return (default 200, max 1000).

    Returns:
        List of row dicts.
    """
    _assert_readonly(sql)
    limit = min(max(1, limit), 1000)
    wrapped = f"SELECT * FROM ({sql}) AS _q LIMIT $1"
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(wrapped, limit)
        return [dict(r) for r in rows]


@mcp.tool()
async def list_revops_metrics(
    scenario_id: str = "na_healthy",
    quarter: str = "Q3-2026",
) -> list[dict]:
    """
    Return pre-computed pipeline metrics for a given scenario from the
    mv_pipeline_metrics materialized view.

    Args:
        scenario_id: One of 'na_healthy', 'emea_undercovered', 'apac_dataquality'.
        quarter:     The quarter string, e.g. 'Q3-2026'.

    Returns:
        List of metric rows with stage_name, deal_count, total_value, avg_age.
    """
    region_map = {
        "na_healthy": "NA",
        "emea_undercovered": "EMEA",
        "apac_dataquality": "APAC",
    }
    segment_map = {
        "na_healthy": "Enterprise",
        "emea_undercovered": "SMB",
        "apac_dataquality": "Enterprise",
    }
    region = region_map.get(scenario_id, "NA")
    segment = segment_map.get(scenario_id, "Enterprise")

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT stage_name, deal_count, total_value, avg_age, quarter, region, segment
            FROM mv_pipeline_metrics
            WHERE region = $1 AND segment = $2 AND quarter = $3
            ORDER BY deal_count DESC
            """,
            region, segment, quarter,
        )
        result = []
        for r in rows:
            row = dict(r)
            # Serialize Decimal/UUID/date types
            for k, v in row.items():
                if hasattr(v, '__float__'):
                    row[k] = float(v)
            result.append(row)
        return result


@mcp.tool()
async def get_pipeline_summary(
    scenario_id: str = "na_healthy",
    quarter: str = "Q3-2026",
) -> dict:
    """
    Get a high-level pipeline summary for a scenario: coverage ratio, deal count,
    total pipeline value, and stage distribution.

    Args:
        scenario_id: One of 'na_healthy', 'emea_undercovered', 'apac_dataquality'.
        quarter:     The quarter string, e.g. 'Q3-2026'.

    Returns:
        Dict with coverage_ratio, total_deals, total_pipeline_value, stage_distribution.
    """
    region_map = {"na_healthy": "NA", "emea_undercovered": "EMEA", "apac_dataquality": "APAC"}
    segment_map = {"na_healthy": "Enterprise", "emea_undercovered": "SMB", "apac_dataquality": "Enterprise"}
    target_map = {"na_healthy": 5_000_000, "emea_undercovered": 5_000_000, "apac_dataquality": 5_000_000}

    region = region_map.get(scenario_id, "NA")
    segment = segment_map.get(scenario_id, "Enterprise")
    quota_target = target_map.get(scenario_id, 5_000_000)

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT stage_name, deal_count, total_value
            FROM mv_pipeline_metrics
            WHERE region = $1 AND segment = $2 AND quarter = $3
            ORDER BY deal_count DESC
            """,
            region, segment, quarter,
        )

        if not rows:
            return {"error": f"No data found for scenario '{scenario_id}'"}

        total_deals = sum(int(r["deal_count"]) for r in rows)
        total_value = sum(float(r["total_value"]) for r in rows)
        coverage_ratio = round(total_value / quota_target, 2)

        stage_distribution = {
            r["stage_name"]: {
                "deal_count": int(r["deal_count"]),
                "total_value": float(r["total_value"]),
                "pct_of_pipeline": round(float(r["total_value"]) / total_value * 100, 1) if total_value else 0,
            }
            for r in rows
        }

        return {
            "scenario_id": scenario_id,
            "quarter": quarter,
            "region": region,
            "segment": segment,
            "coverage_ratio": coverage_ratio,
            "total_deals": total_deals,
            "total_pipeline_value": total_value,
            "quota_target": quota_target,
            "stage_distribution": stage_distribution,
        }


# --------------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------------- #

@mcp.resource("schema://tables")
async def list_tables() -> list[dict]:
    """List all user-facing tables and views in the RevSight database."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND table_schema NOT LIKE 'pg_%'
            ORDER BY table_schema, table_name
            """
        )
        return [dict(r) for r in rows]


@mcp.resource("schema://columns/{schema}/{table}")
async def list_columns(schema: str, table: str) -> list[dict]:
    """List columns for a specific table with data types and nullability."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """,
            schema, table,
        )
        return [dict(r) for r in rows]


@mcp.resource("metrics://pipeline")
async def list_available_metrics() -> dict:
    """
    Describe the available pre-computed RevOps metrics and how to query them.
    """
    return {
        "available_scenarios": [
            {"id": "na_healthy",        "region": "NA",   "segment": "Enterprise", "health": "healthy"},
            {"id": "emea_undercovered", "region": "EMEA", "segment": "SMB",         "health": "at_risk"},
            {"id": "apac_dataquality",  "region": "APAC", "segment": "Enterprise", "health": "critical"},
        ],
        "available_quarters": ["Q3-2026"],
        "metric_definitions": {
            "coverage_ratio":      "Total pipeline value / quota target. Healthy >= 3.0x.",
            "deal_count":          "Number of open opportunities per stage.",
            "total_value":         "Sum of opportunity amounts per stage (USD).",
            "avg_age":             "Average days an opportunity has been in the current stage.",
            "stage_distribution":  "Percentage of pipeline value and deal count per stage.",
        },
        "usage": {
            "summary":     "Call get_pipeline_summary(scenario_id) for a quick overview.",
            "full_metrics": "Call list_revops_metrics(scenario_id) for per-stage breakdown.",
            "raw_sql":     "Call run_select(sql) for arbitrary read-only queries.",
        },
    }


# --------------------------------------------------------------------------- #
# Standalone entry point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import sys
    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    port = int(os.environ.get("MCP_PORT", "8001"))
    print(f"Starting RevSight MCP server (transport={transport})", flush=True)
    mcp.run(transport=transport)
