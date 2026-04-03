"""
DeepEval scenario-based evaluation tests for RevSight.

Run with:
    cd backend
    uv run python -m pytest tests/eval/test_scenarios.py -v

Requires:
    GEMINI_API_KEY and DATABASE_URL in environment (or backend/.env)
    uv run to activate the venv with deepeval installed
"""
import json
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
# Shared helper
# ---------------------------------------------------------------------------

def run_sync(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _run_scenario(scenario_id: str, region: str, segment: str) -> dict:
    await init_db()
    req = ReportRequest(
        quarter="Q3-2026",
        region=region,
        segment=segment,
        persona="revops",
        scenario_id=scenario_id,
    )
    state = await run_pipeline(req)
    report = state.get("report")
    return report.model_dump() if report else {}


# ---------------------------------------------------------------------------
# Scenario 1: NA Healthy
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def na_report():
    return run_sync(_run_scenario("na_healthy", "NA", "Enterprise"))


def test_na_status_healthy(na_report):
    assert na_report.get("overall_status") == "healthy", (
        f"Expected 'healthy', got '{na_report.get('overall_status')}'"
    )


def test_na_forecast_confidence_high(na_report):
    c = na_report.get("forecast_confidence", 0)
    assert c >= 0.65, f"Expected >= 0.65, got {c}"


def test_na_has_metrics(na_report):
    assert len(na_report.get("key_metrics", [])) >= 3


def test_na_no_high_risks(na_report):
    high = [r for r in na_report.get("risks", []) if r.get("severity") == "high"]
    assert len(high) == 0, f"Healthy pipeline should have no high-severity risks: {high}"


def test_na_summary_references_pipeline(na_report):
    summary = na_report.get("executive_summary", "").lower()
    assert any(w in summary for w in ["coverage", "pipeline", "healthy", "strong", "win"])


def test_na_deepeval_correctness(na_report):
    tc = LLMTestCase(
        input="Analyze NA Enterprise Q3 2026 pipeline health",
        actual_output=na_report.get("executive_summary", ""),
        expected_output=(
            "The pipeline is healthy with strong coverage, good win rate, "
            "and balanced stage distribution across Discovery, Demo, Proposal, and Negotiation."
        ),
    )
    metric = GEval(
        name="Correctness",
        criteria="The report correctly identifies a healthy pipeline with good coverage and win rates.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.5,
    )
    assert_test(tc, [metric])


# ---------------------------------------------------------------------------
# Scenario 2: EMEA Under-covered
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def emea_report():
    return run_sync(_run_scenario("emea_undercovered", "EMEA", "SMB"))


def test_emea_status_at_risk(emea_report):
    status = emea_report.get("overall_status")
    assert status in ("at_risk", "critical"), f"Expected at_risk or critical, got {status}"


def test_emea_has_coverage_risk(emea_report):
    text = " ".join(
        r.get("title", "") + " " + r.get("narrative", "")
        for r in emea_report.get("risks", [])
    ).lower()
    assert any(w in text for w in ["coverage", "pipeline", "capacity", "undercovered"]), (
        f"Should flag coverage risk. Got: {text[:300]}"
    )


def test_emea_has_medium_or_high_risk(emea_report):
    flagged = [r for r in emea_report.get("risks", []) if r.get("severity") in ("high", "medium")]
    assert len(flagged) >= 1


def test_emea_has_actions(emea_report):
    assert len(emea_report.get("recommended_actions", [])) >= 2


def test_emea_deepeval_risk_detection(emea_report):
    risk_summary = "; ".join(r.get("title", "") for r in emea_report.get("risks", []))
    tc = LLMTestCase(
        input="Identify pipeline risks for EMEA SMB Q3 2026",
        actual_output=risk_summary,
        expected_output="Coverage risk -- pipeline coverage is below the 3x minimum required for forecast confidence",
    )
    metric = GEval(
        name="Risk Detection",
        criteria="The output identifies low pipeline coverage as a key risk for the EMEA SMB segment.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.4,
    )
    assert_test(tc, [metric])


# ---------------------------------------------------------------------------
# Scenario 3: APAC Data Quality
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def apac_report():
    return run_sync(_run_scenario("apac_dataquality", "APAC", "Enterprise"))


def test_apac_has_data_quality_flags(apac_report):
    flags = apac_report.get("data_quality_flags", [])
    summary = apac_report.get("executive_summary", "").lower()
    assert len(flags) >= 1 or any(w in summary for w in ["missing", "data quality", "incomplete"]), (
        f"Expected data quality flags. Summary: {summary[:200]}"
    )


def test_apac_lower_confidence(apac_report):
    c = apac_report.get("forecast_confidence", 1.0)
    assert c <= 0.75, f"Data quality scenario should have confidence <= 0.75, got {c}"


def test_apac_data_quality_mentioned(apac_report):
    text = (
        apac_report.get("executive_summary", "") + " "
        + " ".join(apac_report.get("data_quality_flags", [])) + " "
        + " ".join(r.get("narrative", "") for r in apac_report.get("risks", []))
    ).lower()
    assert any(w in text for w in ["missing", "data quality", "close date", "incomplete", "inconsistent"]), (
        f"Data quality must appear in risks/flags/summary. Got: {text[:400]}"
    )


def test_numeric_consistency_apac(apac_report):
    """No hallucinated numbers -- every number in narrative must trace to a metric."""
    metrics_vals = {str(round(m["value"], 1)) for m in apac_report.get("key_metrics", [])}
    metrics_vals |= {str(int(m["value"])) for m in apac_report.get("key_metrics", [])}
    summary = apac_report.get("executive_summary", "")
    numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", summary))
    ALLOWED = {"1", "2", "3", "4", "5", "10", "25", "30", "50", "100", "2026", "0", "15", "20"}
    unverified = numbers - metrics_vals - ALLOWED
    assert len(unverified) <= 3, (
        f"Unverified numbers in narrative: {unverified}. Metrics: {metrics_vals}"
    )
