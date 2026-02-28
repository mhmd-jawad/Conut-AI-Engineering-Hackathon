"""
forecast_service.py
-------------------
Demand Forecasting by Branch.

Methods used (lightweight — data is only 4-5 months):
  1. Naive baseline         — last observed value carried forward.
  2. Weighted Moving Average — recent months weighted more heavily.
  3. Simple Linear Trend    — OLS regression on month index, extrapolated.

The final forecast is an ensemble average of the three methods.
Each branch also gets:
  - trend label   : growing / stable / declining
  - confidence    : low / medium  (based on data length)
  - demand index  : branch share of total forecasted demand
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.core.config import PROCESSED_DATA_DIR

# ──────────────────────────────────────────────────────────────────────────────
# Month ordering for sorting
# ──────────────────────────────────────────────────────────────────────────────
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_TO_IDX = {m: i for i, m in enumerate(MONTH_ORDER)}

DATA_PATH = PROCESSED_DATA_DIR / "monthly_sales_by_branch.csv"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _load_data() -> pd.DataFrame:
    """Load and sort the monthly-sales data, adding a chronological index."""
    df = pd.read_csv(DATA_PATH)
    df["month_idx"] = df["month"].map(MONTH_TO_IDX)
    df = df.sort_values(["branch", "year", "month_idx"]).reset_index(drop=True)
    return df


def _detect_anomalies(series: pd.Series) -> list[int]:
    """Flag month indices whose value is < 15 % of the series median (likely
    incomplete-month data, e.g. Conut December)."""
    if len(series) < 3:
        return []
    median = series.median()
    if median == 0:
        return []
    return [i for i, v in enumerate(series) if v < 0.15 * median]


def _naive_forecast(values: np.ndarray, horizon: int) -> list[float]:
    """Repeat the last observed value."""
    last = float(values[-1])
    return [last] * horizon


def _wma_forecast(values: np.ndarray, horizon: int) -> list[float]:
    """Weighted moving average.  Uses up to the last 4 values with linearly
    increasing weights  [1, 2, 3, 4]  (most recent gets highest weight)."""
    n = min(len(values), 4)
    window = values[-n:]
    weights = np.arange(1, n + 1, dtype=float)
    weights /= weights.sum()
    wma = float(np.dot(window, weights))
    return [wma] * horizon


def _trend_forecast(values: np.ndarray, horizon: int) -> list[float]:
    """Simple OLS trend line, extrapolated forward."""
    X = np.arange(len(values)).reshape(-1, 1)
    y = values
    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(values), len(values) + horizon).reshape(-1, 1)
    preds = model.predict(future_X)
    # Clamp negatives to zero (demand can't be negative)
    return [max(0.0, float(p)) for p in preds]


def _classify_trend(values: np.ndarray) -> str:
    """Label the series as growing / stable / declining using the linear slope
    normalised by the mean value."""
    if len(values) < 2:
        return "insufficient data"
    X = np.arange(len(values)).reshape(-1, 1)
    model = LinearRegression().fit(X, values)
    slope = model.coef_[0]
    mean = values.mean()
    if mean == 0:
        return "stable"
    relative_slope = slope / mean  # normalised growth rate per month
    if relative_slope > 0.10:
        return "growing"
    elif relative_slope < -0.10:
        return "declining"
    return "stable"


def _month_name(base_month_idx: int, offset: int) -> str:
    """Return the month name for base + offset (wrapping around December)."""
    return MONTH_ORDER[(base_month_idx + offset) % 12]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────
def forecast_branch_demand(branch: str, horizon_months: int) -> dict[str, Any]:
    """Produce a demand forecast for *branch* over *horizon_months* months."""

    df = _load_data()
    all_branches = sorted(df["branch"].unique().tolist())

    # ── validate branch ────────────────────────────────────────────────────
    if branch not in all_branches:
        return {
            "branch": branch,
            "error": f"Unknown branch. Available: {all_branches}",
        }

    branch_df = df[df["branch"] == branch].copy()
    raw_values = branch_df["total"].values.astype(float)
    months_list = branch_df["month"].tolist()
    n_months = len(raw_values)

    # ── anomaly handling ───────────────────────────────────────────────────
    anomaly_indices = _detect_anomalies(pd.Series(raw_values))
    anomaly_notes = []
    clean_values = raw_values.copy()
    for idx in anomaly_indices:
        anomaly_notes.append(
            f"{months_list[idx]} value ({raw_values[idx]:,.0f}) looks anomalously low "
            f"(< 15% of median) — likely incomplete data. Excluded from forecast."
        )
        clean_values = np.delete(clean_values, idx)

    values = clean_values  # use cleaned series for forecasting

    # ── forecasts ──────────────────────────────────────────────────────────
    naive_fc = _naive_forecast(values, horizon_months)
    wma_fc   = _wma_forecast(values, horizon_months)
    trend_fc = _trend_forecast(values, horizon_months)

    # Ensemble average
    ensemble_fc = [
        round((n + w + t) / 3, 2)
        for n, w, t in zip(naive_fc, wma_fc, trend_fc)
    ]

    # ── trend classification ───────────────────────────────────────────────
    trend = _classify_trend(values)

    # ── confidence ─────────────────────────────────────────────────────────
    if n_months >= 6:
        confidence = "medium"
    elif n_months >= 4:
        confidence = "low-medium"
    else:
        confidence = "low"

    # ── demand index (branch share) ────────────────────────────────────────
    # Forecast every branch 1 month ahead, compute share
    branch_fc_1 = {}
    for b in all_branches:
        bdf = df[df["branch"] == b]
        bvals = bdf["total"].values.astype(float)
        b_anom = _detect_anomalies(pd.Series(bvals))
        bclean = np.delete(bvals, b_anom) if b_anom else bvals
        if len(bclean) == 0:
            branch_fc_1[b] = 0.0
        else:
            branch_fc_1[b] = float(np.mean([
                _naive_forecast(bclean, 1)[0],
                _wma_forecast(bclean, 1)[0],
                _trend_forecast(bclean, 1)[0],
            ]))
    total_fc = sum(branch_fc_1.values())
    demand_index = round(branch_fc_1.get(branch, 0) / total_fc, 4) if total_fc else 0.0

    # ── forecast month labels ──────────────────────────────────────────────
    last_month_idx = MONTH_TO_IDX.get(months_list[-1], 11)
    forecast_months = [
        _month_name(last_month_idx, i + 1) for i in range(horizon_months)
    ]

    # ── per-month breakdown ────────────────────────────────────────────────
    monthly_forecasts = []
    for i in range(horizon_months):
        monthly_forecasts.append({
            "month": forecast_months[i],
            "naive": round(naive_fc[i], 2),
            "wma": round(wma_fc[i], 2),
            "trend": round(trend_fc[i], 2),
            "ensemble": ensemble_fc[i],
        })

    # ── historical summary ─────────────────────────────────────────────────
    history = [
        {"month": m, "total": round(float(v), 2)}
        for m, v in zip(months_list, raw_values)
    ]

    # ── MoM growth rates (on clean values) ─────────────────────────────────
    mom_growth = []
    for i in range(1, len(values)):
        prev = values[i - 1]
        if prev != 0:
            mom_growth.append(round((values[i] - prev) / prev * 100, 2))

    avg_mom_growth = round(float(np.mean(mom_growth)), 2) if mom_growth else None

    # ── build response ─────────────────────────────────────────────────────
    explanation_parts = [
        f"Forecast for {branch} over next {horizon_months} month(s).",
        f"Based on {n_months} months of historical data (Aug–Dec 2025).",
        f"Methods: Naive baseline, Weighted Moving Average (window=4), Linear Trend Regression.",
        f"Ensemble forecast = average of all three methods.",
    ]
    if anomaly_notes:
        explanation_parts.extend(anomaly_notes)
    explanation_parts.append(
        f"Trend classification: {trend}. "
        f"Average month-over-month growth (clean): {avg_mom_growth}%."
        if avg_mom_growth is not None
        else f"Trend classification: {trend}."
    )

    return {
        "branch": branch,
        "horizon_months": horizon_months,
        "trend": trend,
        "confidence": confidence,
        "demand_index": demand_index,
        "avg_mom_growth_pct": avg_mom_growth,
        "history": history,
        "forecasts": monthly_forecasts,
        "anomaly_notes": anomaly_notes if anomaly_notes else None,
        "explanation": " ".join(explanation_parts),
    }
