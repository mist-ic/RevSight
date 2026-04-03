"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
  RadialBarChart,
  RadialBar,
} from "recharts";
import type { MetricSummary } from "@/lib/types";

// ── Coverage vs Target Chart ─────────────────────────────────────────────────
type CoverageData = { stage: string; value: number; target: number };

const COVERAGE_COLORS = {
  healthy: "hsl(142, 71%, 45%)",
  at_risk: "hsl(38, 92%, 50%)",
  critical: "hsl(0, 79%, 63%)",
};

function coverageColor(value: number, target: number) {
  const ratio = value / target;
  if (ratio >= 1) return COVERAGE_COLORS.healthy;
  if (ratio >= 0.7) return COVERAGE_COLORS.at_risk;
  return COVERAGE_COLORS.critical;
}

export function CoverageChart({ metrics }: { metrics: MetricSummary[] }) {
  // Build coverage data from key_metrics
  const coverageMetric = metrics.find(
    (m) => m.metric_id === "coverage" || m.name.toLowerCase().includes("coverage")
  );
  const winRateMetric = metrics.find(
    (m) => m.metric_id === "win_rate" || m.name.toLowerCase().includes("win")
  );
  const conversionMetric = metrics.find(
    (m) => m.metric_id === "conversion" || m.name.toLowerCase().includes("conversion")
  );
  const velocityMetric = metrics.find(
    (m) => m.metric_id === "velocity" || m.name.toLowerCase().includes("velocity")
  );

  const data: { name: string; value: number; target: number; unit: string }[] = [
    {
      name: "Coverage",
      value: coverageMetric?.value ?? 0,
      target: 3,
      unit: "x",
    },
    {
      name: "Win Rate",
      value: winRateMetric?.value ?? 0,
      target: 25,
      unit: "%",
    },
    {
      name: "Conversion",
      value: conversionMetric?.value ?? 0,
      target: 20,
      unit: "%",
    },
  ].filter((d) => d.value > 0);

  if (data.length === 0) return null;

  // Normalize to % of target for comparison
  const normalized = data.map((d) => ({
    name: d.name,
    actual: Math.round((d.value / d.target) * 100),
    target: 100,
    label: `${d.value.toFixed(1)}${d.unit}`,
    color: coverageColor(d.value, d.target),
  }));

  return (
    <div>
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-3"
        style={{ color: "hsl(var(--muted-foreground))" }}
      >
        Metrics vs Target
      </p>
      <ResponsiveContainer width="100%" height={140}>
        <BarChart data={normalized} layout="vertical" margin={{ left: 60, right: 40, top: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="hsla(0,0%,100%,0.05)" />
          <XAxis
            type="number"
            domain={[0, 140]}
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `${v}%`}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11, fill: "hsl(var(--foreground))" }}
            tickLine={false}
            axisLine={false}
            width={56}
          />
          <Tooltip
            cursor={{ fill: "hsla(0,0%,100%,0.04)" }}
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid var(--glass-border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(val, _, props) => [`${props.payload.label} (${val}% of target)`, ""]}
          />
          <ReferenceLine x={100} stroke="hsla(0,0%,100%,0.2)" strokeDasharray="3 3" />
          <Bar dataKey="actual" radius={4} maxBarSize={20}>
            {normalized.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Forecast Confidence Gauge ─────────────────────────────────────────────────
export function ForecastGauge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 70
      ? COVERAGE_COLORS.healthy
      : pct >= 45
      ? COVERAGE_COLORS.at_risk
      : COVERAGE_COLORS.critical;

  const data = [{ value: pct, fill: color }, { value: 100 - pct, fill: "hsla(0,0%,100%,0.06)" }];

  return (
    <div className="flex flex-col items-center">
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-2"
        style={{ color: "hsl(var(--muted-foreground))" }}
      >
        Forecast Confidence
      </p>
      <div className="relative">
        <RadialBarChart
          width={110}
          height={70}
          cx={55}
          cy={65}
          innerRadius={40}
          outerRadius={58}
          startAngle={180}
          endAngle={0}
          data={data}
        >
          <RadialBar dataKey="value" cornerRadius={4} />
        </RadialBarChart>
        <div
          className="absolute inset-0 flex items-end justify-center pb-1"
          style={{ pointerEvents: "none" }}
        >
          <span className="text-xl font-bold" style={{ color }}>
            {pct}%
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Stage Conversion Funnel ───────────────────────────────────────────────────
const STAGE_ORDER = ["Discovery", "Demo", "Proposal", "Negotiation", "Closed Won"];

export function ConversionFunnelChart({
  stageData,
}: {
  stageData: { stage_name: string; deal_count: number; total_value: number }[];
}) {
  if (!stageData || stageData.length === 0) return null;

  const sorted = STAGE_ORDER.map((name) => {
    const match = stageData.find((s) =>
      s.stage_name.toLowerCase().includes(name.toLowerCase())
    );
    return { name, count: match?.deal_count ?? 0 };
  }).filter((s) => s.count > 0);

  const maxCount = Math.max(...sorted.map((s) => s.count), 1);

  return (
    <div>
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-3"
        style={{ color: "hsl(var(--muted-foreground))" }}
      >
        Stage Conversion
      </p>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={sorted} margin={{ top: 4, bottom: 4 }}>
          <CartesianGrid vertical={false} stroke="hsla(0,0%,100%,0.05)" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            cursor={{ fill: "hsla(0,0%,100%,0.04)" }}
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid var(--glass-border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(val) => [`${val} deals`, "Count"]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={40}>
            {sorted.map((entry, i) => {
              const ratio = entry.count / maxCount;
              const alpha = 0.4 + ratio * 0.6;
              return <Cell key={i} fill={`hsla(217, 91%, 60%, ${alpha})`} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
