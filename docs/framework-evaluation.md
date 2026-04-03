# Framework Evaluation: LangGraph vs AutoGen vs CrewAI

## Decision: LangGraph v1.x

RevSight requires a framework that can:
1. Maintain typed, durable state across 5 sequential agent nodes
2. Support a retry cycle (narrative -> guardrail check -> narrative)
3. Pause mid-execution for human approval (HITL) without losing state
4. Provide zero-config observability into every node and sub-agent call

LangGraph satisfies all four. No other evaluated framework does.

---

## Comparison Table

| Capability | LangGraph | AutoGen | CrewAI |
|---|---|---|---|
| **Typed state machine** | TypedDict with Annotated reducers | No formal state contract | No formal state contract |
| **Graph cycles** | Native (conditional edges) | Workaround (nested conversations) | Not supported natively |
| **HITL interrupt** | `interrupt()` built-in, resumes from checkpoint | Manual event loop manipulation | No native interrupt |
| **Durable checkpointing** | PostgreSQL/SQLite checkpointer (built-in) | No | No |
| **Structured output validation** | Composable with Pydantic AI | Requires custom wiring | Requires custom wiring |
| **Full graph tracing** | LangSmith (zero-config) | No equivalent | No equivalent |
| **Sub-graph support** | Native | No | No |
| **Maintenance status (2026)** | Active, Google DeepMind-backed | Maintenance mode (Oct 2025) | Active |

---

## Why Not AutoGen

Microsoft moved AutoGen to maintenance mode in October 2025. The project has been superseded by AutoGen Studio and a partial rewrite (AutoGen 0.4+), but the framework lacks:

- A formal state machine abstraction (agents communicate via message queues, not typed reducers)
- Native cycle support (loops require nested conversation structures)
- PostgreSQL checkpointing for durable execution

In the context of RevSight, the guardrail retry loop (`narrative -> guardrail check -> narrative`) would require a custom event loop or recursive agent call in AutoGen -- a significant workaround for something LangGraph does natively with a conditional edge.

---

## Why Not CrewAI

CrewAI excels at role-based multi-agent workflows with parallel task execution. It is a good fit for "crew of specialists working in parallel." RevSight's pipeline is sequential and stateful, not parallel and role-based.

Specific gaps for this use case:
- No native `interrupt()` for HITL -- requires an external event system
- No typed state: agents communicate via string outputs, requiring manual parsing
- No graph cycles: retry loops require a new Crew instantiation
- No checkpointing: if a node fails after 2 minutes of compute, execution restarts from the beginning

---

## Why Pydantic AI for Agent Nodes

LangGraph provides orchestration but is agnostic about how individual nodes are implemented. Pydantic AI is used for each node because:

- **Type-safe tool calls** -- tools are defined with full type annotations, validated before execution
- **Structured output** -- `output_type=PipelineHealthReport` guarantees the LLM output conforms to the schema before the node returns
- **Composable with LangGraph** -- Pydantic AI `Agent.run()` is just an async function, compatible with any LangGraph node definition
- **Dependency injection** -- `RunContext[deps_type]` passes the DB connection and state to tools without global state

---

## Production Upgrade Path

If this system moves to production, the main evolution would be:

1. **Replace direct SQL tools with MCP** -- a Model Context Protocol server wraps the PostgreSQL read-only connection, allowing any MCP-compatible orchestrator to query the same data source without code changes
2. **Replace `run_metric_query()` with dbt metrics** -- the dbt semantic layer exposes named metrics (`pipeline_coverage`, `win_rate`) with governance, versioning, and caching
3. **Add NeMo Guardrails** -- input topic filtering (block non-RevOps questions), output rails (Colang-defined behavior constraints)
4. **Publish an A2A Agent Card** -- `/.well-known/agent.json` describes RevSight's skills (`analyze-pipeline`, `generate-qbr`) for agent-to-agent interoperability
