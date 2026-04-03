"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MoveRight } from "lucide-react";
import { LivePipelineChart } from "@/components/dashboard/live-pipeline-chart";
import type { Persona, Scenario } from "@/lib/types";

const SCENARIOS: Scenario[] = [
  {
    id: "na_healthy",
    label: "NA ENT",
    region: "NA",
    segment: "Enterprise",
    quarter: "Q3-2026",
    health: "healthy",
    description: "STR_PIPELINE_COVERAGE = TRUE. BALANCED STAGE DISTRIBUTION VALIDATED.",
    tags: ["4.2X COV", "28% WIN"],
  },
  {
    id: "emea_undercovered",
    label: "EU SMB",
    region: "EMEA",
    segment: "SMB",
    quarter: "Q3-2026",
    health: "at_risk",
    description: "WARN_DISCOVERY_VOL_HIGH. CRITICAL FAILURE IN NEGOTIATION STAGING DETECTED.",
    tags: ["1.8X COV", "18% WIN"],
  },
  {
    id: "apac_dataquality",
    label: "AP ENT",
    region: "APAC",
    segment: "Enterprise",
    quarter: "Q3-2026",
    health: "critical",
    description: "ERR_DATA_MISSING. NOMINAL STRENGTH FUNDAMENTALLY UNDERMINED BY NULL DATES.",
    tags: ["3.1X NML", "ERR_DATA"],
  },
];

const PERSONAS: { value: Persona; label: string; description: string }[] = [
  { value: "cro", label: "01_CRO.SYS", description: "Executive summary + forecast" },
  { value: "revops", label: "02_OPS.SYS", description: "Metric drill-down + actions" },
  { value: "engineer", label: "03_ENG.SYS", description: "Agent traces + tool calls" },
];

export default function HomePage() {
  const router = useRouter();
  const [selectedPersona, setSelectedPersona] = useState<Persona>("cro");
  const [loading, setLoading] = useState<string | null>(null);

  function handleGenerate(scenario: Scenario) {
    setLoading(scenario.id);
    const params = new URLSearchParams({
      scenario_id: scenario.id,
      quarter: scenario.quarter,
      region: scenario.region,
      segment: scenario.segment,
      persona: selectedPersona,
    });
    router.push(`/reports/new?${params.toString()}`);
  }

  return (
    <div className="h-full w-full flex flex-col pt-8 md:pt-0">
      {/* Horizontal Persona Selector / Status Bar */}
      <div className="h-20 border-b border-border flex flex-col md:flex-row items-start md:items-center justify-between px-8 bg-[#050505]/90 backdrop-blur-md shrink-0">
        <h2 className="text-2xl font-extrabold tracking-tight text-white uppercase hidden md:block">
          PIPELINE <span className="text-primary italic font-light">INTELLIGENCE</span>
        </h2>
        <div className="flex items-center h-full w-full md:w-auto mt-4 md:mt-0 overflow-x-auto">
          {PERSONAS.map(p => {
             const active = selectedPersona === p.value;
             return (
               <button
                 key={p.value}
                 onClick={() => setSelectedPersona(p.value)}
                 className={`h-full flex items-center px-6 border-x border-transparent hover:border-border transition-colors font-data text-xs uppercase tracking-[0.2em] font-bold shrink-0 ${
                   active ? "text-primary" : "text-muted-foreground hover:text-white"
                 }`}
               >
                 {active && <div className="w-1.5 h-1.5 bg-primary rounded-full mr-3 animate-pulse drop-shadow-[0_0_5px_rgba(229,255,0,0.8)]" />}
                 {p.label}
               </button>
             )
          })}
        </div>
      </div>

      {/* Massive 3 Column Asymmetric Layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-y-auto md:overflow-hidden">
        {SCENARIOS.map((scenario, i) => {
          const isHealthy = scenario.health === 'healthy';
          const isCritical = scenario.health === 'critical';
          const isLoading = loading === scenario.id;
          
          return (
            <div 
              key={scenario.id} 
              className={`group relative flex-1 flex flex-col border-b md:border-b-0 border-r-0 md:border-r border-border transition-colors duration-500 hover:bg-[#0a0a0a] ${isCritical ? 'bg-[#080808]' : ''} ${i === 2 ? 'md:border-r-0' : ''}`}
            >
              {isLoading && (
                <div className="absolute inset-0 bg-primary z-50 flex items-center justify-center p-8">
                  <h1 className="text-6xl text-black font-extrabold animate-pulse tracking-tighter">EXE</h1>
                </div>
              )}

              {/* Top Meta Data */}
              <div className="p-8 pb-12 border-b border-border bg-[#050505]">
                <div className="flex items-center justify-between font-data text-[10px] uppercase tracking-widest mb-12">
                   <span className="text-muted-foreground">[{scenario.region}] {scenario.quarter}</span>
                   <span className={`px-2 py-1 font-bold ${isHealthy ? 'text-primary' : 'text-white bg-red-600'}`}>
                     {scenario.health.replace("_", " ")}
                   </span>
                </div>
                
                <h3 className="text-7xl lg:text-[6rem] tracking-tighter text-white font-extrabold leading-[0.8] mb-8 break-normal">
                  {scenario.label}
                </h3>
                
                <p className="font-data text-xs text-muted-foreground leading-relaxed max-w-[90%]">
                  {scenario.description}
                </p>
                
                <div className="flex gap-2 mt-8">
                  {scenario.tags.map(tag => (
                    <span key={tag} className="font-data text-[9px] uppercase tracking-[0.2em] border border-border px-2 py-1 text-muted-foreground group-hover:border-primary/30 group-hover:text-primary transition-colors">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Middle Chart Canvas */}
              <div className="px-8 flex-1 flex flex-col justify-end pb-8">
                <LivePipelineChart scenarioId={scenario.id} />
              </div>

              {/* Huge Action Button Footer */}
              <button
                onClick={() => handleGenerate(scenario)}
                disabled={!!loading}
                className="w-full h-24 border-t border-border flex items-center justify-between px-8 hover:bg-primary hover:text-black transition-colors group/btn text-muted-foreground cursor-pointer shrink-0"
              >
                <span className="font-data text-xs uppercase tracking-[0.3em] font-bold group-hover/btn:text-black transition-colors">Instantiate</span>
                <MoveRight className="w-6 h-6 group-hover/btn:translate-x-4 transition-all text-white group-hover/btn:text-black" />
              </button>
            </div>
          )
        })}
      </div>
    </div>
  );
}
