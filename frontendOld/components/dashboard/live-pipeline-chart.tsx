"use client";

import { useEffect, useState } from "react";
import { getPipelineMetrics } from "@/lib/api";
import { PipelineChart } from "./pipeline-chart";
import { Skeleton } from "@/components/ui/skeleton";

type Props = {
  scenarioId: string;
  quarter?: string;
  region?: string;
  segment?: string;
};

export function LivePipelineChart({ scenarioId, quarter = "Q3-2026", region, segment }: Props) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Derive region/segment from scenarioId if not provided
  const resolvedRegion = region ?? (scenarioId === "na_healthy" ? "NA" : scenarioId === "emea_undercovered" ? "EMEA" : "APAC");
  const resolvedSegment = segment ?? (scenarioId === "emea_undercovered" ? "SMB" : "Enterprise");

  useEffect(() => {
    getPipelineMetrics({ scenario_id: scenarioId, quarter, region: resolvedRegion, segment: resolvedSegment })
      .then((d) => setData(d.metrics ?? []))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [scenarioId, quarter, resolvedRegion, resolvedSegment]);

  if (loading) return <Skeleton className="w-full h-48 rounded-2xl" style={{ background: "hsl(var(--card))" }} />;
  if (!data.length) return null;

  return <PipelineChart data={data} />;
}
