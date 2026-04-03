# Architecture

## System Overview

RevSight is a multi-agent AI pipeline that analyzes sales pipeline health and generates QBR-ready reports. The system is built on three principles:

1. **Deterministic metrics** -- SQL computes all numbers. LLM only interprets and narrates.
2. **Structured output** -- Every agent produces typed Pydantic models, validated before passing to the next node.
3. **Auditable execution** -- Every run, step, and proposed action is logged to PostgreSQL before any approval.

---

## Component Diagram

```
Browser (Next.js)
     |
     | POST /api/reports/stream  (SSE)
     |
     v
FastAPI (Cloud Run :8080)
     |
     +-- auth, CORS, rate limit
     |
     v
LangGraph Pipeline
     |
     +-- [ingest]          Pydantic AI agent
     |       |
     |       | Tools: load_pipeline_snapshot(), load_deal_activity()
     |       | Output: IngestionResult (raw data slice)
     |
     +-- [compute_metrics] Pydantic AI agent
     |       |
     |       | Tools: run_coverage_sql(), run_conversion_sql(),
     |       |        run_velocity_sql(), run_slippage_sql(), run_aging_sql()
     |       | Output: list[MetricResult]
     |
     +-- [assess_risks]    Heuristic + LLM enrichment
     |       |
     |       | Thresholds: coverage < 3x, aging > 45d, concentration > 40%
     |       | Output: list[RiskObject]
     |
     +-- [generate_narrative] Pydantic AI agent
     |       |
     |       | Guardrail: every number must match MetricResult values
     |       | Retry: up to 2x on numeric mismatch
     |       | Output: PipelineHealthReport
     |
     +-- [governance]      Audit + approval
             |
             | Logs to: audit_actions table
             | Demo mode: auto-approve
             | Prod mode: interrupt() for HITL
             |
             v
         Neon PostgreSQL (runs, agent_steps, audit_actions tables)
```

---

## Data Flow

```
Request: { quarter, region, segment, persona, scenario_id }
     |
     v
[ingest]
     SELECT * FROM opportunities WHERE region=? AND segment=? AND quarter=?
     SELECT * FROM pipeline_stage_history WHERE ...
     SELECT * FROM activities WHERE deal_id IN (...)
     |
     v
[compute_metrics]
     Run 5 SQL templates in parallel:
       coverage.sql  -> pipeline_coverage (ratio)
       conversion.sql -> stage_conversion_rates (per stage)
       velocity.sql  -> avg_days_to_close (by segment)
       slippage.sql  -> pct_slipped_close_dates
       aging.sql     -> deal_count_by_age_bucket (per stage)
     |
     v
[assess_risks]
     Heuristic checks on MetricResult values:
       if coverage < 3.0: create RiskObject(severity=high, ...)
       if conversion[stage2->stage3] < 30%: create RiskObject(...)
       if aging[negotiation][>45d] > 20%: create RiskObject(...)
     LLM adds narrative context to each risk
     |
     v
[generate_narrative]
     Prompt: "Given metrics={...} and risks={...}, write a PipelineHealthReport.
              Only reference numbers that appear in the metrics JSON."
     Guardrail: extract all numbers from output, verify against metric values
     If mismatch: re-prompt with error context (max 2 retries)
     |
     v
[governance]
     INSERT INTO audit_actions (run_id, action_type='report_proposed', payload=report_json)
     if REQUIRE_APPROVAL=false: UPDATE runs SET status='done'
     if REQUIRE_APPROVAL=true: interrupt() -- wait for human API call
```

---

## Database Schema

```sql
-- Core CRM data (seeded, read-only for agents)
users, accounts, contacts, opportunities
pipeline_stage_history, activities

-- Materialized view (pre-aggregated for fast chart queries)
mv_pipeline_metrics (stage_name, deal_count, total_value, avg_age, quarter, region, segment)

-- Audit trail (append-only)
runs          (id, persona, quarter, region, segment, scenario_id, status, created_at, completed_at, report_json)
agent_steps   (id, run_id, agent_name, input_hash, output_hash, duration_ms, created_at)
audit_actions (id, run_id, action_type, payload, status, reviewed_by, created_at)
```

---

## SSE Streaming Protocol

```
Event format (per SSE spec):
  data: {"type": "...", ...}\r\n\r\n

Event types:
  run_started   { run_id }
  step          { node: "ingest" | "compute_metrics" | "assess_risks" | "generate_narrative" | "governance" }
  tool_start    { name, input (truncated) }
  tool_end      { name, output (truncated) }
  token         { content }   -- streamed narrative tokens
  done          { run_id, report: PipelineHealthReport }
  error         { message }
```

---

## Deployment

| Service | Platform | Region | Config |
|---|---|---|---|
| Backend | GCP Cloud Run | asia-south1 | min=0, max=2, memory=512Mi, timeout=300s |
| Frontend | GCP Cloud Run | asia-south1 | min=0, max=2, memory=512Mi, timeout=60s |
| Database | Neon PostgreSQL | ap-southeast-1 | serverless, auto-suspend |
| Secrets | GCP Secret Manager | global | GEMINI_API_KEY, DATABASE_URL |
| CI/CD | GitHub Actions | -- | path-filtered: backend/ and frontend/ deploy independently |
