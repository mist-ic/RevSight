# Governance and Guardrails

## Overview

RevSight applies two layers of governance to every pipeline run:

1. **Numeric Guardrails** -- automated, runs inline during report generation
2. **Audit Trail** -- every run, step, and proposed action logged before any approval

---

## Numeric Consistency Guardrail

The core anti-hallucination mechanism.

**What it does:**
Every number appearing in the narrative (`executive_summary`, `risks[].narrative`) is extracted using regex and compared against the computed `MetricResult` values from the SQL-computed metrics.

**Implementation:**
```python
# app/core/guardrails.py
def check_numeric_consistency(report: PipelineHealthReport, metrics: list[MetricResult]) -> bool:
    metric_values = {str(m.value) for m in metrics}
    metric_values |= {str(round(m.value, 1)) for m in metrics}

    numbers_in_text = extract_numbers(report.executive_summary)
    for risk in report.risks:
        numbers_in_text |= extract_numbers(risk.narrative)

    # Allow common constants that don't need to come from metrics
    ALLOWED_CONSTANTS = {"1", "2", "3", "100", "0", str(datetime.now().year), ...}
    unverified = numbers_in_text - metric_values - ALLOWED_CONSTANTS

    if unverified:
        log.warning(f"Unverified numbers in narrative: {unverified}")
        return False
    return True
```

**Retry behavior:**
- If the check fails, the `narrative_retry_count` in state is incremented
- The narrative node is re-invoked with the validation error in context:
  `"The following numbers appeared in your output but were not found in the metrics: {unverified}. Revise."`
- Maximum 2 retries (3 total attempts). After that, the report is accepted with the flag logged.

---

## Audit Trail

Every run writes three layers of records:

| Table | When written | What it contains |
|---|---|---|
| `runs` | On request start | run_id, persona, filters, status=pending |
| `agent_steps` | After each node completes | agent_name, input_hash, output_hash, duration_ms |
| `audit_actions` | Before governance approval | action_type, full report_json payload |
| `runs` | On completion | status=done, report_json, completed_at |

The `input_hash` and `output_hash` on `agent_steps` are SHA-256 hashes of the serialized Pydantic model inputs/outputs. This allows reconstruction of exactly what each agent saw and produced, without storing full payloads for every step.

---

## HITL Approval (Production Mode)

Set `REQUIRE_APPROVAL=true` in environment to enable.

**Flow:**
```
governance node
    |
    | interrupt()  -- pauses the LangGraph execution checkpoint
    |
    v
POST /api/runs/{run_id}/approve  (human reviews via UI or API)
    |
    | LangGraph resumes from checkpoint
    |
    v
Report stored, status = done
```

**In demo mode** (`REQUIRE_APPROVAL=false`, default):
The governance node auto-approves and logs `reviewer=system`.

---

## Data Quality Flags

The ingest agent checks for:
- Percentage of deals with missing `close_date` (flags if > 10%)
- Inconsistent stage names (fuzzy match against canonical list)
- Deals with `amount = 0` or `amount = NULL`
- Duplicate `opportunity_id` values

Flags are stored in `PipelineHealthReport.data_quality_flags` and surfaced in the dashboard UI.

---

## Persona-Based Views

The governance and narrative nodes are persona-aware:

| Persona | Report emphasis | Risk threshold |
|---|---|---|
| `cro` | Executive summary, forecast confidence, top 2 actions | Conservative (flags medium+ risks) |
| `revops` | Full metrics table, all risks, detailed actions with owner/timeline | Detailed (all risk severities shown) |
| `engineer` | Agent trace, tool call inputs/outputs, guardrail events, metric IDs | Raw (no filtering) |
