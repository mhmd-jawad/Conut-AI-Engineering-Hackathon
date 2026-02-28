"""
Rule-based intent classifier for natural-language business questions.

Identifies which of the 5 business objectives the user is asking about and
extracts relevant entities (branch, shift, horizon, top_k).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ── Known branches (lowercase → canonical) ──────────────────────────────
BRANCH_ALIASES: dict[str, str] = {
    "conut - tyre":         "Conut - Tyre",
    "conut-tyre":           "Conut - Tyre",
    "conut tyre":           "Conut - Tyre",
    "tyre":                 "Conut - Tyre",
    "conut jnah":           "Conut Jnah",
    "jnah":                 "Conut Jnah",
    "main street coffee":   "Main Street Coffee",
    "main street":          "Main Street Coffee",
    "msc":                  "Main Street Coffee",
    "conut":                "Conut",          # must come after longer prefixes
}

KNOWN_BRANCHES = ["Conut - Tyre", "Conut Jnah", "Main Street Coffee", "Conut"]

SHIFTS = {"morning", "midday", "evening"}

# ── Intent definitions ──────────────────────────────────────────────────

INTENT_PATTERNS: dict[str, list[re.Pattern]] = {
    "combo": [
        re.compile(r"\bcombos?\b", re.I),
        re.compile(r"\bbundles?\b", re.I),
        re.compile(r"\bpair(?:ing|s)?\b", re.I),
        re.compile(r"\bbasket\b", re.I),
        re.compile(r"\bcross[- ]?sell\b", re.I),
        re.compile(r"\bfrequently\s+bought\b", re.I),
        re.compile(r"\bproduct\s+combination\b", re.I),
        re.compile(r"\brecommend.*(?:item|product)\b", re.I),
        re.compile(r"\bdeals?\b", re.I),
        re.compile(r"\bpromotions?\b", re.I),
        re.compile(r"\bupsell\b", re.I),
    ],
    "forecast": [
        re.compile(r"\bforecast\b", re.I),
        re.compile(r"\bdemand\b", re.I),
        re.compile(r"\bpredict(?:ion)?\b", re.I),
        re.compile(r"\bnext\s+(?:\d+\s+)?months?\b", re.I),
        re.compile(r"\btrend\b", re.I),
        re.compile(r"\bsales\s+projection\b", re.I),
        re.compile(r"\bproject(?:ed)?\s+sales\b", re.I),
        re.compile(r"\bfuture\s+(?:sales|demand|revenue)\b", re.I),
    ],
    "staffing": [
        re.compile(r"\bstaff(?:ing)?\b", re.I),
        re.compile(r"\bshift\b", re.I),
        re.compile(r"\bemployee\b", re.I),
        re.compile(r"\bschedul\b", re.I),       # schedule / scheduling
        re.compile(r"\bheadcount\b", re.I),
        re.compile(r"\blabor\b", re.I),
        re.compile(r"\bhow\s+many\s+(?:people|workers|staff)\b", re.I),
        re.compile(r"\bworkforce\b", re.I),
    ],
    "expansion": [
        re.compile(r"\bexpan(?:d|sion)\b", re.I),
        re.compile(r"\bnew\s+branch\b", re.I),
        re.compile(r"\bnew\s+location\b", re.I),
        re.compile(r"\bopen(?:ing)?\s+(?:a\s+)?(?:new\s+)?(?:branch|store|shop|outlet)\b", re.I),
        re.compile(r"\bfeasib(?:le|ility)\b", re.I),
        re.compile(r"\bcandidate\s+(?:locations?|areas?|cit(?:y|ies))\b", re.I),
        re.compile(r"\bwhere\s+(?:should|to)\s+(?:we\s+)?open\b", re.I),
    ],
    "growth": [
        re.compile(r"\bgrowth\b", re.I),
        re.compile(r"\bcoffee\b", re.I),
        re.compile(r"\bmilkshake\b", re.I),
        re.compile(r"\bshake\b", re.I),
        re.compile(r"\bbeverage\b", re.I),
        re.compile(r"\bfrappe\b", re.I),
        re.compile(r"\bstrategy\b", re.I),
        re.compile(r"\bincrease\s+(?:coffee|beverage|drink)\b", re.I),
        re.compile(r"\bbeverage\s+attach\b", re.I),
        re.compile(r"\bdrink\s+sales\b", re.I),
    ],
}

# Boost scores when multiple keywords appear
INTENT_BOOST: dict[str, list[re.Pattern]] = {
    "combo":     [re.compile(r"\blift\b|\bsupport\b|\bconfidence\b", re.I)],
    "forecast":  [re.compile(r"\bmonth\b|\bquarter\b|\binventory\b", re.I)],
    "staffing":  [re.compile(r"\bmorning\b|\bevening\b|\bmidday\b", re.I)],
    "expansion": [re.compile(r"\bscorecard\b|\bscore\b|\blocation\b", re.I)],
    "growth":    [re.compile(r"\bpenetration\b|\bhero\b|\battach\b", re.I)],
}


@dataclass
class Intent:
    """Parsed intent from a user question."""
    action: str                        # combo | forecast | staffing | expansion | growth | unknown
    branch: Optional[str] = None       # canonical branch name or "all"
    shift: Optional[str] = None        # morning | midday | evening
    horizon_months: int = 3            # default 3
    top_k: int = 5                     # default 5
    confidence: float = 0.0            # how confident we are [0-1]
    matched_keywords: list[str] = field(default_factory=list)


# ── Entity extraction helpers ───────────────────────────────────────────

def _extract_branch(text: str) -> Optional[str]:
    """Return canonical branch name found in *text*, or None."""
    lower = text.lower()

    # Check "all branches" explicitly
    if re.search(r"\ball\s+branches\b|\bevery\s+branch\b|\beach\s+branch\b", lower):
        return "all"

    # Try longest match first (sort aliases by length desc)
    for alias in sorted(BRANCH_ALIASES, key=len, reverse=True):
        if alias in lower:
            return BRANCH_ALIASES[alias]
    return None


def _extract_shift(text: str) -> Optional[str]:
    lower = text.lower()
    for s in SHIFTS:
        if s in lower:
            return s
    return None


def _extract_horizon(text: str) -> int:
    m = re.search(r"(?:next|coming|forecast(?:ing)?)\s+(\d{1,2})\s+months?", text, re.I)
    if m:
        return min(int(m.group(1)), 12)
    m = re.search(r"(\d{1,2})\s+months?\s+(?:ahead|forecast|prediction|projection)", text, re.I)
    if m:
        return min(int(m.group(1)), 12)
    return 3  # default


def _extract_top_k(text: str) -> int:
    m = re.search(r"top\s+(\d{1,2})", text, re.I)
    if m:
        return min(int(m.group(1)), 20)
    return 5  # default


# ── Main classifier ────────────────────────────────────────────────────

def classify_intent(question: str) -> Intent:
    """Classify a natural-language question into one of 5 business intents."""

    scores: dict[str, float] = {k: 0.0 for k in INTENT_PATTERNS}
    matched: dict[str, list[str]] = {k: [] for k in INTENT_PATTERNS}

    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if pat.search(question):
                scores[intent] += 1.0
                matched[intent].append(pat.pattern)

    # Apply boost patterns (add 0.5 per match)
    for intent, boosts in INTENT_BOOST.items():
        for pat in boosts:
            if pat.search(question):
                scores[intent] += 0.5

    # Pick best intent
    best = max(scores, key=scores.get)          # type: ignore[arg-type]
    best_score = scores[best]

    if best_score == 0:
        return Intent(
            action="unknown",
            branch=_extract_branch(question),
            confidence=0.0,
        )

    # Normalise confidence: score / (number of patterns for that intent)
    max_possible = len(INTENT_PATTERNS[best]) + 0.5 * len(INTENT_BOOST.get(best, []))
    confidence = min(best_score / max_possible, 1.0) if max_possible else 0.0

    return Intent(
        action=best,
        branch=_extract_branch(question),
        shift=_extract_shift(question),
        horizon_months=_extract_horizon(question),
        top_k=_extract_top_k(question),
        confidence=round(confidence, 3),
        matched_keywords=matched[best],
    )
