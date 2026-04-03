"use client";

import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const data = [
  { name: "DSCV", value: 45, color: "var(--chart-1)" },
  { name: "DEMO", value: 30, color: "var(--chart-2)" },
  { name: "PROP", value: 15, color: "var(--chart-3)" },
  { name: "NEGO", value: 8, color: "var(--chart-4)" },
  { name: "CLSD", value: 12, color: "var(--status-good)" }
];

export function LivePipelineChart({ scenarioId }: { scenarioId?: string }) {
  return (
    <div className="h-[200px] w-full mt-auto">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
          <XAxis 
            dataKey="name" 
            axisLine={{ stroke: "var(--border)" }} 
            tickLine={false} 
            tick={{ fill: "var(--text-muted)", fontSize: 9, fontFamily: "var(--font-mono)", fontWeight: "bold" }} 
            dy={16}
          />
          <Tooltip 
            cursor={{ fill: "rgba(255,255,255,0.05)" }}
            contentStyle={{ 
              backgroundColor: "#000", 
              border: "1px solid var(--border)",
              borderRadius: "0",
              fontFamily: "var(--font-mono)",
              fontSize: "10px",
              color: "#fff",
              textTransform: "uppercase",
              padding: "12px"
            }}
            itemStyle={{ color: "var(--accent)" }}
          />
          <Bar dataKey="value" animationDuration={800}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
