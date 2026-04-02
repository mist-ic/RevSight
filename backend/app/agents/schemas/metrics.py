from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RiskSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MetricResult(BaseModel):
    metric_id: str
    name: str
    value: float
    unit: str = ""
    segment: str = ""
    comparison: Optional[float] = None  # previous period or target
    trend: Optional[str] = None  # "up" | "down" | "flat"


class RiskObject(BaseModel):
    risk_id: str
    title: str
    severity: RiskSeverity
    rationale: str
    linked_metric_ids: list[str] = Field(default_factory=list)
    linked_deal_ids: list[str] = Field(default_factory=list)
    recommendation: str = ""
