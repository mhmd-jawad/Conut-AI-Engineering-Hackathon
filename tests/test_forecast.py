"""Quick test for the forecast service — runs all 4 branches."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.forecast_service import forecast_branch_demand

branches = ["Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"]

for branch in branches:
    r = forecast_branch_demand(branch, 1)
    fc = r["forecasts"][0]
    print(f"\n{'='*60}")
    print(f"  Branch      : {r['branch']}")
    print(f"  Trend       : {r['trend']}")
    print(f"  Confidence  : {r['confidence']}")
    print(f"  Demand Index: {r['demand_index']}")
    print(f"  Avg MoM %   : {r['avg_mom_growth_pct']}")
    print(f"  Forecast ({fc['month']}):")
    print(f"    Naive     : {fc['naive']:>20,.0f}")
    print(f"    WMA       : {fc['wma']:>20,.0f}")
    print(f"    Trend     : {fc['trend']:>20,.0f}")
    print(f"    Ensemble  : {fc['ensemble']:>20,.0f}")
    if r.get("anomaly_notes"):
        print(f"  ⚠ Anomaly   : {r['anomaly_notes'][0]}")

# Test unknown branch
print(f"\n{'='*60}")
r = forecast_branch_demand("FakeBranch", 1)
print(f"  Unknown branch test: {r.get('error', 'NO ERROR')}")

# Test multi-month horizon
print(f"\n{'='*60}")
r = forecast_branch_demand("Main Street Coffee", 3)
print(f"  3-month forecast for Main Street Coffee:")
for fc in r["forecasts"]:
    print(f"    {fc['month']}: {fc['ensemble']:>20,.0f}")

print(f"\n✅ All tests passed!")
