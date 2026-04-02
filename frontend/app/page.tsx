"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, TrendingUp, AlertTriangle, Database, ChevronRight, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  healthy: { color: "hsl(var(--healthy))", bg: "hsla(142, 71%, 45%, 0.1)", label: "Healthy" },
  at_risk: { color: "hsl(var(--at-risk))", bg: "hsla(38, 92%, 50%, 0.1)", label: "At Risk" },
  critical: { color: "hsl(var(--critical))", bg: "hsla(0, 79%, 63%, 0.1)", label: "Critical" },
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
    <div className="min-h-screen p-8" style={{ background: "hsl(var(--background))" }}>
      {/* Header */}
      <div className="mb-12 animate-fade-in">
        <div className="flex items-center gap-2 mb-3">
          <div
            className="px-3 py-1 rounded-full text-xs font-medium"
            style={{
              background: "hsla(217, 91%, 60%, 0.1)",
              color: "hsl(var(--primary))",
              border: "1px solid hsla(217, 91%, 60%, 0.2)",
            }}
          >
            Revenue Command Copilot
          </div>
        </div>
        <h1
          className="text-4xl font-bold mb-3"
          style={{ letterSpacing: "-0.02em" }}
        >
          Pipeline Health{" "}
          <span className="gradient-text">Intelligence</span>
        </h1>
        <p style={{ color: "hsl(var(--muted-foreground))", maxWidth: "520px", lineHeight: "1.6" }}>
          Select a scenario and persona to run an AI-powered pipeline analysis.
          Watch the agent reasoning chain in real time, then explore the structured report.
        </p>
      </div>

      {/* Persona Selector */}
      <div className="mb-10 animate-fade-in" style={{ animationDelay: "0.1s" }}>
        <p
          className="text-xs font-semibold uppercase tracking-wider mb-3"
          style={{ color: "hsl(var(--muted-foreground))" }}
        >
          <Users className="w-3.5 h-3.5 inline mr-1.5" />
          View as Persona
        </p>
        <div className="flex gap-2">
          {PERSONAS.map((p) => (
            <button
              key={p.value}
              onClick={() => setSelectedPersona(p.value)}
              className="px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 text-left"
              style={{
                background:
                  selectedPersona === p.value
                    ? "hsla(217, 91%, 60%, 0.15)"
                    : "hsl(var(--card))",
                border:
                  selectedPersona === p.value
                    ? "1px solid hsla(217, 91%, 60%, 0.4)"
                    : "1px solid var(--glass-border)",
                color:
                  selectedPersona === p.value
                    ? "hsl(var(--primary))"
                    : "hsl(var(--foreground))",
              }}
            >
              <div className="font-semibold">{p.label}</div>
              <div
                className="text-xs mt-0.5"
                style={{ color: "hsl(var(--muted-foreground))" }}
              >
                {p.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 stagger">
        {SCENARIOS.map((scenario) => {
          const cfg = healthConfig[scenario.health];
          const Icon = healthIcon[scenario.health];
          const isLoading = loading === scenario.id;

          return (
            <div
              key={scenario.id}
              className="rounded-2xl p-6 hover-lift cursor-pointer group"
              style={{
                background: "var(--gradient-card)",
                border: "1px solid var(--glass-border)",
              }}
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
                <div
                  className="text-xs font-medium px-2 py-1 rounded"
                  style={{
                    background: "hsl(var(--secondary))",
                    color: "hsl(var(--muted-foreground))",
                  }}
                >
                  {scenario.region} - {scenario.segment}
                </div>
              </div>

              {/* Title */}
              <h2
                className="text-lg font-semibold mb-2"
                style={{ color: "hsl(var(--foreground))" }}
              >
                {scenario.label}
              </h2>
              <p
                className="text-sm mb-5 leading-relaxed"
                style={{ color: "hsl(var(--muted-foreground))" }}
              >
                {scenario.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mb-6">
                {scenario.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2.5 py-1 rounded-md font-medium"
                    style={{
                      background: "hsl(var(--secondary))",
                      color: "hsl(var(--foreground))",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* CTA */}
              <Button
                className="w-full group/btn"
                onClick={() => handleGenerate(scenario)}
                disabled={!!loading}
                style={{
                  background: isLoading ? "hsl(var(--secondary))" : "var(--gradient-brand)",
                  border: "none",
                  color: "white",
                  fontWeight: 600,
                }}
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Zap className="w-4 h-4 animate-spin-slow" />
                    Starting analysis...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    Generate Report
                    <ChevronRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-0.5" />
                  </span>
                )}
              </Button>
            </div>
          );
        })}
      </div>

      {/* Stats bar */}
      <div
        className="mt-12 rounded-2xl p-6 flex items-center gap-8 animate-fade-in"
        style={{
          background: "hsl(var(--card))",
          border: "1px solid var(--glass-border)",
          animationDelay: "0.3s",
        }}
      >
        {[
          { label: "Agent Nodes", value: "5", icon: Zap },
          { label: "SQL Templates", value: "5", icon: Database },
          { label: "Guardrail Layer", value: "Active", icon: TrendingUp },
          { label: "Observability", value: "LangSmith + Logfire", icon: AlertTriangle },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-center gap-3">
            <Icon className="w-4 h-4" style={{ color: "hsl(var(--primary))" }} />
            <div>
              <div className="text-xs" style={{ color: "hsl(var(--muted-foreground))" }}>
                {label}
              </div>
              <div className="text-sm font-semibold">{value}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
