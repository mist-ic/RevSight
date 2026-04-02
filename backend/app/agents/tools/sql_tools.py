"""SQL tools for Pydantic AI agents to execute parameterized query templates."""
from __future__ import annotations

import os
from pathlib import Path

from app.db.connection import execute_query

QUERIES_DIR = Path(__file__).parent.parent.parent / "db" / "queries"


def _load_sql(name: str) -> str:
    path = QUERIES_DIR / f"{name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"SQL template not found: {name}")
    return path.read_text()


TEMPLATE_PARAM_MAP = {
    "coverage":   ("scenario_id", "quarter", "region", "segment"),
    "conversion": ("scenario_id", "quarter", "region", "segment"),
    "velocity":   ("scenario_id", "quarter", "region", "segment"),
    "slippage":   ("scenario_id", "quarter", "region", "segment"),
    "aging":      ("scenario_id", "quarter", "region", "segment"),
}

VALID_TEMPLATES = set(TEMPLATE_PARAM_MAP.keys())


async def run_metric_query(query_name: str, params: dict) -> list[dict]:
    """Execute a named SQL template with the given params dict."""
    if query_name not in VALID_TEMPLATES:
        raise ValueError(f"Unknown query template: {query_name}. Valid: {sorted(VALID_TEMPLATES)}")

    sql = _load_sql(query_name)
    param_order = TEMPLATE_PARAM_MAP[query_name]
    args = [params[k] for k in param_order]
    rows = await execute_query(sql, *args)
    # Coerce Decimal/numeric to float for LLM consumption
    return [
        {k: float(v) if hasattr(v, "__float__") and not isinstance(v, (int, str, bool)) else v
         for k, v in row.items()}
        for row in rows
    ]


async def run_raw_query(sql: str, *args) -> list[dict]:
    """Execute a raw SQL query (read-only, used by ingestion agent)."""
    blocked = ["insert ", "update ", "delete ", "drop ", "alter ", "truncate "]
    if any(kw in sql.lower() for kw in blocked):
        raise ValueError("Only SELECT queries are allowed in agents")
    return await execute_query(sql, *args)
