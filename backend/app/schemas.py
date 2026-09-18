"""
Pydantic contracts for the whole system.
Nothing downstream (reasoning, generation, formatting) accepts raw dicts —
everything is validated against these models first. This is the input
handling layer described in Section 6 of the architecture doc.
"""
from __future__ import annotations
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


class EnvironmentalInput(BaseModel):
    """Structured input — the JSON path, and also the target shape that
    free-text extraction (see conversation/slot_filling.py) fills in."""
    soil_organic_carbon_pct: Optional[float] = Field(None, ge=0, le=20)
    soil_ph: Optional[float] = Field(None, ge=0, le=14)
    soil_moisture_pct: Optional[float] = Field(None, ge=0, le=100)
    land_use: Optional[Literal[
        "monoculture", "polyculture", "agroforestry", "fallow",
        "grassland", "forest", "urban", "wetland"
    ]] = None
    rainfall_pattern: Optional[Literal["low", "moderate", "high", "erratic"]] = None
    region_biome: Optional[Literal[
        "semi-arid", "arid", "tropical", "temperate", "mediterranean"
    ]] = None
    pollution_index: Optional[float] = Field(None, ge=0, le=100)
    deforestation_rate_pct_per_yr: Optional[float] = Field(None, ge=0, le=100)
    species_richness_index: Optional[float] = Field(None, ge=0, le=1)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)

    @field_validator("soil_ph")
    @classmethod
    def sane_ph(cls, v):
        if v is not None and (v < 2 or v > 12):
            raise ValueError("soil_ph out of plausible range for agricultural soil")
        return v

    def filled_slots(self) -> List[str]:
        return [k for k, v in self.model_dump().items() if v is not None and k not in ("lat", "lon")]


class ConverseRequest(BaseModel):
    session_id: str
    message: str


class DiagnoseRequest(BaseModel):
    session_id: str
    data: EnvironmentalInput


class ImpactedMetric(BaseModel):
    metric: str
    expected_change: str
    direction: Literal["positive", "negative", "neutral"]


class Recommendation(BaseModel):
    recommendation: str
    reasoning: str
    impacted_metrics: List[ImpactedMetric]
    time_horizon: Literal["short-term", "medium-term", "long-term"]
    confidence: Literal["High", "Medium", "Low"]
    confidence_breakdown: str
    trade_offs: Optional[str] = None
    rejected_alternatives: Optional[List[str]] = None
    sources: List[str]
    rule_node_id: str


class SystemResponse(BaseModel):
    session_id: str
    reply_text: str
    clarification_needed: bool
    missing_slots: List[str] = []
    recommendations: List[Recommendation] = []
    filled_input: Optional[EnvironmentalInput] = None
