"""
combo_service.py
----------------
Basket-analysis combo recommendation engine.

Uses data/processed/basket_lines.csv (produced by pipelines/clean_00502_baskets.py).
Each row is an item in a customer's basket (delivery channel, Jan 2026).
~98 % of customers placed exactly one order, so Customer Name ≈ order basket.

Algorithm:
  1. Filter cancellations (always) and modifiers (optional).
  2. Build baskets: basket_id → set of unique Item Descriptions.
  3. Generate all 2-item combinations per basket.
  4. Compute support, confidence (both directions), and lift for each pair.
  5. Compute revenue impact: avg combined revenue when both items are in a basket.
  6. Suggest combo pricing: 12 % bundle discount from sum of individual prices.
  7. Filter by thresholds, rank by lift desc, return top-K.
"""

from __future__ import annotations

import functools
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "basket_lines.csv"


# ---------------------------------------------------------------------------
# Data loader (cached so we only read the CSV once per process)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_basket_lines() -> pd.DataFrame:
    """Read basket_lines.csv and return a DataFrame."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"basket_lines.csv not found at {DATA_PATH}. "
            "Run  python pipelines/clean_00502_baskets.py  first."
        )
    df = pd.read_csv(DATA_PATH)
    # Ensure consistent types
    df["Is Cancellation"] = df["Is Cancellation"].astype(int)
    df["Is_Modifier"] = df["Is_Modifier"].astype(int)
    return df


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def recommend_combos(
    branch: str,
    top_k: int = 5,
    include_modifiers: bool = False,
    min_support: float = 0.02,
    min_confidence: float = 0.15,
    min_lift: float = 1.0,
) -> dict:
    """Return top-K combo recommendations for *branch* (or 'all')."""

    df = _load_basket_lines()

    # ── 1. Filter ──────────────────────────────────────────────────────────
    # Always drop cancellations
    df = df[df["Is Cancellation"] == 0].copy()

    # Always drop non-product rows (DELIVERY CHARGE is a logistics fee)
    NON_PRODUCTS = {"DELIVERY CHARGE"}
    df = df[~df["Item Description"].str.upper().isin(NON_PRODUCTS)]

    # Optionally drop modifiers (Price == 0 items like WHIPPED CREAM)
    if not include_modifiers:
        df = df[df["Is_Modifier"] == 0]

    # Branch filter
    branch_label = branch.strip()
    if branch_label.lower() != "all":
        df = df[df["Branch"].str.strip().str.lower() == branch_label.lower()]
        if df.empty:
            return _empty_response(branch_label, include_modifiers)

    # ── 2. Build baskets + revenue lookup ──────────────────────────────────
    baskets: dict[str, set[str]] = {}
    basket_revenue: dict[str, dict[str, float]] = {}  # basket_id → {item → line_total}
    for basket_id, group in df.groupby("basket_id"):
        items = set(group["Item Description"].unique())
        if len(items) >= 2:
            baskets[basket_id] = items
            # Sum Line Total per item within this basket
            rev = group.groupby("Item Description")["Line Total"].sum().to_dict()
            basket_revenue[basket_id] = rev

    # Per-item average price (used for bundle pricing)
    item_avg_price: dict[str, float] = (
        df[df["Price"] > 0]
        .groupby("Item Description")["Price"]
        .mean()
        .to_dict()
    )

    total_baskets = len(baskets)
    if total_baskets == 0:
        return _empty_response(branch_label, include_modifiers)

    # ── 3. Count item frequencies & pair frequencies ───────────────────────
    item_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    for items in baskets.values():
        for item in items:
            item_counts[item] += 1
        for pair in combinations(sorted(items), 2):
            pair_counts[pair] += 1

    # ── 4. Compute metrics ─────────────────────────────────────────────────
    results: list[dict] = []
    for (item_a, item_b), count_ab in pair_counts.items():
        support = count_ab / total_baskets
        if support < min_support:
            continue

        support_a = item_counts[item_a] / total_baskets
        support_b = item_counts[item_b] / total_baskets

        confidence_a_to_b = count_ab / item_counts[item_a]  # P(B|A)
        confidence_b_to_a = count_ab / item_counts[item_b]  # P(A|B)

        lift = support / (support_a * support_b) if (support_a * support_b) > 0 else 0.0

        if confidence_a_to_b < min_confidence and confidence_b_to_a < min_confidence:
            continue
        if lift < min_lift:
            continue

        # ── Revenue impact: avg combined revenue in baskets containing both ──
        combo_revenues: list[float] = []
        for bid, items in baskets.items():
            if item_a in items and item_b in items:
                rev_a = basket_revenue[bid].get(item_a, 0.0)
                rev_b = basket_revenue[bid].get(item_b, 0.0)
                combo_revenues.append(rev_a + rev_b)
        avg_combo_revenue = round(sum(combo_revenues) / len(combo_revenues), 2) if combo_revenues else 0.0

        # ── Bundle pricing suggestion ────────────────────────────────────
        price_a = round(item_avg_price.get(item_a, 0.0), 2)
        price_b = round(item_avg_price.get(item_b, 0.0), 2)
        individual_total = round(price_a + price_b, 2)
        DISCOUNT_PCT = 0.12  # 12 % bundle discount
        suggested_combo_price = round(individual_total * (1 - DISCOUNT_PCT), 2) if individual_total > 0 else 0.0
        savings = round(individual_total - suggested_combo_price, 2)

        results.append(
            {
                "item_a": item_a,
                "item_b": item_b,
                "support": round(support, 4),
                "confidence_a_to_b": round(confidence_a_to_b, 4),
                "confidence_b_to_a": round(confidence_b_to_a, 4),
                "lift": round(lift, 4),
                "basket_count": count_ab,
                "avg_combo_revenue": avg_combo_revenue,
                "price_a": price_a,
                "price_b": price_b,
                "individual_total": individual_total,
                "suggested_combo_price": suggested_combo_price,
                "savings": savings,
            }
        )

    # ── 5. Rank & return ──────────────────────────────────────────────────
    results.sort(key=lambda r: r["lift"], reverse=True)
    top_results = results[:top_k]

    explanation = (
        f"Analysed {total_baskets} delivery baskets"
        f"{' for branch ' + branch_label if branch_label.lower() != 'all' else ' across all branches'}. "
        f"Found {len(results)} item pairs passing thresholds "
        f"(support≥{min_support}, confidence≥{min_confidence}, lift≥{min_lift}). "
        f"Returning top {len(top_results)} by lift. "
        f"Modifiers {'included' if include_modifiers else 'excluded'}. "
        f"Data source: delivery orders, Jan 2026. "
        f"Customer ≈ basket (98% single-order accuracy)."
    )

    return {
        "branch": branch_label,
        "total_baskets": total_baskets,
        "include_modifiers": include_modifiers,
        "recommendations": top_results,
        "explanation": explanation,
    }


def _empty_response(branch: str, include_modifiers: bool) -> dict:
    return {
        "branch": branch,
        "total_baskets": 0,
        "include_modifiers": include_modifiers,
        "recommendations": [],
        "explanation": f"No baskets with ≥2 items found for branch '{branch}'.",
    }
