"""Metric computation helpers used by the metrics agent."""
from __future__ import annotations

from app.agents.schemas.metrics import MetricResult


def compute_pipeline_coverage(coverage_rows: list[dict], quota: float = 5_000_000) -> MetricResult:
    """Compute total open pipeline ARR vs quota."""
    open_arr = sum(r.get("total_arr") or 0 for r in coverage_rows)
    coverage_ratio = round(open_arr / quota, 2) if quota else 0
    return MetricResult(
        metric_id="pipeline_coverage",
        name="Pipeline Coverage",
        value=coverage_ratio,
        unit="x",
        comparison=3.0,  # 3x is the benchmark
        trend="up" if coverage_ratio >= 3.0 else "down",
    )


def compute_win_rate(conversion_rows: list[dict]) -> MetricResult:
    """Compute win rate from stage transitions."""
    total_closed = sum(r.get("transitions") or 0 for r in conversion_rows
                       if r.get("to_stage") in ("Closed Won", "Closed Lost"))
    won = sum(r.get("won_count") or 0 for r in conversion_rows)
    rate = round(100 * won / total_closed, 1) if total_closed else 0
    return MetricResult(
        metric_id="win_rate",
        name="Win Rate",
        value=rate,
        unit="%",
        comparison=25.0,
        trend="up" if rate >= 25 else "down",
    )


def compute_avg_velocity(velocity_rows: list[dict]) -> MetricResult:
    """Compute average deal velocity across all open stages."""
    days_list = [r.get("avg_days_in_flight") or 0 for r in velocity_rows
                 if r.get("stage_name") not in ("Closed Won", "Closed Lost")]
    avg = round(sum(days_list) / len(days_list), 1) if days_list else 0
    return MetricResult(
        metric_id="avg_deal_velocity",
        name="Avg Deal Velocity",
        value=avg,
        unit="days",
        comparison=75.0,
        trend="up" if avg <= 75 else "down",
    )


def compute_slippage(slippage_row: dict) -> MetricResult:
    count = slippage_row.get("slipped_deal_count") or 0
    return MetricResult(
        metric_id="close_date_slippage",
        name="Close Date Slippage",
        value=float(count),
        unit="deals",
        comparison=0.0,
        trend="down" if count > 5 else "up",
    )


def compute_stale_deals(aging_rows: list[dict]) -> MetricResult:
    stale = sum(r.get("stale_count") or 0 for r in aging_rows)
    stale_arr = sum(r.get("stale_arr") or 0 for r in aging_rows)
    return MetricResult(
        metric_id="stale_deals",
        name="Stale Deals (>45 days)",
        value=float(stale),
        unit="deals",
        comparison=0.0,
        trend="down" if stale > 10 else "up",
    )
