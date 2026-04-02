// Shared TypeScript types mirroring backend Pydantic models

export type Persona = "cro" | "revops" | "engineer";

export type Scenario = {
  id: string;
  label: string;
  region: string;
  segment: string;
  quarter: string;
  description: string;
  health: "healthy" | "at_risk" | "critical";
  tags: string[];
};

export type MetricResult = {
  metric_id: string;
  name: string;
  value: number;
  unit: string;
  segment: string;
  comparison?: number;
  trend?: "up" | "down" | "flat";
};

export type RiskSeverity = "high" | "medium" | "low";

export type RiskNarrative = {
  risk_id: string;
  title: string;
  severity: RiskSeverity;
  narrative: string;
  linked_metric_ids: string[];
};

export type ActionItem = {
  action: string;
  rationale: string;
  impact: "high" | "medium" | "low";
  effort: "high" | "medium" | "low";
  owner?: string;
  timeline?: string;
};

export type MetricSummary = {
  metric_id: string;
  name: string;
  value: number;
  unit: string;
  status: "healthy" | "at_risk" | "critical";
};

export type PipelineHealthReport = {
  executive_summary: string;
  key_metrics: MetricSummary[];
  risks: RiskNarrative[];
  opportunities: Array<{ title: string; narrative: string; potential_arr_impact?: number }>;
  recommended_actions: ActionItem[];
  forecast_confidence: number;
  data_quality_flags: string[];
  overall_status: "healthy" | "at_risk" | "critical" | "unknown";
};

export type RunStatus = "pending" | "running" | "done" | "failed";

export type Run = {
  id: string;
  persona?: string;
  quarter?: string;
  region?: string;
  segment?: string;
  scenario_id?: string;
  status: RunStatus;
  created_at: string;
  completed_at?: string;
};

export type AgentEvent =
  | { type: "run_started"; run_id: string }
  | { type: "step"; node: string }
  | { type: "tool_start"; name: string; input: string }
  | { type: "tool_end"; name: string; output: string }
  | { type: "token"; content: string }
  | { type: "done"; run_id: string; report: PipelineHealthReport | null }
  | { type: "error"; message: string };
