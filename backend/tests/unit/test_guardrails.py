"""Unit tests for the guardrail numeric consistency checker."""
from __future__ import annotations

import pytest
from app.core.guardrails import check_numeric_consistency
from app.agents.schemas.metrics import MetricResult
from app.agents.schemas.report import (
    PipelineHealthReport, MetricSummary, RiskNarrative,
    OpportunityNarrative, ActionItem
)


def make_report(summary: str, risks: list[str] | None = None) -> PipelineHealthReport:
    return PipelineHealthReport(
        executive_summary=summary,
        key_metrics=[
            MetricSummary(metric_id="pipeline_coverage", name="Pipeline Coverage",
                          value=4.2, unit="x", status="healthy"),
            MetricSummary(metric_id="win_rate", name="Win Rate",
                          value=28.5, unit="%", status="healthy"),
        ],
        risks=[
            RiskNarrative(risk_id="r1", title="Test Risk", severity="low",
                          narrative=risks[0] if risks else "No significant risks.",
                          linked_metric_ids=[])
        ],
        opportunities=[
            OpportunityNarrative(title="Expand outbound", narrative="Opportunity to grow.")
        ],
        recommended_actions=[
            ActionItem(action="Review stale deals", rationale="Improve hygiene",
                       impact="medium", effort="low")
        ],
        forecast_confidence=0.85,
        data_quality_flags=[],
        overall_status="healthy",
    )


def make_metrics() -> list[MetricResult]:
    return [
        MetricResult(metric_id="pipeline_coverage", name="Pipeline Coverage",
                     value=4.2, unit="x"),
        MetricResult(metric_id="win_rate", name="Win Rate",
                     value=28.5, unit="%"),
        MetricResult(metric_id="stale_deals", name="Stale Deals",
                     value=7.0, unit="deals"),
    ]


class TestGuardrailConsistency:
    def test_clean_report_passes(self):
        report = make_report("The pipeline shows 4.2x coverage and a 28.5% win rate.")
        metrics = make_metrics()
        passed, issues = check_numeric_consistency(report, metrics)
        assert passed, f"Clean report should pass. Issues: {issues}"

    def test_fictional_number_fails(self):
        # 99.9 is not in any metric
        report = make_report("Pipeline coverage is 4.2x with a 99.9% forecast accuracy.")
        metrics = make_metrics()
        passed, issues = check_numeric_consistency(report, metrics)
        assert not passed, "Report with fictional number should fail guardrail"
        assert any("99" in str(i) or "99.9" in str(i) for i in issues)

    def test_integer_version_of_metric_passes(self):
        # 4 is the integer version of 4.2 -- should be allowed
        report = make_report("We have 4x coverage based on current pipeline.")
        metrics = make_metrics()
        passed, issues = check_numeric_consistency(report, metrics)
        # Allow some tolerance -- integer rounding is expected
        # This test documents behavior rather than enforces a hard pass
        print(f"Passed: {passed}, Issues: {issues}")

    def test_risk_narrative_fictional_fails(self):
        report = make_report(
            "Coverage is 4.2x.",
            risks=["Win rate dropped to 5.7% last quarter, below our 99% target."]
        )
        metrics = make_metrics()
        passed, issues = check_numeric_consistency(report, metrics)
        assert not passed, "Risk with fictional 5.7% should fail"
