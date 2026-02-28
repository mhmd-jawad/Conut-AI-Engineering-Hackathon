"""
Response formatter – converts raw service dicts into concise, human-readable
Markdown text so the agent's answers are immediately useful.

One formatter per intent + a fallback for ``unknown``.
"""

from __future__ import annotations

from typing import Any


# ── helpers ─────────────────────────────────────────────────────────────

def _num(v: Any, precision: int = 1) -> str:
    """Format a number nicely (add commas, round)."""
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return f"{v:,.{precision}f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def _compact(v: Any) -> str:
    """Format a large number in compact form (e.g. 1.2B, 345.6M, 12.3K)."""
    if v is None:
        return "N/A"
    n = float(v)
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:,.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:,.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:,.1f}K"
    return f"{n:,.1f}"


def _pct(v: Any) -> str:
    if v is None:
        return "N/A"
    return f"{float(v):.1f}%"


# ── Combo ───────────────────────────────────────────────────────────────

def _format_combo(data: dict) -> str:
    lines: list[str] = []
    branch = data.get("branch", "All")
    total_baskets = data.get("total_baskets", "?")
    lines.append(f"🍩  *Combo Recommendations — {branch}*")
    lines.append(f"📊  Based on {_num(total_baskets)} baskets analysed\n")

    combos = data.get("combos") or data.get("recommendations") or []
    if not combos:
        lines.append("No significant combos found with current thresholds.")
        return "\n".join(lines)

    for i, c in enumerate(combos, 1):
        a = c.get("item_a", c.get("item_1", "?"))
        b = c.get("item_b", c.get("item_2", "?"))
        lift = c.get("lift", 0)
        conf = c.get("confidence_a_to_b", c.get("confidence", 0))
        supp = c.get("support", 0)
        price = c.get("suggested_bundle_price")

        conf_val = conf * 100 if conf < 1 else conf
        supp_val = supp * 100 if supp < 1 else supp

        lines.append(f"━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"*{i}.  {a}  +  {b}*")
        lines.append(f"    📈  Lift: *{_num(lift)}×*")
        lines.append(f"    ✅  Confidence: *{_pct(conf_val)}*")
        lines.append(f"    📦  Support: *{_pct(supp_val)}*")
        if price:
            lines.append(f"    💰  Bundle price: *${_num(price)}*")
        lines.append("")

    return "\n".join(lines)


# ── Forecast ────────────────────────────────────────────────────────────

def _format_forecast(data: dict) -> str:
    lines: list[str] = []
    branch = data.get("branch", "?")
    trend = data.get("trend", data.get("trend_classification", "N/A"))
    confidence = data.get("confidence", "N/A")
    demand_idx = data.get("demand_index")
    mom = data.get("avg_mom_growth_pct", data.get("mom_growth_pct"))
    horizon = data.get("horizon_months", "?")

    lines.append(f"📈  *Demand Forecast — {branch}*")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━\n")

    # Summary metrics
    lines.append(f"🔹  Trend: *{trend.title()}*")
    lines.append(f"🔹  Avg Month-over-Month Growth: *{_pct(mom) if mom is not None else 'N/A'}*")
    lines.append(f"🔹  Confidence: *{confidence.title() if isinstance(confidence, str) else confidence}*")
    if demand_idx is not None:
        lines.append(f"🔹  Demand Share (vs all branches): *{_pct(demand_idx * 100)}*")
    lines.append(f"🔹  Forecast Horizon: *{horizon} month(s)*\n")

    # Historical data
    history = data.get("history") or []
    if history:
        lines.append("📊  *Recent History:*\n")
        for h in history:
            month_name = h.get("month", "?")
            total = h.get("total", 0)
            lines.append(f"    📅  {month_name}: *{_compact(total)}*")
        lines.append("")

    # Forecasts
    forecasts = data.get("forecasts") or []
    if forecasts:
        lines.append("🔮  *Monthly Projections:*\n")
        for fc in forecasts:
            label = fc.get("month", fc.get("label", "?"))
            naive = fc.get("naive")
            wma = fc.get("wma")
            trend_r = fc.get("trend")
            ens = fc.get("ensemble")

            lines.append(f"  ━━  *{label}*")
            if naive is not None:
                lines.append(f"      📌  Naive Baseline:  *{_compact(naive)}*")
            if wma is not None:
                lines.append(f"      📐  Weighted Moving Avg:  *{_compact(wma)}*")
            if trend_r is not None:
                lines.append(f"      📈  Trend Regression:  *{_compact(trend_r)}*")
            if ens is not None:
                lines.append(f"      ⭐  Ensemble (Final):  *{_compact(ens)}*")
            lines.append("")

    # Anomaly notes
    anomaly_notes = data.get("anomaly_notes") or data.get("anomalies") or []
    if anomaly_notes:
        lines.append("⚠️  *Anomaly Notes:*")
        for note in anomaly_notes:
            if isinstance(note, str):
                lines.append(f"  ❗ {note}")
            elif isinstance(note, dict):
                lines.append(f"  ❗ {note.get('label', '?')}: {_num(note.get('value'))} (median {_num(note.get('median'))})")
        lines.append("")

    # Explanation
    explanation = data.get("explanation")
    if explanation:
        lines.append(f"💡  _{explanation}_")

    return "\n".join(lines)


# ── Staffing ────────────────────────────────────────────────────────────

def _format_staffing(data: dict) -> str:
    lines: list[str] = []
    branch = data.get("branch", "?")
    shift = data.get("shift", "?")
    lines.append(f"👥  *Staffing — {branch}*")
    lines.append(f"🕐  Shift: *{shift}*\n")

    scenarios = data.get("scenarios") or {}
    if scenarios:
        for label, info in scenarios.items():
            head = info if isinstance(info, (int, float)) else info.get("headcount", info)
            emoji = "🟢" if "low" in label.lower() else ("🟡" if "mid" in label.lower() or "medium" in label.lower() else "🔴")
            lines.append(f"  {emoji}  {label.title()}:  *{_num(head)} staff*")

    rationale = data.get("rationale") or data.get("notes")
    if rationale:
        lines.append(f"\n💡  {rationale}")

    return "\n".join(lines)


# ── Expansion ───────────────────────────────────────────────────────────

def _format_expansion(data: dict) -> str:
    lines: list[str] = []
    lines.append("🏗  *Expansion Feasibility Report*\n")

    verdict = data.get("verdict", "N/A")
    lines.append(f"📋  Verdict: *{verdict}*\n")

    # Best archetype
    archetype = data.get("best_archetype") or {}
    if archetype:
        lines.append(f"🏆  Best archetype: *{archetype.get('branch', '?')}*")
        lines.append(f"    Score: *{_num(archetype.get('total_score'))}*\n")

    # Scorecards
    scorecards = data.get("branch_scorecards") or []
    if scorecards:
        lines.append("📊  *Branch Scores:*")
        for sc in scorecards:
            lines.append(f"  🔹  {sc.get('branch', '?')}:  *{_num(sc.get('total_score'))}*")
        lines.append("")

    # Candidate locations
    candidates = data.get("candidate_locations") or []
    if candidates:
        lines.append("📍  *Top Candidate Locations:*\n")
        for i, loc in enumerate(candidates[:5], 1):
            name = loc.get("area", loc.get("name", "?"))
            score = loc.get("location_score", loc.get("score", "?"))
            lines.append(f"  {i}.  *{name}* — score {_num(score)}")

    return "\n".join(lines)


# ── Growth ──────────────────────────────────────────────────────────────

def _format_growth(data: dict) -> str:
    lines: list[str] = []
    branch = data.get("branch", "?")
    lines.append(f"☕  *Coffee & Milkshake Growth — {branch}*\n")

    profiles = data.get("branches") or []
    if isinstance(profiles, list) and profiles:
        for prof in profiles:
            b_name = prof.get("branch", branch)
            pen = prof.get("beverage_penetration_pct")

            lines.append(f"━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🏪  *{b_name}*")
            if pen is not None:
                lines.append(f"    🥤  Beverage penetration: *{_pct(pen)}*")
            rank = prof.get("penetration_rank")
            if rank:
                lines.append(f"    🏅  Rank: *#{rank}*")
            coffee_rev = prof.get("coffee_revenue")
            shake_rev = prof.get("milkshake_revenue")
            if coffee_rev is not None:
                lines.append(f"    ☕  Coffee revenue: *{_num(coffee_rev)}*")
            if shake_rev is not None:
                lines.append(f"    🥛  Milkshake revenue: *{_num(shake_rev)}*")

            heroes_c = prof.get("hero_coffee_items") or []
            if heroes_c:
                items = [h.get("description") or h.get("item") or str(h) if isinstance(h, dict) else str(h) for h in heroes_c[:3]]
                lines.append(f"    ⭐  Hero coffee: {', '.join(items)}")

            heroes_s = prof.get("hero_milkshake_items") or []
            if heroes_s:
                items = [h.get("description") or h.get("item") or str(h) if isinstance(h, dict) else str(h) for h in heroes_s[:3]]
                lines.append(f"    ⭐  Hero milkshake: {', '.join(items)}")

            under = prof.get("underperforming_items") or []
            if under:
                lines.append(f"\n    ⚠️  *Underperforming (≥40% gap):*")
                for u in under[:5]:
                    if isinstance(u, dict):
                        lines.append(f"      ❗ {u.get('description') or u.get('item') or u.get('product', '?')}: gap {_pct(u.get('gap_pct', 0))}")
                    else:
                        lines.append(f"      ❗ {u}")

            actions = prof.get("actions") or []
            if actions:
                lines.append(f"\n    💡  *Recommendations:*")
                for i, a in enumerate(actions, 1):
                    if isinstance(a, dict):
                        text = a.get("recommendation") or a.get("action") or a.get("text") or str(a)
                        lines.append(f"      {i}. {text}")
                    else:
                        lines.append(f"      {i}. {a}")

            lines.append("")
        return "\n".join(lines)

    # Fallback: old format
    metrics = data.get("key_metrics") or data.get("branch_profile") or {}
    if metrics:
        bev = metrics.get("beverage_penetration") or metrics.get("beverage_penetration_pct")
        if bev is not None:
            lines.append(f"    🥤  Beverage penetration: *{_pct(bev if bev > 1 else bev * 100)}*")
        hero = metrics.get("hero_product") or metrics.get("hero_products")
        if hero:
            if isinstance(hero, list):
                lines.append(f"    ⭐  Hero products: {', '.join(str(h) for h in hero[:3])}")
            else:
                lines.append(f"    ⭐  Hero product: {hero}")

    recs = data.get("recommendations") or []
    if recs:
        lines.append(f"\n💡  *Recommendations:*")
        for i, r in enumerate(recs, 1):
            if isinstance(r, dict):
                text = r.get("recommendation") or r.get("action") or r.get("text") or str(r)
                lines.append(f"  {i}. {text}")
            else:
                lines.append(f"  {i}. {r}")

    return "\n".join(lines)


# ── Multi-branch wrapper ───────────────────────────────────────────────

def _format_multi(data: dict, single_formatter) -> str:
    """Format results when the agent queried multiple branches."""
    branches = data.get("branches", {})
    parts: list[str] = []
    if isinstance(branches, dict):
        for branch_name, branch_data in branches.items():
            parts.append(single_formatter(branch_data))
    elif isinstance(branches, list):
        for branch_data in branches:
            parts.append(single_formatter(branch_data))
    else:
        parts.append(single_formatter(data))
    return "\n\n---\n\n".join(parts)


# ── Unknown / fallback ─────────────────────────────────────────────────

HELP_TEXT = (
    "🤖  *Conut Operations Agent*\n\n"
    "I can help you with:\n\n"
    "1️⃣  *Combo Optimization*\n"
    "      Find best product bundles\n"
    '      _"What are the top combos for Conut Jnah?"_\n\n'
    "2️⃣  *Demand Forecasting*\n"
    "      Predict future branch sales\n"
    '      _"Forecast demand for Conut - Tyre next 4 months"_\n\n'
    "3️⃣  *Staffing Estimation*\n"
    "      Staff needs per shift\n"
    '      _"How many staff for the evening shift?"_\n\n'
    "4️⃣  *Expansion Feasibility*\n"
    "      Should we open a new branch?\n"
    '      _"Is expansion feasible?"_\n\n'
    "5️⃣  *Coffee & Milkshake Growth*\n"
    "      Strategies to boost beverages\n"
    '      _"Growth strategy for Main Street Coffee"_\n\n'
    "💬  Try asking a question about any of these topics!"
)


# ── Public API ──────────────────────────────────────────────────────────

def _format_chitchat(data: dict) -> str:
    """Pass through the conversational reply from the LLM."""
    return data.get("reply", "\U0001f44b Hey! Ask me a business question about Conut.")


_FORMATTERS: dict[str, Any] = {
    "combo":     _format_combo,
    "forecast":  _format_forecast,
    "staffing":  _format_staffing,
    "expansion": _format_expansion,
    "growth":    _format_growth,
    "chitchat":  _format_chitchat,
}


def format_response(action: str, data: dict | None, error: str | None) -> str:
    """Return a human-readable Markdown answer."""

    if error and data is None:
        return f"⚠ **Error:** {error}\n\n" + HELP_TEXT

    if action == "unknown" or action not in _FORMATTERS:
        return HELP_TEXT

    formatter = _FORMATTERS[action]

    # multi-branch result?  Only _multi_branch dispatch wraps in {"branches": {dict}}.
    # Services like growth naturally have "branches" as a list — don't reroute those.
    if data and isinstance(data.get("branches"), dict):
        return _format_multi(data, formatter)

    return formatter(data or {})
