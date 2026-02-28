def forecast_branch_demand(branch: str, horizon_months: int) -> dict:
    return {
        "branch": branch,
        "horizon_months": horizon_months,
        "forecast_index": None,
        "trend": "unknown",
        "confidence": "low",
        "explanation": "Forecast engine scaffold ready; connect to branch_monthly_sales.",
    }
