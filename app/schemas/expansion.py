from pydantic import BaseModel, Field


class ExpansionRequest(BaseModel):
    branch: str = Field(default="", description="Optional reference branch")
