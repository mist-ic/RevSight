from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ImpactLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffortLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MetricSummary(BaseModel):
    metric_id: str
    name: str
    value: float
    unit: str
    status: str  # "healthy" | "at_risk" | "critical"


class RiskNarrative(BaseModel):
    risk_id: str
    title: str
    severity: str
    narrative: str
    linked_metric_ids: list[str] = Field(default_factory=list)


class OpportunityNarrative(BaseModel):
    title: str
    narrative: str
    potential_arr_impact: Optional[float] = None


class ActionItem(BaseModel):
    action: str
    rationale: str
    impact: ImpactLevel
    effort: EffortLevel
    owner: Optional[str] = None
    timeline: Optional[str] = None


class PipelineHealthReport(BaseModel):
    executive_summary: str
    key_metrics: list[MetricSummary]
    risks: list[RiskNarrative]
    opportunities: list[OpportunityNarrative]
    recommended_actions: list[ActionItem]
    forecast_confidence: float = Field(ge=0.0, le=1.0)
    data_quality_flags: list[str] = Field(default_factory=list)
    overall_status: str = "unknown"  # "healthy" | "at_risk" | "critical"
