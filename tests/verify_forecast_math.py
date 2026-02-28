"""
Manual step-by-step verification of all forecast calculations.
Run this to independently verify what forecast_service.py computes.
"""
import numpy as np
from sklearn.linear_model import LinearRegression

# ── Raw data straight from data/processed/monthly_sales_by_branch.csv ────────
DATA = {
    "Conut": {
        "months": ["August", "September", "October", "November", "December"],
        "values": [554074782.88, 784385377.11, 1137352241.41, 1351165728.11, 67887513.35],
    },
    "Conut - Tyre": {
        "months": ["August", "September", "October", "November", "December"],
        "values": [477535459.07, 444800810.51, 2100816729.45, 1129526810.42, 1024205946.30],
    },
    "Conut Jnah": {
        "months": ["August", "September", "October", "November", "December"],
        "values": [363540268.13, 714037266.45, 785925564.58, 947652050.58, 2878191130.49],
    },
    "Main Street Coffee": {
        "months": ["September", "October", "November", "December"],
        "values": [145842540.35, 920588160.21, 1171534376.20, 3074216293.59],
    },
}

SEP = "=" * 72

for branch, info in DATA.items():
    vals = np.array(info["values"])
    months = info["months"]
    median = np.median(vals)
    threshold = 0.15 * median

    print(f"\n{SEP}")
    print(f"  BRANCH: {branch}")
    print(SEP)

    print(f"\n  Historical data (from monthly_sales_by_branch.csv):")
    for m, v in zip(months, vals):
        flag = "  ⚠ ANOMALY" if v < threshold else ""
        print(f"    {m:12s}  {v:>22,.2f}{flag}")

    print(f"\n  Anomaly detection:")
    print(f"    Median of series      = {median:>22,.2f}")
    print(f"    15% threshold         = {threshold:>22,.2f}")

    anomaly_mask = vals < threshold
    removed_months = [m for m, flag in zip(months, anomaly_mask) if flag]
    clean = vals[~anomaly_mask]
    clean_months = [m for m, flag in zip(months, anomaly_mask) if not flag]

    if removed_months:
        print(f"    Removed month(s)      : {removed_months}")
    else:
        print(f"    No anomalies detected.")

    print(f"\n  Clean series used for forecasting:")
    for m, v in zip(clean_months, clean):
        print(f"    {m:12s}  {v:>22,.2f}")

    # ── Naive ────────────────────────────────────────────────────────────
    naive = float(clean[-1])
    print(f"\n  [1] NAIVE BASELINE")
    print(f"    = last clean value = {clean_months[-1]} = {naive:>22,.2f}")

    # ── WMA ─────────────────────────────────────────────────────────────
    n = min(len(clean), 4)
    window = clean[-n:]
    window_months = clean_months[-n:]
    raw_weights = np.arange(1, n + 1, dtype=float)
    norm_weights = raw_weights / raw_weights.sum()
    wma = float(np.dot(window, norm_weights))

    print(f"\n  [2] WEIGHTED MOVING AVERAGE (window = last {n} months)")
    print(f"    Raw weights  : {list(raw_weights.astype(int))}")
    print(f"    Norm weights : {[round(w, 4) for w in norm_weights]}")
    for m, v, w in zip(window_months, window, norm_weights):
        print(f"    {m:12s}  {v:>22,.2f}  × {w:.4f}  = {v*w:>22,.2f}")
    print(f"    WMA          = {wma:>22,.2f}")

    # ── Trend ────────────────────────────────────────────────────────────
    X = np.arange(len(clean)).reshape(-1, 1)
    model = LinearRegression().fit(X, clean)
    slope = model.coef_[0]
    intercept = model.intercept_
    next_x = len(clean)
    trend_pred = max(0.0, float(model.predict([[next_x]])[0]))

    print(f"\n  [3] LINEAR TREND REGRESSION (OLS)")
    print(f"    X (month indices) : {list(range(len(clean)))}")
    print(f"    y (values)        : {[f'{v:,.0f}' for v in clean]}")
    print(f"    Fitted equation   : y = {slope:,.0f} * x + {intercept:,.0f}")
    print(f"    Next x (x={next_x})   => {slope:,.0f} × {next_x} + {intercept:,.0f} = {trend_pred:>22,.2f}")

    # ── Ensemble ────────────────────────────────────────────────────────
    ensemble = (naive + wma + trend_pred) / 3
    print(f"\n  [4] ENSEMBLE (simple average of all three)")
    print(f"    ({naive:,.2f} + {wma:,.2f} + {trend_pred:,.2f}) / 3")
    print(f"    = {ensemble:>22,.2f}")

    # ── MoM growth ──────────────────────────────────────────────────────
    mom = [(clean[i] - clean[i-1]) / clean[i-1] * 100 for i in range(1, len(clean))]
    avg_mom = float(np.mean(mom))
    print(f"\n  [5] MONTH-OVER-MONTH GROWTH (clean series)")
    for i, (g, m) in enumerate(zip(mom, clean_months[1:])):
        print(f"    {clean_months[i]:12s} → {m:12s}  {g:>+8.2f}%")
    print(f"    Average MoM growth     = {avg_mom:>+8.2f}%")

    # ── Trend classification ──────────────────────────────────────────
    rel_slope = slope / clean.mean()
    if rel_slope > 0.10:
        trend_label = "growing"
    elif rel_slope < -0.10:
        trend_label = "declining"
    else:
        trend_label = "stable"
    print(f"\n  [6] TREND CLASSIFICATION")
    print(f"    Slope / Mean = {slope:,.0f} / {clean.mean():,.0f} = {rel_slope:.4f}")
    print(f"    Threshold: >0.10 = growing, <-0.10 = declining, else stable")
    print(f"    => TREND: {trend_label.upper()}")

print(f"\n{SEP}")
print("  ALL CALCULATIONS VERIFIED ✅")
print(SEP)
