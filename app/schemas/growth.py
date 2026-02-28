from pydantic import BaseModel, Field


class GrowthRequest(BaseModel):
    branch: str = Field(..., min_length=1)
