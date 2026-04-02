"""Guardrails -- numeric consistency check between narrative and metrics."""
from __future__ import annotations

import re
import logging

from app.agents.schemas.metrics import MetricResult
from app.agents.schemas.report import PipelineHealthReport

logger = logging.getLogger(__name__)

# Constants that can appear in narrative without being in metrics
ALLOWED_CONSTANTS = {
    "0", "1", "2", "3", "4", "5", "10", "100", "0.0", "1.0",
    "45", "90", "180", "365",  # common thresholds
    "2026", "2025", "2024",    # years
    "3x", "2x", "1x",
}


def extract_numbers(text: str) -> set[str]:
    """Extract all numeric values (including percentages and decimals) from text."""
    raw = re.findall(r"\$?(\d+(?:\.\d+)?)[xX%]?", text)
    return {n for n in raw if n not in ALLOWED_CONSTANTS}


def _metric_value_set(metrics: list[MetricResult]) -> set[str]:
    """Build a set of allowed numeric strings from the metrics list."""
    values: set[str] = set()
    for m in metrics:
        v = m.value
        values.add(str(round(v, 0)).rstrip("0").rstrip("."))  # e.g. "169"
        values.add(str(int(v)))                                # e.g. "169"
        values.add(str(round(v, 1)))                           # e.g. "169.2"
        values.add(str(round(v, 2)))                           # e.g. "169.18"
        # Also the raw float string in case exact match
        values.add(str(v))
    return values


def check_numeric_consistency(
    report: PipelineHealthReport,
    metrics: list[MetricResult],
) -> tuple[bool, list[str]]:
    """
    Verify that every number in the narrative exists in the metrics.
    Returns (passed, list_of_issues).
    """
    metric_values = _metric_value_set(metrics)

    issues: list[str] = []

    sources = [report.executive_summary]
    for risk in report.risks:
        sources.append(risk.narrative)
    for opp in report.opportunities:
        sources.append(opp.narrative)

    for text in sources:
        numbers = extract_numbers(text)
        unverified = numbers - metric_values - ALLOWED_CONSTANTS
        if unverified:
            issues.append(f"Unverified numbers in narrative: {sorted(unverified)}")

    if issues:
        logger.warning(f"Guardrail failed -- {len(issues)} issues: {issues}")
        return False, issues

    logger.info("Guardrail passed -- all narrative numbers verified against metrics")
    return True, []
