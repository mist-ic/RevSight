// API client for RevSight backend

// In the browser, use relative /api/* paths which Next.js proxies to the backend.
// For SSR or non-browser contexts, fall back to the env var.
const API_URL =
  typeof window !== "undefined"
    ? ""
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export async function createReport(body: {
  quarter: string;
  region: string;
  segment: string;
  persona: string;
  scenario_id?: string;
}) {
  const res = await fetch(`${API_URL}/api/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getReport(runId: string) {
  const res = await fetch(`${API_URL}/api/reports/${runId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPipelineMetrics(params: {
  scenario_id: string;
  quarter: string;
  region: string;
  segment: string;
}) {
  const q = new URLSearchParams(params).toString();
  const res = await fetch(`${API_URL}/api/metrics/pipeline?${q}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listRuns(limit = 20, offset = 0) {
  const res = await fetch(`${API_URL}/api/runs?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function streamReport(
  body: {
    quarter: string;
    region: string;
    segment: string;
    persona: string;
    scenario_id?: string;
  },
  onEvent: (event: import("./types").AgentEvent) => void,
  onError: (err: Error) => void
): () => void {
  let aborted = false;
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_URL}/api/reports/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (!aborted) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Server sends \r\n\r\n between events -- normalize to \n\n first
        const normalized = buffer.replace(/\r\n/g, "\n");
        const parts = normalized.split("\n\n");
        // Keep last partial part in buffer
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          for (const line of part.split("\n")) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;
            const payload = trimmed.slice(6).trim();
            if (!payload) continue;
            try {
              const event = JSON.parse(payload);
              onEvent(event);
            } catch {
              // skip malformed chunks
            }
          }
        }
      }
    } catch (err) {
      if (!aborted) onError(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return () => {
    aborted = true;
    controller.abort();
  };
}
