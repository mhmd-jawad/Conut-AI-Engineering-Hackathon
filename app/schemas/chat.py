"""Pydantic schemas for the /chat endpoint."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming natural-language question."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        examples=[
            "What are the top combos for Conut Jnah?",
            "Forecast demand for Conut - Tyre next 4 months",
            "How many staff for the evening shift at Conut?",
            "Should we expand? Where is the best location?",
            "Give me a coffee growth strategy for Main Street Coffee",
        ],
    )


class ChatResponse(BaseModel):
    """Agent answer."""
    intent: str = Field(..., description="Detected intent (combo|forecast|staffing|expansion|growth|unknown)")
    branch: Optional[str] = Field(None, description="Branch the answer relates to")
    answer: str = Field(..., description="Human-readable Markdown answer")
    confidence: float = Field(..., description="Intent-classification confidence 0-1")
    elapsed_ms: float = Field(..., description="End-to-end processing time in milliseconds")
    data: Optional[Any] = Field(None, description="Raw service result for programmatic consumers")
    error: Optional[str] = Field(None, description="Error message if something went wrong")
