"""
combo_service.py
----------------
Combo recommendation engines:
1) Non-AI basket-analysis engine (support/confidence/lift).
2) ML item-item cosine similarity engine.
"""

from __future__ import annotations

import functools
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "basket_lines.csv"
NON_PRODUCTS = {"DELIVERY CHARGE"}
MODEL_NAME = "Item-Item Cosine Similarity"
DISCOUNT_PCT = 0.12


@functools.lru_cache(maxsize=1)
def _load_basket_lines() -> pd.DataFrame:
    """Read basket_lines.csv and return a DataFrame."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"basket_lines.csv not found at {DATA_PATH}. "
            "Run  python pipelines/clean_00502_baskets.py  first."
        )
    df = pd.read_csv(DATA_PATH)
    df["Is Cancellation"] = df["Is Cancellation"].astype(int)
    df["Is_Modifier"] = df["Is_Modifier"].astype(int)
    return df


def _filter_combo_rows(df: pd.DataFrame, branch: str, include_modifiers: bool) -> tuple[str, pd.DataFrame]:
    """Apply common combo filters and optional branch slicing."""
    filtered = df[df["Is Cancellation"] == 0].copy()
    filtered = filtered[~filtered["Item Description"].astype(str).str.upper().isin(NON_PRODUCTS)]
    if not include_modifiers:
        filtered = filtered[filtered["Is_Modifier"] == 0]

    branch_label = branch.strip()
    if branch_label.lower() != "all":
        filtered = filtered[
            filtered["Branch"].astype(str).str.strip().str.lower() == branch_label.lower()
        ]
    return branch_label, filtered


def _build_baskets_and_revenue(df: pd.DataFrame) -> tuple[dict[str, set[str]], dict[str, dict[str, float]]]:
    """Build basket item sets and per-basket revenue lookups."""
    baskets: dict[str, set[str]] = {}
    basket_revenue: dict[str, dict[str, float]] = {}
    for basket_id, group in df.groupby("basket_id"):
        items = set(group["Item Description"].astype(str).unique())
        if len(items) >= 2:
            baskets[str(basket_id)] = items
            rev = group.groupby("Item Description")["Line Total"].sum().to_dict()
            basket_revenue[str(basket_id)] = {str(k): float(v) for k, v in rev.items()}
    return baskets, basket_revenue


def _average_item_prices(df: pd.DataFrame) -> dict[str, float]:
    prices = (
        df[df["Price"] > 0]
        .groupby("Item Description")["Price"]
        .mean()
        .to_dict()
    )
    return {str(k): float(v) for k, v in prices.items()}


def _bundle_pricing(item_a: str, item_b: str, item_avg_price: dict[str, float]) -> dict[str, float]:
    price_a = round(item_avg_price.get(item_a, 0.0), 2)
    price_b = round(item_avg_price.get(item_b, 0.0), 2)
    individual_total = round(price_a + price_b, 2)
    suggested_combo_price = round(individual_total * (1 - DISCOUNT_PCT), 2) if individual_total > 0 else 0.0
    savings = round(individual_total - suggested_combo_price, 2)
    return {
        "price_a": price_a,
        "price_b": price_b,
        "individual_total": individual_total,
        "suggested_combo_price": suggested_combo_price,
        "savings": savings,
    }


def _average_combo_revenue(
    item_a: str,
    item_b: str,
    baskets: dict[str, set[str]],
    basket_revenue: dict[str, dict[str, float]],
) -> float:
    combo_revenues: list[float] = []
    for bid, items in baskets.items():
        if item_a in items and item_b in items:
            rev_a = basket_revenue[bid].get(item_a, 0.0)
            rev_b = basket_revenue[bid].get(item_b, 0.0)
            combo_revenues.append(rev_a + rev_b)
    return round(sum(combo_revenues) / len(combo_revenues), 2) if combo_revenues else 0.0


def _pair_set_from_baskets(baskets: dict[str, set[str]], basket_ids: list[str]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for bid in basket_ids:
        items = sorted(baskets.get(bid, set()))
        for pair in combinations(items, 2):
            pairs.add(pair)
    return pairs


def _empty_response(branch: str, include_modifiers: bool) -> dict:
    return {
        "branch": branch,
        "total_baskets": 0,
        "include_modifiers": include_modifiers,
        "recommendations": [],
        "explanation": f"No baskets with >=2 items found for branch '{branch}'.",
    }


def _empty_ml_response(branch: str, include_modifiers: bool, note: str) -> dict:
    return {
        "branch": branch,
        "total_baskets": 0,
        "include_modifiers": include_modifiers,
        "model_name": MODEL_NAME,
        "recommendations": [],
        "ml_precision_at_k": None,
        "evaluation_note": note,
        "explanation": note,
    }


def recommend_combos(
    branch: str,
    top_k: int = 5,
    include_modifiers: bool = False,
    min_support: float = 0.02,
    min_confidence: float = 0.15,
    min_lift: float = 1.0,
) -> dict:
    """Return top-K non-AI combo recommendations for *branch* (or 'all')."""

    df = _load_basket_lines()
    branch_label, filtered = _filter_combo_rows(df, branch, include_modifiers)
    if filtered.empty:
        return _empty_response(branch_label, include_modifiers)

    baskets, basket_revenue = _build_baskets_and_revenue(filtered)
    item_avg_price = _average_item_prices(filtered)
    total_baskets = len(baskets)
    if total_baskets == 0:
        return _empty_response(branch_label, include_modifiers)

    item_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    for items in baskets.values():
        for item in items:
            item_counts[item] += 1
        for pair in combinations(sorted(items), 2):
            pair_counts[pair] += 1

    results: list[dict] = []
    for (item_a, item_b), count_ab in pair_counts.items():
        support = count_ab / total_baskets
        if support < min_support:
            continue

        support_a = item_counts[item_a] / total_baskets
        support_b = item_counts[item_b] / total_baskets
        confidence_a_to_b = count_ab / item_counts[item_a]
        confidence_b_to_a = count_ab / item_counts[item_b]
        lift = support / (support_a * support_b) if (support_a * support_b) > 0 else 0.0

        if confidence_a_to_b < min_confidence and confidence_b_to_a < min_confidence:
            continue
        if lift < min_lift:
            continue

        pricing = _bundle_pricing(item_a, item_b, item_avg_price)
        results.append(
            {
                "item_a": item_a,
                "item_b": item_b,
                "support": round(support, 4),
                "confidence_a_to_b": round(confidence_a_to_b, 4),
                "confidence_b_to_a": round(confidence_b_to_a, 4),
                "lift": round(lift, 4),
                "basket_count": count_ab,
                "avg_combo_revenue": _average_combo_revenue(item_a, item_b, baskets, basket_revenue),
                **pricing,
            }
        )

    results.sort(key=lambda r: r["lift"], reverse=True)
    top_results = results[:top_k]

    explanation = (
        f"Analysed {total_baskets} delivery baskets"
        f"{' for branch ' + branch_label if branch_label.lower() != 'all' else ' across all branches'}. "
        f"Found {len(results)} item pairs passing thresholds "
        f"(support>={min_support}, confidence>={min_confidence}, lift>={min_lift}). "
        f"Returning top {len(top_results)} by lift. "
        f"Modifiers {'included' if include_modifiers else 'excluded'}."
    )
    return {
        "branch": branch_label,
        "total_baskets": total_baskets,
        "include_modifiers": include_modifiers,
        "recommendations": top_results,
        "explanation": explanation,
    }


def recommend_combos_ml(
    branch: str,
    top_k: int = 5,
    include_modifiers: bool = False,
    min_support: float = 0.02,
) -> dict:
    """Return top-K ML combo recommendations using item-item cosine similarity."""
    df = _load_basket_lines()
    branch_label, filtered = _filter_combo_rows(df, branch, include_modifiers)
    if filtered.empty:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            f"No data after filtering for branch '{branch_label}'.",
        )

    baskets, _ = _build_baskets_and_revenue(filtered)
    item_avg_price = _average_item_prices(filtered)
    basket_ids = sorted(baskets.keys())
    total_baskets = len(basket_ids)
    if total_baskets < 2:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            "Not enough baskets for train/test split. Need at least 2 baskets.",
        )

    try:
        train_ids, test_ids = train_test_split(
            basket_ids,
            test_size=0.2,
            random_state=42,
            shuffle=True,
        )
    except ValueError:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            "Unable to split baskets into train/test partitions.",
        )

    if not train_ids or not test_ids:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            "Train/test split produced an empty partition.",
        )

    train_items = sorted({item for bid in train_ids for item in baskets.get(str(bid), set())})
    if len(train_items) < 2:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            "Not enough unique items in training split for cosine-similarity model.",
        )

    item_to_idx = {item: idx for idx, item in enumerate(train_items)}
    basket_matrix = np.zeros((len(train_ids), len(train_items)), dtype=float)
    for row_idx, bid in enumerate(train_ids):
        for item in baskets.get(str(bid), set()):
            col_idx = item_to_idx.get(item)
            if col_idx is not None:
                basket_matrix[row_idx, col_idx] = 1.0

    if float(basket_matrix.sum()) == 0:
        return _empty_ml_response(
            branch_label,
            include_modifiers,
            "Training matrix is empty after filtering.",
        )

    similarity = cosine_similarity(basket_matrix.T)
    np.fill_diagonal(similarity, 0.0)

    train_pair_counts = Counter()
    for bid in train_ids:
        for pair in combinations(sorted(baskets.get(str(bid), set())), 2):
            train_pair_counts[pair] += 1

    ml_pairs: list[dict] = []
    train_basket_count = len(train_ids)
    for i in range(len(train_items)):
        for j in range(i + 1, len(train_items)):
            sim_score = float(similarity[i, j])
            if sim_score <= 0:
                continue

            item_a = train_items[i]
            item_b = train_items[j]
            count_ab = train_pair_counts.get((item_a, item_b), 0)
            support_train = (count_ab / train_basket_count) if train_basket_count else 0.0
            if support_train < min_support:
                continue

            pricing = _bundle_pricing(item_a, item_b, item_avg_price)
            ml_pairs.append(
                {
                    "item_a": item_a,
                    "item_b": item_b,
                    "similarity_score": round(sim_score, 4),
                    "support_train": round(support_train, 4),
                    "basket_count_train": int(count_ab),
                    **pricing,
                }
            )

    ml_pairs.sort(
        key=lambda r: (-r["similarity_score"], -r["support_train"], r["item_a"], r["item_b"])
    )
    top_results = ml_pairs[:top_k]

    test_pairs = _pair_set_from_baskets(baskets, [str(bid) for bid in test_ids])
    if not test_pairs:
        precision_at_k = None
        evaluation_note = (
            f"Precision@{top_k} unavailable because no 2-item pairs were present in held-out test baskets."
        )
    elif not top_results:
        precision_at_k = None
        evaluation_note = f"Precision@{top_k} unavailable because ML model produced no candidate pairs."
    else:
        predicted_pairs = {(r["item_a"], r["item_b"]) for r in top_results}
        hits = sum(1 for pair in predicted_pairs if pair in test_pairs)
        precision_at_k = round(hits / top_k, 4)
        evaluation_note = (
            f"Precision@{top_k} on held-out baskets: {precision_at_k} "
            f"({hits}/{top_k} hits; {len(test_pairs)} true test pairs)."
        )

    explanation = (
        f"ML model={MODEL_NAME}. "
        f"Train/test split is deterministic (80/20, random_state=42). "
        f"Filtered by support>={min_support}. "
        f"Generated {len(ml_pairs)} pair candidates, returning top {len(top_results)}."
    )
    return {
        "branch": branch_label,
        "total_baskets": total_baskets,
        "include_modifiers": include_modifiers,
        "model_name": MODEL_NAME,
        "recommendations": top_results,
        "ml_precision_at_k": precision_at_k,
        "evaluation_note": evaluation_note,
        "explanation": explanation,
    }


def _summarize_non_ai(recommendations: list[dict]) -> str:
    if not recommendations:
        return "No significant combo found with current thresholds."
    top = recommendations[0]
    return (
        f"Top combo is {top['item_a']} + {top['item_b']} "
        f"(lift={top['lift']}, support={top['support']})."
    )


def _summarize_ml(recommendations: list[dict]) -> str:
    if not recommendations:
        return "No ML combo found with current thresholds and train/test split."
    top = recommendations[0]
    return (
        f"Top combo is {top['item_a']} + {top['item_b']} "
        f"(similarity={top['similarity_score']}, support_train={top['support_train']})."
    )


def compare_combo_solutions(
    branch: str,
    top_k: int = 5,
    include_modifiers: bool = False,
    min_support: float = 0.02,
    min_confidence: float = 0.15,
    min_lift: float = 1.0,
) -> dict:
    """Compare non-AI and ML combo engines side-by-side."""
    non_ai = recommend_combos(
        branch=branch,
        top_k=top_k,
        include_modifiers=include_modifiers,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
    )
    ml = recommend_combos_ml(
        branch=branch,
        top_k=top_k,
        include_modifiers=include_modifiers,
        min_support=min_support,
    )

    non_ai_answer_line = f"The non AI answer: {_summarize_non_ai(non_ai['recommendations'])}"
    ml_answer_line = f"The ML [{MODEL_NAME}] answer: {_summarize_ml(ml['recommendations'])}"
    explanation = (
        f"Compared non-AI basket metrics vs ML cosine similarity for branch '{non_ai['branch']}'. "
        f"Non-AI thresholds used support>={min_support}, confidence>={min_confidence}, lift>={min_lift}. "
        f"{ml['evaluation_note']}"
    )
    return {
        "branch": non_ai["branch"],
        "model_name": MODEL_NAME,
        "non_ai_answer_line": non_ai_answer_line,
        "ml_answer_line": ml_answer_line,
        "ml_precision_at_k": ml["ml_precision_at_k"],
        "non_ai_recommendations": non_ai["recommendations"],
        "ml_recommendations": ml["recommendations"],
        "evaluation_note": ml["evaluation_note"],
        "explanation": explanation,
    }
