from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Persona(str, Enum):
    CRO = "cro"
    REVOPS = "revops"
    ENGINEER = "engineer"


class ReportRequest(BaseModel):
    quarter: str = Field(..., description="e.g. Q3-2026")
    region: str = Field(..., description="e.g. NA, EMEA, APAC")
    segment: str = Field(..., description="e.g. Enterprise, SMB, Mid-Market")
    persona: Persona = Field(default=Persona.CRO)
    scenario_id: Optional[str] = Field(None, description="Pre-defined scenario shortcut")
