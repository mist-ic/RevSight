"use client";

import type { AgentEvent } from "@/lib/types";
import { Database, CheckCircle2, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";

type Props = {
  events: AgentEvent[];
  tokenBuffer: string;
  isStreaming: boolean;
};

function ToolCallCard({
  name,
  input,
  output,
  status,
}: {
  name: string;
  input?: string;
  output?: string;
  status: "running" | "done";
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="rounded-lg overflow-hidden animate-slide-in"
      style={{
        background: "hsl(var(--secondary))",
        border: "1px solid var(--glass-border)",
      }}
    >
      <button
        className="w-full flex items-center gap-2.5 p-3 text-left"
        onClick={() => setExpanded((x) => !x)}
      >
        <div
          className="w-6 h-6 rounded flex items-center justify-center shrink-0"
          style={{
            background:
              status === "done"
                ? "hsla(142, 71%, 45%, 0.15)"
                : "hsla(217, 91%, 60%, 0.15)",
          }}
        >
          {status === "running" ? (
            <Loader2
              className="w-3.5 h-3.5 animate-spin"
              style={{ color: "hsl(var(--primary))" }}
            />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5" style={{ color: "hsl(var(--healthy))" }} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold mono truncate" style={{ color: "hsl(var(--foreground))" }}>
            {name}
          </p>
        </div>
        {(input || output) && (
          expanded ? (
            <ChevronDown className="w-3.5 h-3.5 shrink-0" style={{ color: "hsl(var(--muted-foreground))" }} />
          ) : (
            <ChevronRight className="w-3.5 h-3.5 shrink-0" style={{ color: "hsl(var(--muted-foreground))" }} />
          )
        )}
      </button>

      {expanded && (input || output) && (
        <div
          className="px-3 pb-3 text-xs mono space-y-1"
          style={{ color: "hsl(var(--muted-foreground))" }}
        >
          {input && (
            <div>
              <span className="font-semibold text-white/50">in: </span>
              <span className="break-all">{input.slice(0, 200)}</span>
            </div>
          )}
          {output && (
            <div>
              <span className="font-semibold text-white/50">out: </span>
              <span className="break-all">{output.slice(0, 300)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function AgentReasoningChain({ events, tokenBuffer, isStreaming }: Props) {
  // Build a merged view of tool_start/tool_end pairs
  const toolMap = new Map<string, { name: string; input?: string; output?: string; done: boolean }>();
  const toolOrder: string[] = [];

  for (const evt of events) {
    if (evt.type === "tool_start") {
      const key = `${evt.name}-${toolOrder.length}`;
      toolMap.set(key, { name: evt.name, input: evt.input, done: false });
      toolOrder.push(key);
    } else if (evt.type === "tool_end") {
      // update last matching tool
      for (let i = toolOrder.length - 1; i >= 0; i--) {
        const key = toolOrder[i];
        const t = toolMap.get(key);
        if (t && t.name === evt.name && !t.done) {
          toolMap.set(key, { ...t, output: evt.output, done: true });
          break;
        }
      }
    }
  }

  const toolCards = toolOrder.map((key) => toolMap.get(key)!);

  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: "hsl(var(--card))",
        border: "1px solid var(--glass-border)",
        maxHeight: "520px",
        overflowY: "auto",
      }}
    >
      <p
        className="text-xs font-semibold uppercase tracking-wider mb-4"
        style={{ color: "hsl(var(--muted-foreground))" }}
      >
        <Database className="w-3.5 h-3.5 inline mr-1.5" />
        Tool Calls
      </p>

      {toolCards.length === 0 && isStreaming && (
        <div className="flex items-center gap-2 text-sm" style={{ color: "hsl(var(--muted-foreground))" }}>
          <Loader2 className="w-4 h-4 animate-spin" />
          Waiting for agent...
        </div>
      )}

      <div className="space-y-2">
        {toolCards.map((tool, i) => (
          <ToolCallCard
            key={i}
            name={tool.name}
            input={tool.input}
            output={tool.output}
            status={tool.done ? "done" : "running"}
          />
        ))}
      </div>

      {/* Streaming token preview */}
      {tokenBuffer && (
        <div className="mt-4">
          <p
            className="text-xs font-semibold uppercase tracking-wider mb-2"
            style={{ color: "hsl(var(--muted-foreground))" }}
          >
            Narrative Stream
          </p>
          <div
            className="rounded-lg p-3 text-xs leading-relaxed"
            style={{
              background: "hsl(var(--secondary))",
              color: "hsl(var(--foreground))",
              maxHeight: "120px",
              overflowY: "auto",
            }}
          >
            {tokenBuffer}
            {isStreaming && <span className="inline-block w-1 h-3 ml-0.5 bg-blue-400 animate-pulse" />}
          </div>
        </div>
      )}
    </div>
  );
}
