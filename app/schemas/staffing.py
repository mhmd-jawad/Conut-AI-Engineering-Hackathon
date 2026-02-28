from pydantic import BaseModel, Field


class StaffingRequest(BaseModel):
    branch: str = Field(..., min_length=1)
    shift: str = Field(default="evening", min_length=3)
