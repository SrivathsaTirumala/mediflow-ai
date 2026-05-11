from typing import Literal

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    name: str = ""
    age: int | None = None
    gender: str = ""
    duration: str = "1-2 days"
    symptoms: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    allergies: str = ""
    location_query: str = ""
    notes: str = ""


class DifferentialItem(BaseModel):
    condition: str
    confidence: int = Field(ge=0, le=100)
    reason: str


class SafetyAssessment(BaseModel):
    risk_level: Literal["Low", "Moderate", "High"]
    care_level: Literal["routine", "urgent", "emergency"]
    summary: str
    safety_flags: list[str] = Field(default_factory=list)
    emergency_flags: list[str] = Field(default_factory=list)


class NearbyCareOption(BaseModel):
    label: str
    google_maps_url: str


class AnalysisResponse(BaseModel):
    risk_level: Literal["Low", "Moderate", "High"]
    care_level: Literal["routine", "urgent", "emergency"]
    summary: str
    differentials: list[DifferentialItem] = Field(default_factory=list)
    medication_support: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    emergency_flags: list[str] = Field(default_factory=list)
    suggested_tests: list[str] = Field(default_factory=list)
    nearby_care: list[str] = Field(default_factory=list)
    nearby_care_options: list[NearbyCareOption] = Field(default_factory=list)
    follow_up: str
    reasoning: str
    agent_outputs: dict[str, str] = Field(default_factory=dict)
    memory_context: list[str] = Field(default_factory=list)
    session_id: str
    agent_status: str
    used_a2a: bool = False
