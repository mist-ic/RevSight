"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useEffect } from "react";
import { useAgentStream } from "@/hooks/use-agent-stream";
import { AgentReasoningChain } from "@/components/agent/reasoning-chain";
import { ReportViewer } from "@/components/dashboard/report-viewer";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Zap } from "lucide-react";

const NODE_LABELS: Record<string, string> = {
  ingest: "Loading pipeline data",
  compute_metrics: "Computing metrics via SQL",
  assess_risks: "Assessing pipeline risks",
  generate_narrative: "Generating report narrative",
  governance: "Running governance check",
};

function NewReportContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const scenario_id = searchParams.get("scenario_id") ?? "na_healthy";
  const quarter = searchParams.get("quarter") ?? "Q3-2026";
  const region = searchParams.get("region") ?? "NA";
  const segment = searchParams.get("segment") ?? "Enterprise";
  const persona = searchParams.get("persona") ?? "cro";

  const { isStreaming, events, tokenBuffer, activeNode, report, error, runId, start } =
    useAgentStream();

  useEffect(() => {
    start({ scenario_id, quarter, region, segment, persona });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const nodeSteps = ["ingest", "compute_metrics", "assess_risks", "generate_narrative", "governance"];
  const currentNodeIndex = activeNode ? nodeSteps.indexOf(activeNode) : -1;

  return (
    <div className="min-h-screen p-8" style={{ background: "hsl(var(--background))" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8 animate-fade-in">
        <div>
          <Button
            variant="ghost"
            className="mb-3 -ml-2 text-sm"
            style={{ color: "hsl(var(--muted-foreground))" }}
            onClick={() => router.push("/")}
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Back to scenarios
          </Button>
          <h1 className="text-2xl font-bold">
            {region} {segment} {quarter}
          </h1>
          <p className="text-sm mt-1" style={{ color: "hsl(var(--muted-foreground))" }}>
            Persona: <span className="capitalize font-medium text-white">{persona}</span>
            {runId && (
              <span className="ml-3 mono text-xs opacity-60">
                Run: {runId.slice(0, 8)}
              </span>
            )}
          </p>
        </div>

        {isStreaming && (
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium animate-pulse-glow"
            style={{
              background: "hsla(217, 91%, 60%, 0.1)",
              border: "1px solid hsla(217, 91%, 60%, 0.3)",
              color: "hsl(var(--primary))",
            }}
          >
            <Zap className="w-4 h-4 animate-spin-slow" />
            {activeNode ? NODE_LABELS[activeNode] ?? activeNode : "Starting agents..."}
          </div>
        )}
      </div>

      {error && (
        <div
          className="rounded-xl p-4 mb-6 text-sm"
          style={{
            background: "hsla(0, 79%, 63%, 0.1)",
            border: "1px solid hsla(0, 79%, 63%, 0.3)",
            color: "hsl(var(--critical))",
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Agent reasoning chain */}
        <div className="xl:col-span-1">
          {/* Progress stepper */}
          <div
            className="rounded-2xl p-5 mb-4"
            style={{
              background: "hsl(var(--card))",
              border: "1px solid var(--glass-border)",
            }}
          >
            <p
              className="text-xs font-semibold uppercase tracking-wider mb-4"
              style={{ color: "hsl(var(--muted-foreground))" }}
            >
              Agent Pipeline
            </p>
            <div className="space-y-3">
              {nodeSteps.map((node, i) => {
                const isDone = i < currentNodeIndex || (!isStreaming && report);
                const isActive = node === activeNode;
                return (
                  <div key={node} className="flex items-center gap-3">
                    <div
                      className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                      style={{
                        background: isDone
                          ? "hsl(var(--healthy))"
                          : isActive
                          ? "hsl(var(--primary))"
                          : "hsl(var(--secondary))",
                        color: isDone || isActive ? "white" : "hsl(var(--muted-foreground))",
                      }}
                    >
                      {isDone ? "✓" : i + 1}
                    </div>
                    <span
                      className="text-sm"
                      style={{
                        color: isActive
                          ? "hsl(var(--foreground))"
                          : isDone
                          ? "hsl(var(--healthy))"
                          : "hsl(var(--muted-foreground))",
                        fontWeight: isActive ? 600 : 400,
                      }}
                    >
                      {NODE_LABELS[node]}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tool calls */}
          <AgentReasoningChain events={events} tokenBuffer={tokenBuffer} isStreaming={isStreaming} />
        </div>

        {/* Right: Report or streaming skeleton */}
        <div className="xl:col-span-2">
          {report ? (
            <ReportViewer report={report} persona={persona as any} />
          ) : isStreaming ? (
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <Skeleton
                  key={i}
                  className="w-full rounded-2xl"
                  style={{ height: i === 0 ? 120 : 80, background: "hsl(var(--card))" }}
                />
              ))}
            </div>
          ) : (
            <div
              className="rounded-2xl p-8 text-center"
              style={{ background: "hsl(var(--card))", border: "1px solid var(--glass-border)" }}
            >
              <p style={{ color: "hsl(var(--muted-foreground))" }}>
                Waiting for report...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function NewReportPage() {
  return (
    <Suspense fallback={<div className="p-8"><Skeleton className="h-32 w-full rounded-2xl" /></div>}>
      <NewReportContent />
    </Suspense>
  );
}
