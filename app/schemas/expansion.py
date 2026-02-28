from __future__ import annotations

from pydantic import BaseModel, Field


class ExpansionRequest(BaseModel):
    branch: str = Field(
        default="",
        description="Branch name to focus on, or empty / 'all' to score every branch.",
    )


# ── Response models ────────────────────────────────────────────────────────


class DimensionDetail(BaseModel):
    """Flexible key-value detail for a scorecard dimension."""
    score: float = Field(description="Normalized score 0-100")
    detail: dict = Field(description="Dimension-specific metrics")


class BranchScorecard(BaseModel):
    branch: str
    dimensions: dict[str, DimensionDetail] = Field(
        description="Six KPI dimensions, each with score + detail",
    )
    composite_score: float = Field(description="Weighted composite 0-100")


class ArchetypeProfile(BaseModel):
    branch: str = Field(description="Best-performing branch name")
    composite_score: float
    channel_mix: dict[str, float] = Field(
        description="Channel → total sales for the archetype branch",
    )
    top_categories: dict[str, float] = Field(
        description="Top 5 revenue divisions",
    )
    beverage_pct: float = Field(description="Beverage revenue as % of ITEMS total")
    recommendation: str = Field(description="Human-readable replication advice")


class CandidateLocation(BaseModel):
    area: str
    governorate: str
    score: float = Field(description="Attractiveness score 0-100")
    population: int
    university_nearby: bool
    foot_traffic_tier: int = Field(ge=1, le=5)
    rent_tier: int = Field(ge=1, le=5)
    cafe_density: str
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class ExpansionResponse(BaseModel):
    verdict: str = Field(description="GO / CAUTION / NO-GO")
    verdict_detail: str
    best_archetype: ArchetypeProfile
    scorecards: list[BranchScorecard]
    candidate_locations: list[CandidateLocation]
    risks: list[str]
    explanation: str
