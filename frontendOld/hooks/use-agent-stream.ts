"use client";

import { useState, useRef, useCallback } from "react";
import type { AgentEvent, PipelineHealthReport } from "@/lib/types";
import { streamReport } from "@/lib/api";

type StreamState = {
  events: AgentEvent[];
  tokenBuffer: string;
  isStreaming: boolean;
  runId: string | null;
  report: PipelineHealthReport | null;
  error: string | null;
  activeNode: string | null;
};

export function useAgentStream() {
  const [state, setState] = useState<StreamState>({
    events: [],
    tokenBuffer: "",
    isStreaming: false,
    runId: null,
    report: null,
    error: null,
    activeNode: null,
  });

  const stopRef = useRef<(() => void) | null>(null);

  const start = useCallback(
    (body: {
      quarter: string;
      region: string;
      segment: string;
      persona: string;
      scenario_id?: string;
    }) => {
      // Reset state
      setState({
        events: [],
        tokenBuffer: "",
        isStreaming: true,
        runId: null,
        report: null,
        error: null,
        activeNode: null,
      });

      const stop = streamReport(
        body,
        (event) => {
          setState((prev) => {
            const next = { ...prev, events: [...prev.events, event] };

            if (event.type === "run_started") {
              next.runId = event.run_id;
            } else if (event.type === "step") {
              next.activeNode = event.node;
            } else if (event.type === "token") {
              next.tokenBuffer = prev.tokenBuffer + event.content;
            } else if (event.type === "done") {
              next.isStreaming = false;
              next.report = event.report;
              next.runId = event.run_id;
            } else if (event.type === "error") {
              next.isStreaming = false;
              next.error = event.message;
            }

            return next;
          });
        },
        (err) => {
          setState((prev) => ({ ...prev, isStreaming: false, error: err.message }));
        }
      );

      stopRef.current = stop;
    },
    []
  );

  const stop = useCallback(() => {
    stopRef.current?.();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  return { ...state, start, stop };
}
