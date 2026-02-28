"""
LLM-powered intent classifier using OpenAI GPT-4o.

Used as the **primary** classifier when an ``OPENAI_API_KEY`` is set.
Falls back to the regex-based classifier in ``intent.py`` when:
  - no API key is configured, or
  - the OpenAI call fails for any reason.

A single GPT-4o call is made per question (~100-200 tokens).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from app.agent.intent import (
    Intent,
    _extract_branch,
    _extract_horizon,
    _extract_shift,
    _extract_top_k,
    classify_intent as regex_classify,
)

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────────

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = """\
You are the intent classifier for **Conut**, a bakery & café chain with 4 branches \
(Conut, Conut - Tyre, Conut Jnah, Main Street Coffee).

Your job: given a user's natural-language question, determine which of the 5 \
business objectives it relates to.

═══════════════════════════════════════════════════════════════
INTENT DEFINITIONS (choose exactly one)
═══════════════════════════════════════════════════════════════

1. **combo** — anything about product combinations, bundles, pairings, deals, \
   promotions, cross-selling, upselling, "what goes well together", \
   "frequently bought together", menu deals, package offers, "2-for-1", \
   "which items complement each other", "what should we promote together".

2. **forecast** — anything about predicting future sales, demand, revenue, \
   how busy a branch will be, projections, trends, seasonality, \
   "what to expect next month", inventory planning, supply chain, \
   "will we be busy", "predict the futures", "what will sales look like", \
   "expected performance", "anticipate demand".

3. **staffing** — anything about employees, workers, shifts, schedules, \
   headcount, "how many people do we need", labor, workforce, roster, \
   hiring, overtime, "do we need more workers", "who works when", \
   "Friday night staff", "busy shift coverage".

4. **expansion** — anything about opening new branches/stores/outlets, \
   entering new markets, feasibility analysis, location scouting, \
   "should we expand", "where to open next", "new city", "new area", \
   "is it worth opening", geographic growth, real estate.

5. **growth** — anything about increasing sales of coffee, milkshakes, \
   beverages, frappes, shakes, drinks strategy, beverage attachment, \
   product mix improvement, "sell more drinks", "boost coffee sales", \
   "improve beverage performance", drink menu optimization.

6. **unknown** — ONLY for clearly off-topic questions: weather, jokes, \
   personal questions, completely unrelated subjects. When in doubt, \
   pick the closest business intent — do NOT default to unknown.

═══════════════════════════════════════════════════════════════
RESPONSE FORMAT
═══════════════════════════════════════════════════════════════

Return ONLY a JSON object:
{"intent": "<combo|forecast|staffing|expansion|growth|unknown>", "confidence": <0.0-1.0>}

CRITICAL RULES:
- Think about what the user REALLY wants, not just keywords.
- "Predict the futures of conut tyre" → forecast (they mean future sales predictions).
- "Which products go well together?" → combo.
- "Do we need more workers?" → staffing.
- "How can we sell more drinks?" → growth.
- "Should we enter Tripoli?" → expansion.
- Be GENEROUS: if it's even loosely related to one intent, classify it. \
  Only use "unknown" for truly off-topic questions like "what's the weather".
- Return ONLY the JSON. No explanation, no markdown, no extra text.
"""


def _get_client():
    """Lazily create the OpenAI client. Returns None if no key."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception as exc:
        logger.warning("Failed to create OpenAI client: %s", exc)
        return None


def llm_classify(question: str) -> Optional[Intent]:
    """
    Classify intent via OpenAI.  Returns None on any failure so the caller
    can fall back to the regex classifier.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.0,
            max_tokens=60,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)

        action = parsed.get("intent", "unknown").lower().strip()
        if action not in {"combo", "forecast", "staffing", "expansion", "growth", "unknown"}:
            action = "unknown"

        confidence = float(parsed.get("confidence", 0.8))
        confidence = max(0.0, min(1.0, confidence))

        # Entity extraction still uses the robust regex helpers
        return Intent(
            action=action,
            branch=_extract_branch(question),
            shift=_extract_shift(question),
            horizon_months=_extract_horizon(question),
            top_k=_extract_top_k(question),
            confidence=confidence,
            matched_keywords=["llm"],
        )

    except Exception as exc:
        logger.warning("LLM classify failed (%s), falling back to regex.", exc)
        return None


def smart_classify(question: str) -> Intent:
    """
    Try LLM first, fall back to regex.

    This is the function that ``agent.py`` should call instead of
    ``classify_intent`` directly.
    """
    llm_result = llm_classify(question)
    if llm_result is not None:
        logger.info("LLM classified as: %s (conf=%.2f)", llm_result.action, llm_result.confidence)
        return llm_result

    logger.info("No LLM available, using regex classifier.")
    return regex_classify(question)
