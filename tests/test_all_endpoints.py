"""Comprehensive endpoint test across all branches."""
import requests
import json

BASE = "http://127.0.0.1:8000"
BRANCHES = ["Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee", "all", "conut jnah"]

def test_forecast():
    print("\n" + "="*60)
    print("FORECAST /forecast")
    print("="*60)
    for b in BRANCHES:
        try:
            r = requests.post(f"{BASE}/forecast", json={"branch": b, "horizon_months": 3})
            d = r.json()
            if r.status_code == 200:
                hist_len = len(d.get("history", []))
                fc_len = len(d.get("forecasts", []))
                trend = d.get("trend", "?")
                conf = d.get("confidence", "?")
                err = d.get("error", "")
                print(f"  [{r.status_code}] {b:25s} -> history={hist_len}, forecasts={fc_len}, trend={trend}, conf={conf}")
            else:
                print(f"  [{r.status_code}] {b:25s} -> {str(d)[:120]}")
        except Exception as e:
            print(f"  [ERR]  {b:25s} -> {e}")

def test_combos():
    print("\n" + "="*60)
    print("COMBOS /combo")
    print("="*60)
    for b in BRANCHES:
        try:
            r = requests.post(f"{BASE}/combo", json={"branch": b, "top_k": 5})
            d = r.json()
            if r.status_code == 200:
                recs = d.get("recommendations", [])
                baskets = d.get("total_baskets", 0)
                print(f"  [{r.status_code}] {b:25s} -> recs={len(recs)}, baskets={baskets}")
                if len(recs) == 0:
                    expl = d.get("explanation", "")[:150]
                    print(f"         explanation: {expl}")
            else:
                print(f"  [{r.status_code}] {b:25s} -> {str(d)[:120]}")
        except Exception as e:
            print(f"  [ERR]  {b:25s} -> {e}")

def test_staffing():
    print("\n" + "="*60)
    print("STAFFING /staffing")
    print("="*60)
    for b in BRANCHES:
        for shift in ["morning", "midday", "evening"]:
            try:
                r = requests.post(f"{BASE}/staffing", json={"branch": b, "shift": shift})
                d = r.json()
                if r.status_code == 200:
                    rec = d.get("recommended_staff", "?")
                    conf = d.get("confidence", "?")
                    trend = d.get("demand_trend", "?")
                    print(f"  [{r.status_code}] {b:25s} {shift:8s} -> staff={rec}, conf={conf}, trend={trend}")
                else:
                    detail = d.get("detail", str(d))[:100]
                    print(f"  [{r.status_code}] {b:25s} {shift:8s} -> {detail}")
            except Exception as e:
                print(f"  [ERR]  {b:25s} {shift:8s} -> {e}")

def test_expansion():
    print("\n" + "="*60)
    print("EXPANSION /expansion")
    print("="*60)
    for b in BRANCHES:
        try:
            r = requests.post(f"{BASE}/expansion", json={"branch": b})
            d = r.json()
            if r.status_code == 200:
                verdict = d.get("verdict", "?")
                scorecards = d.get("scorecards", [])
                cands = len(d.get("candidate_locations", []))
                best = d.get("best_archetype", {})
                err = d.get("error", "")
                if err:
                    print(f"  [{r.status_code}] {b:25s} -> error='{err[:80]}'")
                else:
                    print(f"  [{r.status_code}] {b:25s} -> verdict={verdict}, scorecards={len(scorecards)}, candidates={cands}, best={best.get('branch','')}")
            else:
                print(f"  [{r.status_code}] {b:25s} -> {str(d)[:120]}")
        except Exception as e:
            print(f"  [ERR]  {b:25s} -> {e}")

def test_growth():
    print("\n" + "="*60)
    print("GROWTH /growth-strategy")
    print("="*60)
    for b in BRANCHES:
        try:
            r = requests.post(f"{BASE}/growth-strategy", json={"branch": b})
            d = r.json()
            if r.status_code == 200:
                branches = d.get("branches", [])
                print(f"  [{r.status_code}] {b:25s} -> {len(branches)} branch profiles returned")
                for br in branches[:2]:
                    name = br.get("branch", "?")
                    rev = br.get("revenue_momentum", {}).get("trend", "?")
                    acts = len(br.get("actions", []))
                    print(f"         {name}: rev_trend={rev}, actions={acts}")
            else:
                print(f"  [{r.status_code}] {b:25s} -> {str(d)[:120]}")
        except Exception as e:
            print(f"  [ERR]  {b:25s} -> {e}")

if __name__ == "__main__":
    print("Testing all endpoints...")
    test_forecast()
    test_combos()
    test_staffing()
    test_expansion()
    test_growth()
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
