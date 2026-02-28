from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    branch: str = Field(..., min_length=1)
    horizon_months: int = Field(default=1, ge=1, le=6)
