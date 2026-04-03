export type Persona = "cro" | "revops" | "engineer";

export interface Scenario {
  id: string;
  label: string;
  region: string;
  segment: string;
  quarter: string;
  health: "healthy" | "at_risk" | "critical";
  description: string;
  tags: string[];
}
