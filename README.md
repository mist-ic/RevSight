# RevSight

**Revenue Command Copilot** -- AI-powered pipeline health analysis for CROs, RevOps leads, and data engineers.

Pick a scenario, watch the agent pipeline execute in real time, and get a structured QBR-ready report with risks, actions, and deterministic metrics.

---

## What It Does

RevSight runs a multi-agent pipeline that:

1. **Loads pipeline data** from a CRM-modeled PostgreSQL database (3 pre-seeded scenarios)
2. **Computes all metrics via SQL** -- coverage, conversion, velocity, slippage, deal aging
3. **Classifies risks** using threshold-based heuristics then LLM-enriched narratives
4. **Generates a structured report** with an executive summary, KPIs, risks, and recommended actions
5. **Validates the output** with a guardrail that checks every narrative number against the computed metrics
6. **Logs the full run** to an audit trail with per-agent step timing

The LLM never invents numbers. Every numeric value in the report is traceable to a SQL query result.

---

## Architecture

```
User Request
    |
    v
[ LangGraph Orchestrator ]
    |
    +-- ingest       -> Pydantic AI agent loads pipeline snapshot from PostgreSQL
    |
    +-- metrics      -> Pydantic AI agent runs 5 SQL templates (coverage, conversion, velocity, slippage, aging)
    |
    +-- risk         -> Heuristic thresholds + LLM narrative enrichment
    |
    +-- narrative    -> Pydantic AI agent generates PipelineHealthReport (anti-hallucination enforced)
    |       |
    |       v
    |   [Guardrail Check] -- if numeric mismatch, retry narrative (max 2 times)
    |
    +-- governance   -> Audit log + auto-approve (demo) or interrupt for HITL (production)
    |
    v
Structured JSON Report -> SSE stream to Next.js -> Rendered dashboard
```

**Observability:** LangSmith traces every graph node. Logfire instruments every Pydantic AI agent run.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Orchestration | LangGraph v1.x |
| Agent Nodes | Pydantic AI |
| Backend API | FastAPI |
| Database | Neon PostgreSQL |
| Frontend | Next.js 16 + shadcn/ui |
| Charts | Recharts |
| Observability | LangSmith + Pydantic Logfire |
| LLM Gateway | LiteLLM (primary: GPT-4o, fallback: Claude) |
| Evaluation | DeepEval |
| Package Manager | uv |
| Deployment | Railway |

---

## Framework Selection

**Why LangGraph over AutoGen/CrewAI?**

- **Durable state machine** -- the TypedDict state persists across all nodes with typed reducers
- **Native HITL** -- `interrupt()` pauses the graph for human approval without any extra plumbing
- **Cycle support** -- the guardrail retry loop (narrative -> guardrail check -> narrative) is a native graph cycle, not a workaround
- **LangSmith integration** -- zero-config full-graph tracing including subgraph calls and interrupt/resume events
- **PostgreSQL checkpointer** -- durable execution that survives restarts

AutoGen was moved to maintenance mode by Microsoft in October 2025. CrewAI is strong for fast role-based prototypes but lacks native cycle/interrupt primitives for this kind of validation loop.

---

## Scenarios

| Scenario | Region | Segment | Health | Key Signal |
|---|---|---|---|---|
| NA Enterprise Q3 | NA | Enterprise | Healthy | 4.2x coverage, 28% win rate, clean data |
| EMEA SMB Q3 | EMEA | SMB | At Risk | 1.8x coverage, top-heavy stage distribution |
| APAC Enterprise Q3 | APAC | Enterprise | Critical | 30% missing close dates, inconsistent stages |

---

## Guardrails

Every number in the narrative is checked against the computed metrics JSON. If the LLM includes an unverified number, the output is rejected and the narrative agent is re-prompted with the validation error in context (max 2 retries).

In production mode (`REQUIRE_APPROVAL=true`), the governance node pauses execution via `interrupt()` and waits for a human to approve or reject before the report is stored.

---

## Running Locally

### Prerequisites

- Python 3.12+
- Node 20+
- uv (`pip install uv`)
- A Neon PostgreSQL database
- OpenAI API key

### Backend

```bash
cp .env.example .env
# Fill in your DATABASE_URL and OPENAI_API_KEY

cd backend
uv sync
python -m app.db.seed        # Seed the 3 demo scenarios
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

### Docker Compose

```bash
cp .env.example .env
# Fill in your keys
docker compose up --build
```

---

## Project Structure

```
RevSight/
-- backend/
   -- app/
      -- agents/          LangGraph graph + 4 Pydantic AI agent nodes
      -- api/routes/      FastAPI endpoints (reports, metrics, runs, stream)
      -- core/            Guardrails + audit trail
      -- db/              PostgreSQL connection, migrations, seed, SQL templates
-- frontend/
   -- app/                Next.js App Router pages
   -- components/         Dashboard + agent visualization components
   -- hooks/              useAgentStream SSE hook
   -- lib/                API client + shared types
-- Dockerfile.backend
-- Dockerfile.frontend
-- docker-compose.yml
-- .env.example
```

---

## Evaluation

DeepEval tests verify:
- Healthy scenario classified as healthy with confidence > 0.70
- Under-covered scenario flags coverage risk with SDR recommendations
- Data quality scenario identifies missing close dates as primary risk
- All numbers in narrative match the computed metrics JSON

---

## Governance

Every run is logged to the `runs` and `agent_steps` tables with full timing. Proposed reports are written to `audit_actions` before approval. In production mode, the governance node pauses the graph and waits for a human to review before the report is stored or returned.

---

## Production Path

- MCP server for PostgreSQL access (Phase 4)
- A2A Agent Card at `/.well-known/agent.json` (Phase 4)
- NeMo Guardrails for input topic filtering (Phase 4)
- dbt semantic layer replacing materialized views (Phase 4)
- HITL approval UI with live interrupt/resume (Phase 4)
