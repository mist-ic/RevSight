"""Guardrails -- numeric consistency check between narrative and metrics."""
from __future__ import annotations

import re
import logging

from app.agents.schemas.metrics import MetricResult
from app.agents.schemas.report import PipelineHealthReport

logger = logging.getLogger(__name__)

# Acceptable constants that can appear in narrative without being in metrics
ALLOWED_CONSTANTS = {"0", "1", "2", "3", "100", "0.0", "1.0", "45", "3x", "2x"}


def extract_numbers(text: str) -> set[str]:
    """Extract all numeric values (including percentages and decimals) from text."""
    # Match numbers like 4.2, 28%, 1800, $4.2M, 3x
    raw = re.findall(r"\$?(\d+(?:\.\d+)?)[xX%]?", text)
    return {n for n in raw if n not in ALLOWED_CONSTANTS}


def check_numeric_consistency(
    report: PipelineHealthReport,
    metrics: list[MetricResult],
) -> tuple[bool, list[str]]:
    """
    Verify that every number in the narrative exists in the metrics.
    Returns (passed, list_of_issues).
    """
    metric_values = {str(round(m.value, 1)) for m in metrics}
    metric_values |= {str(int(m.value)) for m in metrics}

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
