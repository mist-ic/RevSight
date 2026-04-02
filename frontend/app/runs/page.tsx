"use client";

import { useEffect, useState } from "react";
import { listRuns } from "@/lib/api";
import type { Run } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { Activity, Clock, ChevronRight } from "lucide-react";

const STATUS_CONFIG = {
  done: { label: "Done", color: "hsl(var(--healthy))", bg: "hsla(142, 71%, 45%, 0.1)" },
  running: { label: "Running", color: "hsl(var(--primary))", bg: "hsla(217, 91%, 60%, 0.1)" },
  pending: { label: "Pending", color: "hsl(var(--at-risk))", bg: "hsla(38, 92%, 50%, 0.1)" },
  failed: { label: "Failed", color: "hsl(var(--critical))", bg: "hsla(0, 79%, 63%, 0.1)" },
};

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listRuns(50, 0)
      .then((data) => setRuns(data.runs ?? []))
      .catch(() => setRuns([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen p-8" style={{ background: "hsl(var(--background))" }}>
      <div className="mb-8 animate-fade-in">
        <h1 className="text-3xl font-bold mb-2">
          Agent <span className="gradient-text">Runs</span>
        </h1>
        <p style={{ color: "hsl(var(--muted-foreground))" }}>
          Full audit trail of every pipeline analysis run. Click any row to view the report.
        </p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" style={{ background: "hsl(var(--card))" }} />
          ))}
        </div>
      ) : runs.length === 0 ? (
        <div
          className="rounded-2xl p-12 text-center"
          style={{ background: "hsl(var(--card))", border: "1px solid var(--glass-border)" }}
        >
          <Activity className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="font-medium mb-1">No runs yet</p>
          <p className="text-sm" style={{ color: "hsl(var(--muted-foreground))" }}>
            Generate a report from the home page to see run history here.
          </p>
        </div>
      ) : (
        <div className="space-y-3 stagger">
          {runs.map((run) => {
            const cfg = STATUS_CONFIG[run.status] ?? STATUS_CONFIG.pending;
            const durationMs = run.completed_at
              ? new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()
              : null;

            return (
              <Link
                key={run.id}
                href={`/reports/${run.id}`}
                className="block rounded-xl p-5 hover-lift group"
                style={{
                  background: "hsl(var(--card))",
                  border: "1px solid var(--glass-border)",
                  textDecoration: "none",
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ background: cfg.bg }}
                    >
                      <Activity className="w-4 h-4" style={{ color: cfg.color }} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm">
                          {run.region} {run.segment} {run.quarter}
                        </p>
                        {run.persona && (
                          <span
                            className="text-xs capitalize px-2 py-0.5 rounded"
                            style={{
                              background: "hsl(var(--secondary))",
                              color: "hsl(var(--muted-foreground))",
                            }}
                          >
                            {run.persona}
                          </span>
                        )}
                      </div>
                      <div
                        className="flex items-center gap-3 text-xs mt-0.5 mono"
                        style={{ color: "hsl(var(--muted-foreground))" }}
                      >
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(run.created_at).toLocaleString()}
                        </span>
                        {durationMs !== null && (
                          <span>{(durationMs / 1000).toFixed(1)}s</span>
                        )}
                        <span className="opacity-60">{run.id.slice(0, 8)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span
                      className="text-xs font-semibold px-2.5 py-1 rounded-full"
                      style={{ background: cfg.bg, color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                    <ChevronRight
                      className="w-4 h-4 transition-transform group-hover:translate-x-0.5"
                      style={{ color: "hsl(var(--muted-foreground))" }}
                    />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
