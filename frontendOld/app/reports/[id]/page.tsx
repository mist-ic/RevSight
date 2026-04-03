"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getReport } from "@/lib/api";
import type { PipelineHealthReport } from "@/lib/types";
import { ReportViewer } from "@/components/dashboard/report-viewer";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Copy, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<PipelineHealthReport | null>(null);
  const [run, setRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getReport(id)
      .then((data) => {
        setRun(data);
        setReport(data.report);
      })
      .catch(() => toast.error("Failed to load report"))
      .finally(() => setLoading(false));
  }, [id]);

  function handleCopy() {
    if (!report) return;
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    toast.success("Report JSON copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="min-h-screen p-8" style={{ background: "hsl(var(--background))" }}>
      <div className="flex items-center justify-between mb-8">
        <div>
          <Button
            variant="ghost"
            className="mb-3 -ml-2 text-sm"
            style={{ color: "hsl(var(--muted-foreground))" }}
            onClick={() => router.back()}
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Back
          </Button>
          <h1 className="text-2xl font-bold">
            {run?.region} {run?.segment} {run?.quarter}
          </h1>
          <p className="text-sm mt-1 mono" style={{ color: "hsl(var(--muted-foreground))" }}>
            Run ID: {id}
          </p>
        </div>
        {report && (
          <Button variant="outline" onClick={handleCopy} className="gap-2">
            {copied ? (
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
            {copied ? "Copied!" : "Copy JSON"}
          </Button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" style={{ background: "hsl(var(--card))" }} />
          ))}
        </div>
      ) : report ? (
        <ReportViewer report={report} persona={run?.persona ?? "cro"} />
      ) : (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ background: "hsl(var(--card))", border: "1px solid var(--glass-border)" }}
        >
          <p style={{ color: "hsl(var(--muted-foreground))" }}>
            Report not available or run is still in progress.
          </p>
        </div>
      )}
    </div>
  );
}
