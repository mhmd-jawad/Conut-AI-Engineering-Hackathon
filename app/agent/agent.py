"""
Operational AI Agent – the orchestrator.

Pipeline:  question → smart_classify → dispatch → format_response

Uses OpenAI (GPT-4o-mini) as the **primary** intent classifier for robust
natural-language understanding.  Falls back to the regex classifier when no
OPENAI_API_KEY is set or the API call fails.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

from app.agent.intent import Intent
from app.agent.llm_intent import smart_classify
from app.agent.tools import dispatch
from app.agent.formatter import format_response

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Value object returned by ``ask()``."""
    intent: str
    branch: Optional[str]
    answer: str                # human-readable Markdown
    raw_data: Any = None       # original service dict (for programmatic use)
    error: Optional[str] = None
    elapsed_ms: float = 0.0
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def ask(question: str) -> AgentResponse:
    """
    Accept a free-text business question and return a structured answer.

    >>> resp = ask("What are the best combos for Conut Jnah?")
    >>> resp.intent
    'combo'
    """
    t0 = time.perf_counter()

    # 1. Intent classification (LLM-first, regex-fallback)
    intent: Intent = smart_classify(question)
    logger.info("Intent: %s  branch=%s  conf=%.2f  via=%s",
                intent.action, intent.branch, intent.confidence,
                "llm" if "llm" in intent.matched_keywords else "regex")

    # 2. Dispatch to service
    result = dispatch(intent)

    # 3. Format
    answer = format_response(
        action=intent.action,
        data=result.get("data"),
        error=result.get("error"),
    )

    elapsed = (time.perf_counter() - t0) * 1000

    return AgentResponse(
        intent=intent.action,
        branch=intent.branch,
        answer=answer,
        raw_data=result.get("data"),
        error=result.get("error"),
        elapsed_ms=round(elapsed, 1),
        confidence=intent.confidence,
    )
