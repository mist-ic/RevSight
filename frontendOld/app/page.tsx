"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, TrendingUp, AlertTriangle, Database, ChevronRight, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LivePipelineChart } from "@/components/dashboard/live-pipeline-chart";
import type { Persona, Scenario } from "@/lib/types";

const SCENARIOS: Scenario[] = [
  {
    id: "na_healthy",
    label: "NA Enterprise Q3",
    region: "NA",
    segment: "Enterprise",
    quarter: "Q3-2026",
    health: "healthy",
    description:
      "Strong pipeline with 4.2x coverage. Balanced stage distribution and clean data. " +
      "Expected outcome: healthy classification with high confidence.",
    tags: ["4.2x Coverage", "28% Win Rate", "62 day velocity"],
  },
  {
    id: "emea_undercovered",
    label: "EMEA SMB Q3",
    region: "EMEA",
    segment: "SMB",
    quarter: "Q3-2026",
    health: "at_risk",
    description:
      "Pipeline coverage at 1.8x with top-heavy stage distribution. " +
      "High Discovery volume, thin Negotiation. SDR capacity risk flagged.",
    tags: ["1.8x Coverage", "18% Win Rate", "85 day velocity"],
  },
  {
    id: "apac_dataquality",
    label: "APAC Enterprise Q3",
    region: "APAC",
    segment: "Enterprise",
    quarter: "Q3-2026",
    health: "critical",
    description:
      "Nominal 3.1x pipeline but 30% missing close dates and inconsistent stage names " +
      "undermine forecasting confidence. Data quality is the primary risk.",
    tags: ["3.1x Nominal", "30% Missing Dates", "Low Confidence"],
  },
];

const PERSONAS: { value: Persona; label: string; description: string }[] = [
  { value: "cro", label: "CRO", description: "Executive summary + forecast" },
  { value: "revops", label: "RevOps Lead", description: "Metric drill-down + actions" },
  { value: "engineer", label: "Data Engineer", description: "Agent traces + tool calls" },
];

const healthConfig = {
  healthy: { color: "var(--status-good)", bg: "rgba(47, 111, 58, 0.1)", label: "Healthy" },
  at_risk: { color: "var(--accent)", bg: "rgba(212, 107, 35, 0.1)", label: "At Risk" },
  critical: { color: "var(--chart-4)", bg: "rgba(166, 66, 25, 0.1)", label: "Critical" },
};

const healthIcon = {
  healthy: TrendingUp,
  at_risk: AlertTriangle,
  critical: AlertTriangle,
};

export default function HomePage() {
  const router = useRouter();
  const [selectedPersona, setSelectedPersona] = useState<Persona>("cro");
  const [loading, setLoading] = useState<string | null>(null);

  function handleGenerate(scenario: Scenario) {
    setLoading(scenario.id);
    const params = new URLSearchParams({
      scenario_id: scenario.id,
      quarter: scenario.quarter,
      region: scenario.region,
      segment: scenario.segment,
      persona: selectedPersona,
    });
    router.push(`/reports/new?${params.toString()}`);
  }

  return (
    <div className="min-h-screen p-8 bg-background">
      {/* Header */}
      <div className="mb-12 animate-fade-in">
        <div className="flex items-center gap-2 mb-3">
          <div className="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
            Revenue Command Copilot
          </div>
        </div>
        <h1 className="text-4xl font-bold mb-3 font-serif text-foreground">
          Pipeline Health{" "}
          <span className="text-primary font-serif">Intelligence</span>
        </h1>
        <p className="text-muted-foreground max-w-[520px] leading-relaxed">
          Select a scenario and persona to run an AI-powered pipeline analysis.
          Watch the agent reasoning chain in real time, then explore the structured report.
        </p>
      </div>

      {/* Persona Selector */}
      <div className="mb-10 animate-fade-in" style={{ animationDelay: "0.1s" }}>
        <p className="text-xs font-semibold uppercase tracking-wider mb-3 text-muted-foreground">
          <Users className="w-3.5 h-3.5 inline mr-1.5" />
          View as Persona
        </p>
        <div className="flex gap-2">
          {PERSONAS.map((p) => {
            const active = selectedPersona === p.value;
            return (
              <button
                key={p.value}
                onClick={() => setSelectedPersona(p.value)}
                className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 text-left border ${
                  active
                    ? "bg-primary/10 border-primary/40 text-primary shadow-sm"
                    : "bg-surface border-border text-foreground hover:bg-muted"
                }`}
              >
                <div className="font-semibold">{p.label}</div>
                <div className="text-xs mt-0.5 opacity-80">
                  {p.description}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 stagger">
        {SCENARIOS.map((scenario) => {
          const cfg = healthConfig[scenario.health];
          const Icon = healthIcon[scenario.health];
          const isLoading = loading === scenario.id;

          return (
            <div
              key={scenario.id}
              className="fusion-card cursor-pointer group hover:-translate-y-1 hover:shadow-[4px_6px_0px_var(--border)] transition-all"
            >
              {/* Status badge */}
              <div className="flex items-center justify-between mb-5">
                <div
                  className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold"
                  style={{ background: cfg.bg, color: cfg.color }}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {cfg.label}
                </div>
                <div className="text-xs font-medium px-2 py-1 rounded bg-secondary text-muted-foreground">
                  {scenario.region} - {scenario.segment}
                </div>
              </div>

              {/* Title */}
              <h2 className="text-xl font-semibold mb-2 text-foreground font-serif border-none pb-0">
                {scenario.label}
              </h2>
              <p className="text-sm mb-5 leading-relaxed text-muted-foreground">
                {scenario.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mb-6">
                {scenario.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2.5 py-1 rounded-md font-medium border border-border bg-white"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Live chart (Placeholder or Component) */}
              <div className="mb-8 border-t border-border pt-6">
                <LivePipelineChart scenarioId={scenario.id} />
              </div>

              {/* CTA */}
              <Button
                className="w-full group/btn bg-foreground text-background hover:bg-primary transition-colors h-11"
                onClick={() => handleGenerate(scenario)}
                disabled={!!loading}
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Zap className="w-4 h-4 animate-spin-slow" />
                    Starting analysis...
                  </span>
                ) : (
                  <span className="flex items-center gap-2 font-semibold">
                    Generate Report
                    <ChevronRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" />
                  </span>
                )}
              </Button>
            </div>
          );
        })}
      </div>

      {/* Stats bar */}
      <div
        className="mt-12 rounded-lg p-6 flex items-center gap-8 animate-fade-in border border-border bg-card shadow-sm"
        style={{
          animationDelay: "0.3s",
        }}
      >
        {[
          { label: "Agent Nodes", value: "5", icon: Zap },
          { label: "SQL Templates", value: "12", icon: Database },
          { label: "Guardrail Layer", value: "Active", icon: TrendingUp },
          { label: "Observability", value: "LangSmith + Logfire", icon: AlertTriangle },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-center gap-3">
            <Icon className="w-4 h-4 text-primary" />
            <div>
              <div className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">
                {label}
              </div>
              <div className="text-sm font-semibold text-foreground">{value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
