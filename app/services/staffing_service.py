from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.core.config import PROCESSED_DATA_DIR


ATTENDANCE_PATH = PROCESSED_DATA_DIR / "attendance.csv"
MONTHLY_SALES_PATH = PROCESSED_DATA_DIR / "monthly_sales_by_branch.csv"

MIN_EFFECTIVE_SHIFT_HOURS = 2.0

SHIFT_ALIASES = {
    "morning": "morning",
    "am": "morning",
    "midday": "midday",
    "afternoon": "midday",
    "noon": "midday",
    "evening": "evening",
    "night": "evening",
    "pm": "evening",
}

MONTH_TO_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _normalize_shift(shift: str) -> str:
    key = _normalize_text(shift)
    normalized = SHIFT_ALIASES.get(key)
    if normalized:
        return normalized
    raise HTTPException(
        status_code=422,
        detail="Unsupported shift. Use one of: morning, midday, evening.",
    )


def _resolve_branch(requested_branch: str, available_branches: list[str]) -> str:
    normalized_map = {_normalize_text(b): b for b in available_branches}
    key = _normalize_text(requested_branch)
    if key in normalized_map:
        return normalized_map[key]

    raise HTTPException(
        status_code=404,
        detail=(
            f"Unknown branch '{requested_branch}'. "
            f"Available branches: {', '.join(sorted(available_branches))}"
        ),
    )


def _load_attendance_data(path: Path = ATTENDANCE_PATH) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "attendance.csv not found. Run the attendance cleaning pipeline first "
                "(python pipelines/clean_00461.py)."
            ),
        )

    df = pd.read_csv(path)
    required = {"employee_id", "branch", "date", "shift", "hours_worked"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"attendance.csv is missing required columns: {sorted(missing)}",
        )

    df = df.copy()
    df["employee_id"] = pd.to_numeric(df["employee_id"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["hours_worked"] = pd.to_numeric(df["hours_worked"], errors="coerce")
    df["shift"] = df["shift"].astype(str).str.strip().str.lower()
    df["branch"] = df["branch"].astype(str).str.strip()

    df = df.dropna(subset=["employee_id", "date", "hours_worked"])
    return df


def _load_monthly_sales_data(path: Path = MONTHLY_SALES_PATH) -> pd.DataFrame | None:
    if not path.exists():
        return None

    df = pd.read_csv(path)
    required = {"branch", "month", "year", "total"}
    if not required.issubset(df.columns):
        return None

    df = df.copy()
    df["branch"] = df["branch"].astype(str).str.strip()
    df["month"] = df["month"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["total"] = pd.to_numeric(df["total"], errors="coerce")
    return df.dropna(subset=["year", "total"])


def _build_shift_presence(attendance_df: pd.DataFrame, branch: str, shift: str) -> pd.Series:
    filtered = attendance_df[
        (attendance_df["branch"] == branch)
        & (attendance_df["shift"] == shift)
        & (attendance_df["hours_worked"] >= MIN_EFFECTIVE_SHIFT_HOURS)
    ].copy()

    if filtered.empty:
        return pd.Series(dtype="float64")

    # Multiple punch rows can exist for the same employee/date/shift.
    # Keep one effective presence record per employee/day/shift.
    dedup = filtered.sort_values("hours_worked").drop_duplicates(
        subset=["date", "employee_id", "shift"], keep="last"
    )

    return dedup.groupby("date")["employee_id"].nunique().sort_index()


def _compute_demand_factor(monthly_sales_df: pd.DataFrame | None, branch: str) -> dict:
    default = {"factor": 1.0, "trend": "unknown"}
    if monthly_sales_df is None or monthly_sales_df.empty:
        return default

    branch_rows = monthly_sales_df[monthly_sales_df["branch"] == branch].copy()
    if branch_rows.empty:
        return default

    branch_rows["month_num"] = (
        branch_rows["month"].astype(str).str.lower().map(MONTH_TO_NUM)
    )
    branch_rows = branch_rows.dropna(subset=["month_num", "year", "total"])
    if branch_rows.empty:
        return default

    branch_rows = branch_rows.sort_values(["year", "month_num"])
    totals = branch_rows["total"].astype(float)
    first_total = float(totals.iloc[0])
    latest_total = float(totals.iloc[-1])
    median_total = float(totals.median())

    ratio = latest_total / median_total if median_total > 0 else 1.0
    pct_change = ((latest_total - first_total) / first_total) if first_total > 0 else 0.0

    if pct_change > 0.08:
        trend = "growing"
        trend_adjustment = 0.05
    elif pct_change < -0.08:
        trend = "declining"
        trend_adjustment = -0.05
    else:
        trend = "stable"
        trend_adjustment = 0.0

    factor = float(np.clip(ratio + trend_adjustment, 0.80, 1.30))
    return {"factor": round(factor, 2), "trend": trend}


def _estimate_staffing(
    attendance_df: pd.DataFrame, monthly_sales_df: pd.DataFrame | None, branch: str, shift: str
) -> dict:
    shift_presence = _build_shift_presence(attendance_df, branch, shift)
    if shift_presence.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                "No attendance records found for this branch/shift with effective work "
                f"duration >= {MIN_EFFECTIVE_SHIFT_HOURS} hours."
            ),
        )

    base_staff = max(1, int(round(float(shift_presence.median()))))
    low_hist = max(1, int(np.floor(float(shift_presence.quantile(0.25)))))
    high_hist = max(base_staff, int(np.ceil(float(shift_presence.quantile(0.90)))))
    avg_hist = round(float(shift_presence.mean()), 2)
    historical_days = int(shift_presence.shape[0])

    demand = _compute_demand_factor(monthly_sales_df, branch)
    demand_factor = float(demand["factor"])

    recommended = max(1, int(round(base_staff * demand_factor)))
    low = max(1, int(np.floor(low_hist * demand_factor)))
    high = max(recommended, int(np.ceil(high_hist * demand_factor)))

    if historical_days >= 20:
        confidence = "high"
    elif historical_days >= 10:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "branch": branch,
        "shift": shift,
        "recommended_staff": recommended,
        "scenarios": {"low": low, "base": recommended, "high": high},
        "historical_days": historical_days,
        "average_historical_staff": avg_hist,
        "demand_factor": demand_factor,
        "demand_trend": demand["trend"],
        "confidence": confidence,
        "explanation": (
            f"Baseline {shift} staffing from attendance is {base_staff} staff/day. "
            f"Applied demand factor {demand_factor:.2f} from branch monthly sales trend "
            f"({demand['trend']}) to produce the recommendation."
        ),
        "assumptions": [
            "Attendance records with <2 worked hours are treated as non-effective shifts.",
            "Demand adjustment is derived from branch-level monthly sales in scaled units.",
        ],
    }


def recommend_staffing(branch: str, shift: str) -> dict:
    attendance_df = _load_attendance_data()
    monthly_sales_df = _load_monthly_sales_data()

    available_branches = sorted(attendance_df["branch"].dropna().unique().tolist())
    canonical_branch = _resolve_branch(branch, available_branches)
    normalized_shift = _normalize_shift(shift)

    return _estimate_staffing(attendance_df, monthly_sales_df, canonical_branch, normalized_shift)
