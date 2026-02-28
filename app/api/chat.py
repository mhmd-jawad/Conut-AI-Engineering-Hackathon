"""
/chat endpoint – single unified entry-point for the Operational AI Agent.

Accepts a natural-language question and returns a structured Markdown answer
backed by the 5 business-objective analytics services.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.agent.agent import ask
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """Ask the Conut Chief-of-Operations Agent a business question."""
    resp = ask(body.question)
    return ChatResponse(
        intent=resp.intent,
        branch=resp.branch,
        answer=resp.answer,
        confidence=resp.confidence,
        elapsed_ms=resp.elapsed_ms,
        data=resp.raw_data,
        error=resp.error,
    )
