# RevSight - Revenue Command Copilot

<div align="center">

**AI-powered pipeline health analysis for CROs, RevOps leads, and data engineers.**

Pick a scenario → watch a multi-agent AI pipeline execute in real time → get a QBR-ready report with risks, actions, and SQL-computed metrics.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-%E2%86%92-22c55e?style=for-the-badge)](https://revsight-frontend-ski7hmysfa-el.a.run.app)
[![Backend API](https://img.shields.io/badge/Backend%20API-%E2%86%92-3b82f6?style=for-the-badge)](https://revsight-backend-ski7hmysfa-el.a.run.app/health)
[![Deploy](https://img.shields.io/github/actions/workflow/status/mist-ic/RevSight/deploy.yml?label=Deploy&style=for-the-badge)](https://github.com/mist-ic/RevSight/actions)

</div>

---

## What it does

RevSight runs a 5-node LangGraph pipeline on every request:

1. **Ingest** - Loads a pipeline snapshot from PostgreSQL (opportunities, stages, activities, targets)
2. **Compute Metrics** - Pydantic AI agent runs 5 parameterized SQL templates (coverage, conversion, velocity, slippage, deal aging). The LLM never computes numbers.
3. **Assess Risks** - Threshold heuristics classify risks (coverage < 3x, stage aging > 45 days, account concentration) - LLM adds narrative context only
4. **Generate Narrative** - Pydantic AI agent writes a structured `PipelineHealthReport`. Numeric guardrail rejects the output and retries if any number doesn't match the metrics JSON
5. **Governance** - Logs the proposed report to the audit trail; auto-approves in demo mode, pauses for HITL in production (`REQUIRE_APPROVAL=true`)

Every step streams to the frontend via SSE as it happens.

---

## Live Demo

> **Frontend:** https://revsight-frontend-ski7hmysfa-el.a.run.app
>
> **Backend API:** https://revsight-backend-ski7hmysfa-el.a.run.app

> [!NOTE]
> Deployed on Google Cloud Run with scale-to-zero. First request after idle takes ~3–5 seconds to cold-start.

### Try these scenarios

| Scenario | What to expect |
|---|---|
| **NA Enterprise Q3** | Healthy pipeline - 4.2x coverage, 28% win rate, clean data |
| **EMEA SMB Q3** | At-risk - 1.8x coverage, top-heavy stage distribution, SDR recommendations |
| **APAC Enterprise Q3** | Critical - 30% missing close dates, data quality flagged as primary risk |

---

## Architecture

```
User Request (Next.js)
        │
        ▼
  POST /api/reports/stream
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph Orchestrator                   │
│                                                       │
│  ┌─────────┐   ┌─────────┐   ┌──────┐               │
│  │ Ingest  │──▶│ Metrics │──▶│ Risk │               │
│  │ (Pyd AI)│   │ (Pyd AI)│   │      │               │
│  └─────────┘   └─────────┘   └──┬───┘               │
│                                  │                    │
│  ┌────────────┐   ┌──────────┐  │                   │
│  │ Governance │◀──│Narrative │◀─┘                   │
│  │ (audit +   │   │ (Pyd AI) │                       │
│  │  approve)  │   └────┬─────┘                       │
│  └─────┬──────┘        │ Guardrail check              │
│        │               │ (retry up to 2x)             │
└────────┼───────────────┼─────────────────────────────┘
         │               │
         ▼               ▼
   Neon PostgreSQL    SSE stream → Next.js
   (audit trail)     (step events + tokens)
```

**Key design principle:** SQL computes all numbers. LLM interprets, narrates, and recommends. Guardrail enforces this at runtime.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **Orchestration** | LangGraph v1.x | Durable state machine, native `interrupt()` for HITL, cycle support for guardrail retries |
| **Agent Nodes** | Pydantic AI | Structured output with full Pydantic validation, type-safe tool calls |
| **LLM** | Gemini 3 Flash Preview | Fast, cost-effective, 1M context window |
| **Backend API** | FastAPI | Async-native, SSE support, automatic OpenAPI docs |
| **Database** | Neon PostgreSQL | Serverless Postgres, connection pooling, Singapore region |
| **Frontend** | Next.js 16 + shadcn/ui | App Router, standalone Docker output, SSE streaming |
| **Charts** | Recharts | Composable, dark-mode compatible |
| **Deployment** | Google Cloud Run | Scale-to-zero, ~$0/month for portfolio traffic |
| **CI/CD** | GitHub Actions | Path-based: backend changes only rebuild backend, frontend changes only rebuild frontend |
| **Package Manager** | uv | 10–100× faster than pip |

---

## Why LangGraph over AutoGen / CrewAI

| Feature | LangGraph | AutoGen | CrewAI |
|---|---|---|---|
| Durable typed state | ✅ TypedDict with reducers | ❌ | ❌ |
| Native HITL interrupt | ✅ `interrupt()` built-in | ❌ workaround | ❌ workaround |
| Graph cycles (retry loops) | ✅ first-class | ⚠️ complex | ❌ |
| PostgreSQL checkpointing | ✅ | ❌ | ❌ |
| LangSmith tracing | ✅ zero-config | ❌ | ❌ |
| Status (2026) | Active | ⚠️ Maintenance mode¹ | Active |

> ¹ Microsoft moved AutoGen to maintenance mode October 2025.

The guardrail → narrative retry loop is a native graph cycle. HITL is a single `interrupt()` call. These would require significant workarounds in the alternatives.

---

## Running Locally

### Prerequisites
- Python 3.12+, Node 20+, `uv` (`pip install uv`)
- Neon PostgreSQL database
- Gemini API key

### Backend

```bash
cd backend
cp ../.env.example .env
# Fill in DATABASE_URL and GEMINI_API_KEY

uv sync
python -m uv run python app/db/seed.py   # Seed the 3 demo scenarios
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/reports` | Run full pipeline, returns report JSON |
| `GET` | `/api/reports/{run_id}` | Fetch a stored report |
| `POST` | `/api/reports/stream` | Run pipeline with SSE streaming (real-time step events) |
| `GET` | `/api/metrics/pipeline` | Raw pipeline metrics for charts |
| `GET` | `/api/runs` | Paginated audit trail of all runs |

Full interactive docs: https://revsight-backend-ski7hmysfa-el.a.run.app/docs

---

## Guardrails

Every narrative number is cross-checked against the metrics JSON before the report is accepted:

```python
# core/guardrails.py
def check_numeric_consistency(report, metrics) -> bool:
    metric_values = {str(m.value) for m in metrics}
    numbers_in_text = extract_numbers(report.executive_summary)
    unverified = numbers_in_text - metric_values - ALLOWED_CONSTANTS
    if unverified:
        return False  # triggers narrative retry
    return True
```

If the check fails, the narrative node is re-invoked with the validation error in context (max 2 retries). The governance node logs every proposed report to the `audit_actions` table before approval.

---

## Deployment

Deployed on Google Cloud Run (`asia-south1`) with GitHub Actions CI/CD:

- **Scale-to-zero** - 0 instances at idle, auto-scales on request
- **Secrets** - `GEMINI_API_KEY` and `DATABASE_URL` stored in GCP Secret Manager, mounted at runtime
- **Path-based CI** - push to `backend/**` only rebuilds and redeploys the backend; push to `frontend/**` only rebuilds the frontend
- **Force deploy** via CLI: `gh workflow run deploy.yml -f deploy_backend=true`

---

## Project Structure

```
RevSight/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph graph + 5 Pydantic AI nodes
│   │   │   ├── graph.py     # 5-node pipeline with guardrail retry loop
│   │   │   ├── state.py     # TypedDict state with Annotated reducers
│   │   │   └── nodes/       # ingest, metrics, risk, narrative, governance
│   │   ├── api/routes/      # FastAPI: reports, metrics, runs, stream (SSE)
│   │   ├── core/            # guardrails.py + audit.py
│   │   └── db/              # asyncpg pool, migrations, seed, SQL templates
│   └── test_backend.py      # 6 integration tests (all pass)
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # Dashboard, agent reasoning chain, report viewer
│   ├── hooks/               # useAgentStream SSE streaming hook
│   └── lib/                 # Typed API client + shared types
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions: path-filtered Cloud Run deploy
├── backend/Dockerfile       # Cloud Run-ready, uses $PORT
├── frontend/Dockerfile      # Next.js standalone build
└── cloudbuild.yaml          # Manual Cloud Build trigger (optional)
```

---

## Phase 4 Roadmap (not yet implemented)

- [ ] **MCP Server** - expose PostgreSQL as a Model Context Protocol server, replace direct SQL tools with MCP client calls
- [ ] **A2A Agent Card** - publish `/.well-known/agent.json` for agent interoperability
- [ ] **NeMo Guardrails** - input topic filtering + PII scrubbing via Colang rails
- [ ] **dbt Semantic Layer** - replace materialized views with governed dbt models
- [ ] **HITL Approval UI** - wire `interrupt()` to WebSocket for live approve/reject in the browser
- [ ] **PDF Export** - react-pdf QBR report download
