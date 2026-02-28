from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    branch: str = Field(..., min_length=1, description="Branch name, e.g. 'Conut Jnah'")
    horizon_months: int = Field(default=1, ge=1, le=6, description="Months ahead to forecast")


class MonthForecast(BaseModel):
    month: str
    naive: float
    wma: float
    trend: float
    ensemble: float


class HistoryPoint(BaseModel):
    month: str
    total: float


class ForecastResponse(BaseModel):
    branch: str
    horizon_months: int
    trend: str
    confidence: str
    demand_index: float | None = None
    avg_mom_growth_pct: float | None = None
    history: list[HistoryPoint]
    forecasts: list[MonthForecast]
    anomaly_notes: list[str] | None = None
    explanation: str
    error: str | None = None
