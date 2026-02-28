"""
Tool wrappers – thin adapters around each of the 5 business-objective services.

Every wrapper returns a standardised dict:
    {"success": bool, "data": <service_result | None>, "error": <str | None>}

The ``dispatch`` function maps an Intent to the correct wrapper.
"""

from __future__ import annotations

import traceback
from typing import Any

from app.agent.intent import Intent, KNOWN_BRANCHES


# ── Lazy service imports (avoid circular / heavy load at parse time) ────

def _combo(branch: str, top_k: int) -> dict:
    from app.services.combo_service import recommend_combos
    return recommend_combos(branch=branch, top_k=top_k)


def _forecast(branch: str, horizon: int) -> dict:
    from app.services.forecast_service import forecast_branch_demand
    return forecast_branch_demand(branch=branch, horizon_months=horizon)


def _staffing(branch: str, shift: str) -> dict:
    from app.services.staffing_service import recommend_staffing
    return recommend_staffing(branch=branch, shift=shift)


def _expansion(branch: str) -> dict:
    from app.services.expansion_service import evaluate_expansion
    return evaluate_expansion(branch=branch)


def _growth(branch: str) -> dict:
    from app.services.growth_service import growth_strategy
    return growth_strategy(branch=branch)


# ── Standardised wrapper ───────────────────────────────────────────────

def _safe_call(fn, **kwargs) -> dict[str, Any]:
    """Call *fn* and wrap result in standard envelope."""
    try:
        data = fn(**kwargs)
        return {"success": True, "data": data, "error": None}
    except Exception as exc:
        return {
            "success": False,
            "data": None,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }


# ── Multi-branch helper ────────────────────────────────────────────────

def _multi_branch(fn, branches: list[str], **extra) -> dict[str, Any]:
    """Run *fn* for every branch and merge results."""
    results: dict[str, Any] = {}
    errors: list[str] = []
    for b in branches:
        res = _safe_call(fn, branch=b, **extra)
        if res["success"]:
            results[b] = res["data"]
        else:
            errors.append(f"{b}: {res['error']}")

    if not results:
        return {"success": False, "data": None, "error": "; ".join(errors)}
    return {
        "success": True,
        "data": {"branches": results},
        "error": "; ".join(errors) if errors else None,
    }


# ── Dispatch ────────────────────────────────────────────────────────────

DEFAULT_SHIFT = "morning"


# ── Chitchat LLM reply ──────────────────────────────────────────────────

_STATIC_CHITCHAT = (
    "\U0001f44b Hey there! I'm the Conut Operations Agent.\n\n"
    "I'm here to help you with:\n"
    "\U0001f369 Combo deals  |  \U0001f4c8 Forecasts  |  \U0001f465 Staffing\n"
    "\U0001f3d7 Expansion  |  \u2615 Growth strategies\n\n"
    "Just ask me a business question and I'll crunch the numbers for you!"
)


def _chitchat_reply(intent: Intent) -> str:
    """Generate a friendly conversational reply using GPT-4o, with a static fallback."""
    import os, json, logging as _log
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": (
                        "You are the friendly AI assistant for Conut, a bakery & cafe chain "
                        "with 4 branches in Lebanon. You handle greetings and small talk warmly. "
                        "Keep replies short (2-3 sentences max), friendly, and always gently "
                        "remind the user you can help with: combo optimization, demand forecasting, "
                        "staffing, expansion feasibility, and coffee/milkshake growth strategies. "
                        "Use a few emojis to keep it fun. Never use markdown headers."
                    )},
                    {"role": "user", "content": intent.raw_question or "hello"},
                ],
                temperature=0.8,
                max_tokens=150,
            )
            return resp.choices[0].message.content or _STATIC_CHITCHAT
        except Exception as exc:
            _log.getLogger(__name__).warning("Chitchat LLM failed: %s", exc)
    return _STATIC_CHITCHAT


def dispatch(intent: Intent) -> dict[str, Any]:
    """Route an Intent to the correct service and return a wrapped result."""

    branch = intent.branch
    branches_to_query = (
        KNOWN_BRANCHES if branch == "all" else
        [branch] if branch else
        KNOWN_BRANCHES            # default → all when branch not mentioned
    )

    action = intent.action

    # ── combo ───────────────────────────────────────────────────────────
    if action == "combo":
        if len(branches_to_query) == 1:
            return _safe_call(_combo, branch=branches_to_query[0], top_k=intent.top_k)
        return _multi_branch(_combo, branches_to_query, top_k=intent.top_k)

    # ── forecast ────────────────────────────────────────────────────────
    if action == "forecast":
        if len(branches_to_query) == 1:
            return _safe_call(_forecast, branch=branches_to_query[0], horizon=intent.horizon_months)
        return _multi_branch(_forecast, branches_to_query, horizon=intent.horizon_months)

    # ── staffing ────────────────────────────────────────────────────────
    if action == "staffing":
        shift = intent.shift or DEFAULT_SHIFT
        if len(branches_to_query) == 1:
            return _safe_call(_staffing, branch=branches_to_query[0], shift=shift)
        return _multi_branch(_staffing, branches_to_query, shift=shift)

    # ── expansion ───────────────────────────────────────────────────────
    if action == "expansion":
        # expansion already handles "" as "all branches"
        b = branches_to_query[0] if len(branches_to_query) == 1 else ""
        return _safe_call(_expansion, branch=b)

    # ── growth ──────────────────────────────────────────────────────────
    if action == "growth":
        # growth_strategy handles "all" internally, so pass directly
        if len(branches_to_query) == 1:
            return _safe_call(_growth, branch=branches_to_query[0])
        return _safe_call(_growth, branch="all")

    # ── chitchat ────────────────────────────────────────────────────────
    if action == "chitchat":
        reply = _chitchat_reply(intent)
        return {"success": True, "data": {"reply": reply}, "error": None}

    # ── unknown ─────────────────────────────────────────────────────────
    return {
        "success": False,
        "data": None,
        "error": "Could not determine what you are asking about.",
    }
