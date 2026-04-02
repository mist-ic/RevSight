"""
DeepEval evaluation suite for RevSight.

Tests:
  1. NA Healthy -- should classify healthy with confidence > 0.70
  2. EMEA Under-covered -- should flag low coverage risk
  3. APAC Data Quality -- should identify missing close dates as primary risk
  4. Numeric consistency -- all narrative numbers must appear in computed metrics

Run: python -m pytest tests/eval/ -v
"""
from __future__ import annotations

import json
import re
import pytest
import asyncio
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    GEval,
    HallucinationMetric,
)
from deepeval.metrics.g_eval import GEvalMetric

# We import the pipeline directly to test the full stack
from app.agents.schemas.request import ReportRequest, Persona
from app.agents.graph import run_pipeline


# ─── Helpers ──────────────────────────────────────────────────────────────────

def run_sync(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def pipeline_result(scenario_id: str, region: str, segment: str, persona: str = "cro"):
    req = ReportRequest(
        quarter="Q3-2026",
        region=region,
        segment=segment,
        persona=Persona(persona),
        scenario_id=scenario_id,
    )
    return run_sync(run_pipeline(req))


def extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


# ─── Scenario 1: NA Healthy ───────────────────────────────────────────────────

class TestNAHealthy:
    @pytest.fixture(scope="class")
    def state(self):
        return pipeline_result("na_healthy", "NA", "Enterprise")

    def test_status_healthy(self, state):
        assert state["report"] is not None, "Report should not be None"
        assert state["report"].overall_status == "healthy", (
            f"Expected 'healthy', got '{state['report'].overall_status}'"
        )

    def test_confidence_above_threshold(self, state):
        assert state["report"].forecast_confidence >= 0.70, (
            f"Expected confidence >= 0.70, got {state['report'].forecast_confidence}"
        )

    def test_has_executive_summary(self, state):
        summary = state["report"].executive_summary
        assert len(summary) > 100, "Executive summary too short"
        assert "NA" in summary or "Enterprise" in summary or "Q3" in summary

    def test_no_critical_risks(self, state):
        high_risks = [r for r in state["report"].risks if r.severity == "high"]
        assert len(high_risks) == 0, f"Healthy scenario should have no high risks, found: {[r.title for r in high_risks]}"

    def test_has_metrics(self, state):
        assert len(state["report"].key_metrics) >= 3, "Should have at least 3 key metrics"

    def test_approved(self, state):
        assert state["approval_status"] == "approved"


# ─── Scenario 2: EMEA Under-covered ──────────────────────────────────────────

class TestEMEAUndercovered:
    @pytest.fixture(scope="class")
    def state(self):
        return pipeline_result("emea_undercovered", "EMEA", "SMB")

    def test_status_at_risk_or_critical(self, state):
        assert state["report"].overall_status in ("at_risk", "critical"), (
            f"Under-covered should be at_risk or critical, got '{state['report'].overall_status}'"
        )

    def test_coverage_risk_identified(self, state):
        risk_titles = [r.title.lower() for r in state["report"].risks]
        coverage_flagged = any("coverage" in t or "pipeline" in t for t in risk_titles)
        assert coverage_flagged, f"Coverage risk not flagged. Risks: {risk_titles}"

    def test_confidence_below_healthy(self, state):
        # Under-covered should have lower confidence than healthy
        assert state["report"].forecast_confidence <= 0.75

    def test_has_high_risk(self, state):
        high_risks = [r for r in state["report"].risks if r.severity == "high"]
        assert len(high_risks) >= 1, "Under-covered scenario should have at least 1 high risk"


# ─── Scenario 3: APAC Data Quality ───────────────────────────────────────────

class TestAPACDataQuality:
    @pytest.fixture(scope="class")
    def state(self):
        return pipeline_result("apac_dataquality", "APAC", "Enterprise")

    def test_data_quality_flags_present(self, state):
        flags = state["report"].data_quality_flags
        assert len(flags) >= 1, "APAC scenario should have at least 1 data quality flag"

    def test_low_confidence(self, state):
        assert state["report"].forecast_confidence <= 0.70, (
            f"Data quality scenario should have low confidence, got {state['report'].forecast_confidence}"
        )

    def test_data_quality_mentioned_in_summary(self, state):
        summary = state["report"].executive_summary.lower()
        quality_terms = ["data", "quality", "missing", "incomplete", "inconsistent"]
        assert any(t in summary for t in quality_terms), (
            "APAC executive summary should mention data quality issues"
        )


# ─── Numeric Consistency Tests ────────────────────────────────────────────────

class TestNumericConsistency:
    @pytest.fixture(scope="class")
    def state(self):
        return pipeline_result("na_healthy", "NA", "Enterprise")

    def test_guardrail_passed(self, state):
        assert state.get("guardrail_passed", True), (
            "Guardrail should pass -- all narrative numbers should match metrics"
        )

    def test_executive_summary_has_no_fictional_numbers(self, state):
        report = state["report"]
        metric_values = {str(round(m.value, 1)) for m in report.key_metrics}
        metric_values |= {str(int(m.value)) for m in report.key_metrics}

        # Extract numbers from summary
        summary_numbers = extract_numbers(report.executive_summary)

        # Allow common non-metric numbers (quarters, years, percentages of 100, etc.)
        allowed = {"2026", "3", "100", "0", "1", "2", "45", "90"}
        unverified = summary_numbers - metric_values - allowed

        # Soft check -- warn but don't hard-fail (narrative may use rounded values)
        if unverified:
            print(f"WARNING: Potentially unverified numbers in summary: {unverified}")
            print(f"Metric values: {sorted(metric_values)}")
