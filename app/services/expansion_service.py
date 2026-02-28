"""
expansion_service.py
--------------------
Branch expansion feasibility engine.

Evaluates whether Conut should open a new branch by scoring every existing
branch across **6 KPI dimensions**, identifying the best-performing archetype,
and ranking **candidate Lebanese locations** where that archetype could be
replicated.

Scorecard dimensions (default weights):
  1. Demand trend        (0.25)  — month-over-month revenue growth trajectory
  2. Branch strength     (0.20)  — total revenue relative to peers
  3. Avg-ticket health   (0.15)  — average spend per customer × channel breadth
  4. Repeat-customer     (0.10)  — % of delivery customers who ordered >1 time
  5. Product-mix breadth (0.15)  — unique SKU count + category concentration
  6. Beverage attachment (0.15)  — beverage revenue as % of product-item total

External data:
  data/external/lebanon_candidate_areas.csv
  Hand-curated from publicly available sources (Wikipedia population data,
  general commercial knowledge of Lebanese cities/towns).  Justified per
  hackathon rule 3: "External data is allowed only if clearly documented
  and justified."

Data sources (internal):
  - monthly_sales_by_branch.csv   → demand trend, branch strength
  - avg_sales_by_menu_channel.csv → avg ticket, channel diversity
  - customer_orders_delivery.csv  → repeat-customer signal
  - Sales by items and groups.csv → product-mix breadth
  - Summary by division-menu channel.csv → beverage attachment
"""

from __future__ import annotations

import functools
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent.parent
_PROC = _PROJECT / "data" / "processed"
_EXT = _PROJECT / "data" / "external"

_MONTHLY_SALES = _PROC / "monthly_sales_by_branch.csv"
_AVG_CHANNEL = _PROC / "avg_sales_by_menu_channel.csv"
_CUST_ORDERS = _PROC / "customer_orders_delivery.csv"
_ITEM_SALES = _PROC / "Sales by items and groups.csv"
_DIV_CHANNEL = _PROC / "Summary by division-menu channel.csv"
_AREAS = _EXT / "lebanon_candidate_areas.csv"

# Month ordering for chronological sort
_MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

# Beverage division names in the division-channel summary
_BEVERAGE_DIVISIONS = {
    "Hot-Coffee Based", "Frappes", "Shakes",
    "Hot and Cold Drinks", "Bev Add-ons",
}

# Default scorecard weights (sum to 1.0)
DEFAULT_WEIGHTS: dict[str, float] = {
    "demand_trend": 0.25,
    "branch_strength": 0.20,
    "avg_ticket_health": 0.15,
    "repeat_customer": 0.10,
    "product_mix": 0.15,
    "beverage_attachment": 0.15,
}


# ---------------------------------------------------------------------------
# Data loaders (cached)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_monthly_sales() -> pd.DataFrame:
    df = pd.read_csv(_MONTHLY_SALES)
    df["month_num"] = df["month"].map(_MONTH_ORDER)
    df.sort_values(["branch", "year", "month_num"], inplace=True)
    return df


@functools.lru_cache(maxsize=1)
def _load_avg_channel() -> pd.DataFrame:
    return pd.read_csv(_AVG_CHANNEL)


@functools.lru_cache(maxsize=1)
def _load_cust_orders() -> pd.DataFrame:
    return pd.read_csv(_CUST_ORDERS)


@functools.lru_cache(maxsize=1)
def _load_item_sales() -> pd.DataFrame:
    return pd.read_csv(_ITEM_SALES)


@functools.lru_cache(maxsize=1)
def _load_div_channel() -> pd.DataFrame:
    return pd.read_csv(_DIV_CHANNEL)


@functools.lru_cache(maxsize=1)
def _load_candidate_areas() -> pd.DataFrame:
    if not _AREAS.exists():
        raise FileNotFoundError(
            f"External candidate-areas file not found at {_AREAS}. "
            "Expected data/external/lebanon_candidate_areas.csv."
        )
    return pd.read_csv(_AREAS)


# ---------------------------------------------------------------------------
# Per-branch KPI calculators
# ---------------------------------------------------------------------------

def _demand_trend_score(branch: str, ms: pd.DataFrame) -> tuple[float, dict]:
    """Score 0-100 based on MoM growth trend.  Positive → higher score."""
    bdf = ms[ms["branch"] == branch].sort_values(["year", "month_num"])
    totals = bdf["total"].tolist()
    if len(totals) < 2:
        return 50.0, {"mom_growth_rates": [], "avg_mom_growth_pct": 0.0}

    growths: list[float] = []
    for i in range(1, len(totals)):
        if totals[i - 1] > 0:
            growths.append((totals[i] - totals[i - 1]) / totals[i - 1] * 100)
    avg_growth = sum(growths) / len(growths) if growths else 0.0

    # Map avg MoM growth % → 0-100 score
    # -50% or worse → 0,  0% → 50,  +100% or better → 100
    raw = 50 + avg_growth * 0.5
    score = max(0.0, min(100.0, raw))
    return round(score, 2), {
        "mom_growth_rates": [round(g, 2) for g in growths],
        "avg_mom_growth_pct": round(avg_growth, 2),
    }


def _branch_strength_score(branch: str, ms: pd.DataFrame,
                           all_totals: dict[str, float]) -> tuple[float, dict]:
    """Score 0-100 based on total revenue rank among peers."""
    total = all_totals.get(branch, 0.0)
    max_total = max(all_totals.values()) if all_totals else 1.0
    score = (total / max_total) * 100 if max_total > 0 else 0.0
    return round(score, 2), {"total_revenue": round(total, 2)}


def _avg_ticket_score(branch: str, ch: pd.DataFrame) -> tuple[float, dict]:
    """Score 0-100 combining avg-per-customer and channel diversity."""
    bch = ch[ch["branch"] == branch]
    if bch.empty:
        return 50.0, {"avg_ticket": 0.0, "channels": 0}

    avg_ticket = bch["avg_per_customer"].mean()
    n_channels = len(bch)

    # Normalize ticket: use max across all branches
    all_avg = ch.groupby("branch")["avg_per_customer"].mean()
    max_avg = all_avg.max() if len(all_avg) else 1.0
    ticket_norm = (avg_ticket / max_avg) * 100 if max_avg > 0 else 0.0

    # Channel diversity bonus: 1 channel → 0, 2 → 20, 3 → 40
    diversity_bonus = min((n_channels - 1) * 20, 40)

    # Weighted combination: 70% ticket + 30% diversity (base 30 for single channel)
    score = ticket_norm * 0.7 + diversity_bonus * 0.3 + 30 * 0.3
    score = max(0.0, min(100.0, score))
    return round(score, 2), {
        "avg_ticket": round(avg_ticket, 2),
        "channels": n_channels,
        "channel_list": bch["channel"].tolist(),
    }


def _repeat_customer_score(branch: str, co: pd.DataFrame) -> tuple[float, dict]:
    """Score 0-100 based on % of delivery customers who ordered more than once."""
    bco = co[co["branch"] == branch]
    if bco.empty:
        # No delivery data → neutral score
        return 50.0, {
            "total_customers": 0,
            "repeat_customers": 0,
            "repeat_pct": 0.0,
            "note": "No delivery customer data available; neutral score applied.",
        }

    total_cust = len(bco)
    repeat_cust = int((bco["num_orders"] > 1).sum())
    repeat_pct = (repeat_cust / total_cust) * 100 if total_cust > 0 else 0.0

    # Map repeat_pct to 0-100.  0% → 20, 30%+ → 100
    score = 20 + repeat_pct * (80 / 30)
    score = max(0.0, min(100.0, score))
    return round(score, 2), {
        "total_customers": total_cust,
        "repeat_customers": repeat_cust,
        "repeat_pct": round(repeat_pct, 2),
    }


def _product_mix_score(branch: str, items: pd.DataFrame) -> tuple[float, dict]:
    """Score 0-100 using unique SKU count + revenue concentration (Herfindahl)."""
    bi = items[items["branch"] == branch]
    if bi.empty:
        return 50.0, {"unique_skus": 0, "divisions": 0, "herfindahl": 1.0}

    n_skus = bi["description"].nunique()
    n_divs = bi["division"].nunique()

    # Revenue Herfindahl index by division (lower = more diversified = better)
    div_rev = bi.groupby("division")["total_amount"].sum()
    total_rev = div_rev.sum()
    if total_rev > 0:
        shares = div_rev / total_rev
        hhi = float((shares ** 2).sum())
    else:
        hhi = 1.0

    # Normalize: max SKUs across all branches → 100
    all_skus = items.groupby("branch")["description"].nunique()
    max_skus = all_skus.max() if len(all_skus) else 1
    sku_norm = (n_skus / max_skus) * 100 if max_skus > 0 else 0.0

    # Herfindahl: 0 → perfectly diversified, 1 → single division
    # Map inversely: HHI 0.0 → 100, HHI 1.0 → 0
    hhi_score = (1 - hhi) * 100

    # 60% SKU breadth + 40% diversification
    score = sku_norm * 0.6 + hhi_score * 0.4
    score = max(0.0, min(100.0, score))
    return round(score, 2), {
        "unique_skus": int(n_skus),
        "divisions": int(n_divs),
        "herfindahl": round(hhi, 4),
    }


def _beverage_attachment_score(branch: str,
                               dc: pd.DataFrame) -> tuple[float, dict]:
    """Score 0-100 based on beverage revenue as % of total product (ITEMS) revenue."""
    bdc = dc[dc["section"] == branch]
    if bdc.empty:
        return 50.0, {"beverage_revenue": 0.0, "items_revenue": 0.0, "bev_pct": 0.0}

    items_row = bdc[bdc["item"] == "ITEMS"]
    bev_rows = bdc[bdc["item"].isin(_BEVERAGE_DIVISIONS)]

    items_total = float(items_row["total"].sum()) if not items_row.empty else 0.0
    bev_total = float(bev_rows["total"].sum()) if not bev_rows.empty else 0.0
    bev_pct = (bev_total / items_total * 100) if items_total > 0 else 0.0

    # Map bev_pct to score.  0% → 0, 20%+ → 100
    score = min(bev_pct * (100 / 20), 100.0)
    score = max(0.0, score)
    return round(score, 2), {
        "beverage_revenue": round(bev_total, 2),
        "items_revenue": round(items_total, 2),
        "bev_pct": round(bev_pct, 2),
    }


# ---------------------------------------------------------------------------
# Candidate location scorer
# ---------------------------------------------------------------------------

def _score_candidate_locations(
    archetype_profile: dict,
    areas: pd.DataFrame,
) -> list[dict]:
    """Score candidate areas based on attractiveness × archetype fit."""

    density_map = {"low": 1, "medium": 2, "high": 3}
    scored: list[dict] = []

    for _, row in areas.iterrows():
        if row["conut_present"] == 1:
            continue  # skip areas where Conut already exists

        # Area attractiveness (0-100 scale)
        pop_score = min(row["estimated_population"] / 5000, 100)   # 500k → 100
        uni_bonus = 15 if row["university_nearby"] == 1 else 0
        foot = row["foot_traffic_tier"] * 20        # 1-5 → 20-100
        rent_penalty = row["commercial_rent_tier"] * 5  # 1-5 → 5-25
        cafe_density = density_map.get(row["estimated_cafe_density"], 1)
        # Medium café density is ideal (market exists but not saturated)
        cafe_score = {1: 30, 2: 50, 3: 35}.get(cafe_density, 30)

        attractiveness = (
            pop_score * 0.30
            + uni_bonus
            + foot * 0.25
            + cafe_score * 0.20
            - rent_penalty * 0.10
        )
        attractiveness = max(0, min(100, attractiveness))

        # Build rationale
        pros: list[str] = []
        cons: list[str] = []
        if row["estimated_population"] >= 100000:
            pros.append(f"Large population ({row['estimated_population']:,})")
        elif row["estimated_population"] >= 50000:
            pros.append(f"Mid-size population ({row['estimated_population']:,})")
        else:
            cons.append(f"Small population ({row['estimated_population']:,})")

        if row["university_nearby"] == 1:
            pros.append("University nearby (young demographic)")
        if row["foot_traffic_tier"] >= 4:
            pros.append("High foot traffic")
        if row["commercial_rent_tier"] >= 4:
            cons.append(f"High commercial rent (tier {row['commercial_rent_tier']}/5)")
        if cafe_density == 3:
            cons.append("High cafe density — competitive market")
        elif cafe_density == 2:
            pros.append("Moderate cafe scene — market exists but not saturated")
        else:
            pros.append("Low cafe density — first-mover opportunity")

        scored.append({
            "area": row["area"],
            "governorate": row["governorate"],
            "score": round(attractiveness, 2),
            "population": int(row["estimated_population"]),
            "university_nearby": bool(row["university_nearby"]),
            "foot_traffic_tier": int(row["foot_traffic_tier"]),
            "rent_tier": int(row["commercial_rent_tier"]),
            "cafe_density": row["estimated_cafe_density"],
            "pros": pros,
            "cons": cons,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_expansion(branch: str = "") -> dict:
    """
    Score all branches, identify best archetype, rank candidate locations.

    Parameters
    ----------
    branch : str
        Optional.  If empty or "all", score every branch and recommend.
        If a specific branch name, focus the archetype recommendation on it.
    """

    # ── Load all data ─────────────────────────────────────────────────────
    ms = _load_monthly_sales()
    ch = _load_avg_channel()
    co = _load_cust_orders()
    items = _load_item_sales()
    dc = _load_div_channel()
    areas = _load_candidate_areas()

    branches = sorted(ms["branch"].unique().tolist())

    # Validate branch input (case-insensitive)
    branch_label = branch.strip()
    if branch_label and branch_label.lower() != "all":
        branch_map = {b.lower(): b for b in branches}
        matched = branch_map.get(branch_label.lower())
        if not matched:
            close = [b for b in branches if branch_label.lower() in b.lower()]
            return {
                "error": f"Unknown branch '{branch_label}'.",
                "available_branches": branches,
                "did_you_mean": close or None,
            }
        branch_label = matched  # use canonical casing

    # ── Pre-compute shared metrics ────────────────────────────────────────
    all_totals: dict[str, float] = (
        ms.groupby("branch")["total"].sum().to_dict()
    )

    # ── Score each branch ─────────────────────────────────────────────────
    scorecards: list[dict] = []
    for b in branches:
        demand_sc, demand_det = _demand_trend_score(b, ms)
        strength_sc, strength_det = _branch_strength_score(b, ms, all_totals)
        ticket_sc, ticket_det = _avg_ticket_score(b, ch)
        repeat_sc, repeat_det = _repeat_customer_score(b, co)
        mix_sc, mix_det = _product_mix_score(b, items)
        bev_sc, bev_det = _beverage_attachment_score(b, dc)

        dimensions = {
            "demand_trend": {"score": demand_sc, "detail": demand_det},
            "branch_strength": {"score": strength_sc, "detail": strength_det},
            "avg_ticket_health": {"score": ticket_sc, "detail": ticket_det},
            "repeat_customer": {"score": repeat_sc, "detail": repeat_det},
            "product_mix": {"score": mix_sc, "detail": mix_det},
            "beverage_attachment": {"score": bev_sc, "detail": bev_det},
        }

        composite = sum(
            dimensions[dim]["score"] * DEFAULT_WEIGHTS[dim]
            for dim in DEFAULT_WEIGHTS
        )

        scorecards.append({
            "branch": b,
            "dimensions": dimensions,
            "composite_score": round(composite, 2),
        })

    # ── Identify best archetype ───────────────────────────────────────────
    scorecards.sort(key=lambda s: s["composite_score"], reverse=True)
    best = scorecards[0]

    # Build archetype profile from the best branch
    best_branch = best["branch"]
    bch = ch[ch["branch"] == best_branch]
    channel_mix = {
        row["channel"]: round(row["sales"], 2)
        for _, row in bch.iterrows()
    }

    # Top 5 revenue divisions for the best branch
    bi = items[items["branch"] == best_branch]
    if not bi.empty:
        top_divs = (
            bi.groupby("division")["total_amount"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        top_categories = {k: round(v, 2) for k, v in top_divs.items()}
    else:
        top_categories = {}

    bev_pct = best["dimensions"]["beverage_attachment"]["detail"].get("bev_pct", 0)

    archetype_profile = {
        "branch": best_branch,
        "composite_score": best["composite_score"],
        "channel_mix": channel_mix,
        "top_categories": top_categories,
        "beverage_pct": bev_pct,
        "recommendation": (
            f"Replicate the '{best_branch}' operating model: "
            f"{', '.join(channel_mix.keys())} channels, "
            f"{bev_pct:.1f}% beverage attachment."
        ),
    }

    # ── Expansion verdict ─────────────────────────────────────────────────
    top_score = best["composite_score"]
    if top_score >= 65:
        verdict = "GO"
        verdict_detail = (
            f"Expansion is recommended. The best archetype ('{best_branch}') "
            f"scores {top_score}/100, indicating a strong replicable profile."
        )
    elif top_score >= 45:
        verdict = "CAUTION"
        verdict_detail = (
            f"Expansion is conditionally feasible. The best archetype scores "
            f"{top_score}/100 — proceed with limited pilot and close monitoring."
        )
    else:
        verdict = "NO-GO"
        verdict_detail = (
            f"Expansion is not recommended at this time. The best archetype "
            f"scores only {top_score}/100 — focus on strengthening existing "
            f"branches first."
        )

    # ── Candidate locations ───────────────────────────────────────────────
    candidate_locations = _score_candidate_locations(archetype_profile, areas)

    # ── Risks and assumptions ─────────────────────────────────────────────
    risks = [
        "Sales data covers only 4-5 months (Aug-Dec 2025); trends may not persist.",
        "Numeric values are intentionally scaled — scores reflect relative "
        "patterns, not absolute revenue.",
        "Repeat-customer signal is delivery-only; TABLE/TAKE-AWAY repeat "
        "behavior is unobserved.",
        "Candidate location scores use curated external data (population, "
        "foot traffic tiers) — not precise real-estate analytics.",
        "Main Street Coffee has only 4 months of data (Sep-Dec), potentially "
        "biasing its trend score.",
    ]

    # ── Explanation ───────────────────────────────────────────────────────
    explanation = (
        f"Scored {len(branches)} branches across 6 KPI dimensions "
        f"(demand trend, branch strength, avg ticket, repeat customers, "
        f"product mix, beverage attachment). "
        f"Best archetype: '{best_branch}' with composite score "
        f"{top_score}/100. Verdict: {verdict}. "
        f"Ranked {len(candidate_locations)} candidate Lebanese locations "
        f"for expansion (excluding areas where Conut is already present). "
        f"Data sources: monthly sales, channel summary, delivery customer "
        f"orders, item-level sales, division-channel breakdown, plus "
        f"external area data."
    )

    return {
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "best_archetype": archetype_profile,
        "scorecards": scorecards,
        "candidate_locations": candidate_locations[:10],
        "risks": risks,
        "explanation": explanation,
    }
