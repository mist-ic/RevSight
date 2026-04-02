"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend
} from "recharts";

type StageRow = {
  stage_name: string;
  deal_count: number;
  total_arr: number;
  avg_probability: number;
};

type Props = { data: StageRow[] };

const STAGE_COLORS: Record<string, string> = {
  Discovery:   "#3b82f6",
  Demo:        "#8b5cf6",
  Proposal:    "#f59e0b",
  Negotiation: "#10b981",
  "Closed Won": "#22c55e",
  "Closed Lost": "#ef4444",
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg p-3 text-xs"
      style={{
        background: "hsl(222 47% 12%)",
        border: "1px solid var(--glass-border)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      }}
    >
      <p className="font-semibold mb-2">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.dataKey === "total_arr"
            ? `$${(p.value / 1e6).toFixed(1)}M`
            : p.value}
        </p>
      ))}
    </div>
  );
};

export function PipelineChart({ data }: Props) {
  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: "hsl(var(--card))",
        border: "1px solid var(--glass-border)",
      }}
    >
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-4"
        style={{ color: "hsl(var(--muted-foreground))" }}
      >
        Pipeline by Stage
      </p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255,255,255,0.05)"
            vertical={false}
          />
          <XAxis
            dataKey="stage_name"
            tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "hsl(215 20% 55%)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `$${(v / 1e6).toFixed(1)}M`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="total_arr" name="Pipeline ARR" radius={[4, 4, 0, 0]}>
            {data.map((row) => (
              <Cell
                key={row.stage_name}
                fill={STAGE_COLORS[row.stage_name] ?? "#6366f1"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
