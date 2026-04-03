"use client";

import type { PipelineHealthReport, MetricSummary, Persona } from "@/lib/types";
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PipelineChart } from "./pipeline-chart";
import { CoverageChart, ForecastGauge } from "./metric-charts";

type Props = {
  report: PipelineHealthReport;
  persona: Persona;
};

const STATUS_COLORS = {
  healthy: { color: "hsl(var(--healthy))", bg: "hsla(142, 71%, 45%, 0.1)", label: "Healthy" },
  at_risk: { color: "hsl(var(--at-risk))", bg: "hsla(38, 92%, 50%, 0.1)", label: "At Risk" },
  critical: { color: "hsl(var(--critical))", bg: "hsla(0, 79%, 63%, 0.1)", label: "Critical" },
  unknown: { color: "hsl(var(--muted-foreground))", bg: "hsl(var(--secondary))", label: "Unknown" },
};

const SEVERITY_COLORS = {
  high: { color: "hsl(var(--critical))", bg: "hsla(0, 79%, 63%, 0.1)" },
  medium: { color: "hsl(var(--at-risk))", bg: "hsla(38, 92%, 50%, 0.1)" },
  low: { color: "hsl(var(--healthy))", bg: "hsla(142, 71%, 45%, 0.1)" },
};

const IMPACT_COLORS = {
  high: "hsl(var(--critical))",
  medium: "hsl(var(--at-risk))",
  low: "hsl(var(--healthy))",
};

function KpiCard({ metric }: { metric: MetricSummary }) {
  const cfg = STATUS_COLORS[metric.status] ?? STATUS_COLORS.unknown;
  return (
    <div
      className="rounded-xl p-4 hover-lift"
      style={{
        background: "hsl(var(--card))",
        border: `1px solid ${cfg.color}33`,
      }}
    >
      <p className="text-xs mb-2" style={{ color: "hsl(var(--muted-foreground))" }}>
        {metric.name}
      </p>
      <p className="text-2xl font-bold" style={{ color: cfg.color }}>
        {typeof metric.value === "number" ? metric.value.toFixed(metric.unit === "x" || metric.unit === "%" ? 1 : 0) : metric.value}
        <span className="text-sm font-normal ml-1">{metric.unit}</span>
      </p>
      <div
        className="mt-2 inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
        style={{ background: cfg.bg, color: cfg.color }}
      >
        {metric.status === "healthy" ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        {cfg.label}
      </div>
    </div>
  );
}

export function ReportViewer({ report, persona }: Props) {
  const statusCfg = STATUS_COLORS[report.overall_status] ?? STATUS_COLORS.unknown;

  const tabs =
    persona === "engineer"
      ? ["summary", "metrics", "risks", "actions"]
      : persona === "revops"
      ? ["summary", "metrics", "risks", "actions"]
      : ["summary", "risks", "actions"];

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Status banner */}
      <div
        className="rounded-2xl p-5 flex items-center justify-between"
        style={{
          background: statusCfg.bg,
          border: `1px solid ${statusCfg.color}44`,
        }}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            {report.overall_status === "healthy" ? (
              <CheckCircle2 className="w-5 h-5" style={{ color: statusCfg.color }} />
            ) : (
              <AlertTriangle className="w-5 h-5" style={{ color: statusCfg.color }} />
            )}
            <span className="font-semibold" style={{ color: statusCfg.color }}>
              {statusCfg.label} Pipeline
            </span>
          </div>
          <p className="text-sm" style={{ color: "hsl(var(--foreground))", opacity: 0.8 }}>
            {report.risks.length} risks &middot; {report.recommended_actions.length} actions
          </p>
        </div>
        <ForecastGauge confidence={report.forecast_confidence} />
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 stagger">
        {report.key_metrics.map((m) => (
          <KpiCard key={m.metric_id} metric={m} />
        ))}
      </div>

      {/* Main tabs */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "hsl(var(--card))",
          border: "1px solid var(--glass-border)",
        }}
      >
        <Tabs defaultValue="summary">
          <div
            className="px-5 pt-4 border-b"
            style={{ borderColor: "var(--glass-border)" }}
          >
            <TabsList
              className="bg-transparent gap-1"
              style={{ background: "transparent" }}
            >
              <TabsTrigger value="summary" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary text-sm">
                Summary
              </TabsTrigger>
              <TabsTrigger value="risks" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary text-sm">
                Risks ({report.risks.length})
              </TabsTrigger>
              <TabsTrigger value="actions" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary text-sm">
                Actions
              </TabsTrigger>
              {(persona === "revops" || persona === "engineer") && (
                <TabsTrigger value="metrics" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary text-sm">
                  Metrics
                </TabsTrigger>
              )}
              {(persona === "revops" || persona === "engineer") && (
                <TabsTrigger value="charts" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary text-sm">
                  Charts
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          {/* Summary */}
          <TabsContent value="summary" className="p-5 space-y-4">
            <CoverageChart metrics={report.key_metrics} />
            <p className="text-sm leading-relaxed" style={{ color: "hsl(var(--foreground))", lineHeight: 1.7 }}>
              {report.executive_summary}
            </p>
            {report.data_quality_flags.length > 0 && (
              <div
                className="rounded-lg p-4"
                style={{
                  background: "hsla(38, 92%, 50%, 0.08)",
                  border: "1px solid hsla(38, 92%, 50%, 0.2)",
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Info className="w-4 h-4" style={{ color: "hsl(var(--at-risk))" }} />
                  <p className="text-sm font-semibold" style={{ color: "hsl(var(--at-risk))" }}>
                    Data Quality Flags
                  </p>
                </div>
                <ul className="space-y-1">
                  {report.data_quality_flags.map((flag, i) => (
                    <li key={i} className="text-sm" style={{ color: "hsl(var(--foreground))", opacity: 0.8 }}>
                      - {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Opportunities */}
            {report.opportunities.length > 0 && (
              <div>
                <p
                  className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: "hsl(var(--muted-foreground))" }}
                >
                  Opportunities
                </p>
                <div className="space-y-3">
                  {report.opportunities.map((opp, i) => (
                    <div
                      key={i}
                      className="rounded-lg p-4"
                      style={{
                        background: "hsl(var(--secondary))",
                        border: "1px solid var(--glass-border)",
                      }}
                    >
                      <p className="font-medium text-sm mb-1">{opp.title}</p>
                      <p className="text-sm" style={{ color: "hsl(var(--muted-foreground))" }}>
                        {opp.narrative}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Risks */}
          <TabsContent value="risks" className="p-5 space-y-3">
            {report.risks.map((risk) => {
              const sev = SEVERITY_COLORS[risk.severity as keyof typeof SEVERITY_COLORS] ??
                SEVERITY_COLORS.low;
              return (
                <div
                  key={risk.risk_id}
                  className="rounded-xl p-4"
                  style={{
                    background: "hsl(var(--secondary))",
                    border: `1px solid ${sev.color}33`,
                  }}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <p className="font-semibold text-sm">{risk.title}</p>
                    <span
                      className="text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase shrink-0"
                      style={{ background: sev.bg, color: sev.color }}
                    >
                      {risk.severity}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed" style={{ color: "hsl(var(--muted-foreground))" }}>
                    {risk.narrative}
                  </p>
                </div>
              );
            })}
          </TabsContent>

          {/* Actions */}
          <TabsContent value="actions" className="p-5 space-y-3">
            {report.recommended_actions.map((action, i) => (
              <div
                key={i}
                className="rounded-xl p-4"
                style={{
                  background: "hsl(var(--secondary))",
                  border: "1px solid var(--glass-border)",
                }}
              >
                <p className="font-semibold text-sm mb-1">{action.action}</p>
                <p className="text-sm mb-3" style={{ color: "hsl(var(--muted-foreground))" }}>
                  {action.rationale}
                </p>
                <div className="flex gap-2 flex-wrap">
                  <span
                    className="text-xs px-2 py-0.5 rounded font-medium"
                    style={{
                      background: `${IMPACT_COLORS[action.impact as keyof typeof IMPACT_COLORS]}22`,
                      color: IMPACT_COLORS[action.impact as keyof typeof IMPACT_COLORS],
                    }}
                  >
                    Impact: {action.impact}
                  </span>
                  <span
                    className="text-xs px-2 py-0.5 rounded font-medium"
                    style={{
                      background: "hsl(var(--muted))",
                      color: "hsl(var(--muted-foreground))",
                    }}
                  >
                    Effort: {action.effort}
                  </span>
                  {action.owner && (
                    <span
                      className="text-xs px-2 py-0.5 rounded"
                      style={{
                        background: "hsl(var(--muted))",
                        color: "hsl(var(--muted-foreground))",
                      }}
                    >
                      Owner: {action.owner}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </TabsContent>

          {/* Metrics detail (RevOps + Engineer only) */}
          {(persona === "revops" || persona === "engineer") && (
            <TabsContent value="metrics" className="p-5">
              <div className="space-y-2">
                {report.key_metrics.map((m) => {
                  const cfg = STATUS_COLORS[m.status] ?? STATUS_COLORS.unknown;
                  return (
                    <div
                      key={m.metric_id}
                      className="flex items-center justify-between p-3 rounded-lg"
                      style={{
                        background: "hsl(var(--secondary))",
                        border: "1px solid var(--glass-border)",
                      }}
                    >
                      <div>
                        <p className="text-sm font-medium">{m.name}</p>
                        <p className="text-xs mono" style={{ color: "hsl(var(--muted-foreground))" }}>
                          {m.metric_id}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold" style={{ color: cfg.color }}>
                          {typeof m.value === "number" ? m.value.toFixed(1) : m.value}
                          <span className="text-sm ml-1">{m.unit}</span>
                        </p>
                        <span
                          className="text-xs px-1.5 py-0.5 rounded"
                          style={{ background: cfg.bg, color: cfg.color }}
                        >
                          {cfg.label}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </TabsContent>
          )}

          {/* Charts tab (RevOps + Engineer) */}
          {(persona === "revops" || persona === "engineer") && (
            <TabsContent value="charts" className="p-5 space-y-6">
              <CoverageChart metrics={report.key_metrics} />
              <div
                className="rounded-xl p-4"
                style={{ background: "hsl(var(--secondary))", border: "1px solid var(--glass-border)" }}
              >
                <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: "hsl(var(--muted-foreground))" }}>
                  All Metrics
                </p>
                <div className="space-y-2">
                  {report.key_metrics.map((m) => {
                    const cfg = STATUS_COLORS[m.status] ?? STATUS_COLORS.unknown;
                    return (
                      <div key={m.metric_id} className="flex items-center justify-between text-sm">
                        <span style={{ color: "hsl(var(--muted-foreground))" }}>{m.name}</span>
                        <span className="font-semibold" style={{ color: cfg.color }}>
                          {typeof m.value === "number" ? m.value.toFixed(1) : m.value}{m.unit}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}
