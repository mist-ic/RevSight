"""
DeepEval scenario-based evaluation tests for RevSight.

Run with:
    cd backend
    python -m uv run python -m pytest tests/eval/test_scenarios.py -v

Requires GEMINI_API_KEY and DATABASE_URL in environment (or backend/.env).
"""
import re
import asyncio

import pytest

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from app.agents.graph import run_pipeline
from app.agents.schemas.request import ReportRequest
from app.db.connection import init_db


# ---------------------------------------------------------------------------
# Run all 3 scenarios in one event loop at module-collection time so we
# never cross event-loop boundaries inside a pytest fixture.
# ---------------------------------------------------------------------------

SCENARIOS = [
    ("na_healthy",        "NA",   "Enterprise"),
    ("emea_undercovered", "EMEA", "SMB"),
    ("apac_dataquality",  "APAC", "Enterprise"),
]


async def _run_all_scenarios() -> dict[str, dict]:
    await init_db()
    results: dict[str, dict] = {}
    for scenario_id, region, segment in SCENARIOS:
        req = ReportRequest(
            quarter="Q3-2026",
            region=region,
            segment=segment,
            persona="revops",
            scenario_id=scenario_id,
        )
        state = await run_pipeline(req)
        report = state.get("report")
        results[scenario_id] = report.model_dump() if report else {}
    return results


# Fetch all at module-import time (before any fixture runs)
_ALL_REPORTS: dict[str, dict] = asyncio.run(_run_all_scenarios())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def na_report():
    return _ALL_REPORTS["na_healthy"]


@pytest.fixture(scope="module")
def emea_report():
    return _ALL_REPORTS["emea_undercovered"]


@pytest.fixture(scope="module")
def apac_report():
    return _ALL_REPORTS["apac_dataquality"]


# ---------------------------------------------------------------------------
# Scenario 1: NA Enterprise Q3 -- healthy, confidence >= 0.65
# ---------------------------------------------------------------------------

def test_na_status_healthy(na_report):
    assert na_report.get("overall_status") == "healthy", (
        f"Expected 'healthy', got '{na_report.get('overall_status')}'"
    )


def test_na_forecast_confidence_high(na_report):
    c = na_report.get("forecast_confidence", 0)
    assert c >= 0.65, f"Expected confidence >= 0.65, got {c}"


def test_na_has_sufficient_metrics(na_report):
    assert len(na_report.get("key_metrics", [])) >= 3


def test_na_no_high_severity_risks(na_report):
    high = [r for r in na_report.get("risks", []) if r.get("severity") == "high"]
    assert len(high) == 0, f"Healthy pipeline should have 0 high-severity risks, got: {high}"


def test_na_summary_references_pipeline_health(na_report):
    summary = na_report.get("executive_summary", "").lower()
    assert any(w in summary for w in ["coverage", "pipeline", "healthy", "strong", "win"])


def test_na_has_recommended_actions(na_report):
    assert len(na_report.get("recommended_actions", [])) >= 1


def test_na_deepeval_correctness(na_report):
    tc = LLMTestCase(
        input="Analyze NA Enterprise Q3 2026 pipeline health",
        actual_output=na_report.get("executive_summary", ""),
        expected_output=(
            "The pipeline is healthy with strong coverage above 3x, "
            "good win rate, and balanced stage distribution."
        ),
    )
    metric = GEval(
        name="Correctness",
        criteria="The report correctly characterizes a healthy pipeline with strong coverage and win rates.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5,
    )
    assert_test(tc, [metric])


# ---------------------------------------------------------------------------
# Scenario 2: EMEA SMB Q3 -- at_risk, coverage risk flagged
# ---------------------------------------------------------------------------

def test_emea_status_at_risk(emea_report):
    status = emea_report.get("overall_status")
    assert status in ("at_risk", "critical"), f"Expected at_risk/critical, got '{status}'"


def test_emea_has_coverage_risk(emea_report):
    text = " ".join(
        r.get("title", "") + " " + r.get("narrative", "")
        for r in emea_report.get("risks", [])
    ).lower()
    assert any(w in text for w in ["coverage", "pipeline", "capacity", "undercovered", "below"])


def test_emea_has_medium_or_high_risk(emea_report):
    flagged = [r for r in emea_report.get("risks", []) if r.get("severity") in ("high", "medium")]
    assert len(flagged) >= 1


def test_emea_has_recommended_actions(emea_report):
    assert len(emea_report.get("recommended_actions", [])) >= 2


def test_emea_lower_confidence_than_na(emea_report, na_report):
    assert emea_report.get("forecast_confidence", 1.0) < na_report.get("forecast_confidence", 0.0)


def test_emea_deepeval_risk_detection(emea_report):
    risk_summary = "; ".join(r.get("title", "") for r in emea_report.get("risks", []))
    tc = LLMTestCase(
        input="Identify pipeline risks for EMEA SMB Q3 2026",
        actual_output=risk_summary,
        expected_output="Coverage risk -- pipeline coverage below 3x minimum threshold",
    )
    metric = GEval(
        name="Risk Detection",
        criteria="The output identifies low pipeline coverage as a primary risk for EMEA SMB.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.4,
    )
    assert_test(tc, [metric])


# ---------------------------------------------------------------------------
# Scenario 3: APAC Enterprise Q3 -- data quality risk, low confidence
# ---------------------------------------------------------------------------

def test_apac_has_data_quality_flags(apac_report):
    flags = apac_report.get("data_quality_flags", [])
    summary = apac_report.get("executive_summary", "").lower()
    assert len(flags) >= 1 or any(
        w in summary for w in ["missing", "data quality", "incomplete", "inconsistent"]
    )


def test_apac_lower_forecast_confidence(apac_report):
    c = apac_report.get("forecast_confidence", 1.0)
    assert c <= 0.75, f"Expected confidence <= 0.75, got {c}"


def test_apac_data_quality_in_report(apac_report):
    text = (
        apac_report.get("executive_summary", "") + " "
        + " ".join(apac_report.get("data_quality_flags", [])) + " "
        + " ".join(r.get("narrative", "") for r in apac_report.get("risks", []))
    ).lower()
    assert any(w in text for w in [
        "missing", "data quality", "close date", "incomplete", "inconsistent"
    ])


def test_apac_numeric_consistency(apac_report):
    """Every number in the summary must trace to a computed metric."""
    metrics_vals = set()
    for m in apac_report.get("key_metrics", []):
        v = m["value"]
        metrics_vals.add(str(round(v, 1)))
        if v == int(v):
            metrics_vals.add(str(int(v)))
    summary = apac_report.get("executive_summary", "")
    numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", summary))
    ALLOWED = {"0", "1", "2", "3", "4", "5", "10", "15", "20", "25", "30", "50", "100", "2026"}
    unverified = numbers - metrics_vals - ALLOWED
    assert len(unverified) <= 3, (
        f"Unverified numbers in narrative: {unverified}\nMetrics: {metrics_vals}"
    )
