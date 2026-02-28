"""
OpenClaw Integration Tests
Verifies that every endpoint OpenClaw needs works correctly.
Run with: python tests/test_openclaw.py  (server must be on port 8000)
"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}")
    return json.loads(r.read())


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


def test(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f"  ({detail})" if detail else ""))
    return ok


def main():
    passed = 0
    total = 0

    print("\n=== OpenClaw Integration Tests ===\n")

    # 1. Health
    print("1. GET /health")
    d = get("/health")
    total += 1
    if test("status ok", d.get("status") == "ok"):
        passed += 1

    # 2. Branches discovery
    print("\n2. GET /branches")
    d = get("/branches")
    total += 1
    if test("has branches list", len(d.get("branches", [])) == 4, f"branches={d.get('branches')}"):
        passed += 1
    total += 1
    if test("has shifts", len(d.get("shifts", [])) == 3):
        passed += 1
    total += 1
    if test("has defaults", d.get("default_horizon_months") == 3 and d.get("default_top_k") == 5):
        passed += 1

    # 3. Chat — combo
    print("\n3. POST /chat — combo")
    d = post("/chat", {"question": "What are the top combos for Conut Jnah?"})
    total += 1
    if test("intent=combo", d.get("intent") == "combo"):
        passed += 1
    total += 1
    if test("branch detected", d.get("branch") == "Conut Jnah"):
        passed += 1
    total += 1
    if test("has answer", len(d.get("answer", "")) > 20):
        passed += 1
    total += 1
    if test("no error", d.get("error") is None):
        passed += 1

    # 4. Chat — forecast
    print("\n4. POST /chat — forecast")
    d = post("/chat", {"question": "Forecast demand for Conut - Tyre next 4 months"})
    total += 1
    if test("intent=forecast", d.get("intent") == "forecast"):
        passed += 1
    total += 1
    if test("branch detected", d.get("branch") == "Conut - Tyre"):
        passed += 1
    total += 1
    if test("has answer", "Forecast" in d.get("answer", "")):
        passed += 1

    # 5. Chat — staffing
    print("\n5. POST /chat — staffing")
    d = post("/chat", {"question": "How many staff for the evening shift at Conut?"})
    total += 1
    if test("intent=staffing", d.get("intent") == "staffing"):
        passed += 1
    total += 1
    if test("has answer", len(d.get("answer", "")) > 20):
        passed += 1

    # 6. Chat — expansion
    print("\n6. POST /chat — expansion")
    d = post("/chat", {"question": "Should we expand? Where should we open next?"})
    total += 1
    if test("intent=expansion", d.get("intent") == "expansion"):
        passed += 1
    total += 1
    if test("has answer", "Expansion" in d.get("answer", "")):
        passed += 1

    # 7. Chat — growth
    print("\n7. POST /chat — growth")
    d = post("/chat", {"question": "Give me a coffee growth strategy for Main Street Coffee"})
    total += 1
    if test("intent=growth", d.get("intent") == "growth"):
        passed += 1
    total += 1
    if test("branch detected", d.get("branch") == "Main Street Coffee"):
        passed += 1
    total += 1
    if test("has answer", "Growth" in d.get("answer", "")):
        passed += 1

    # 8. Chat — unknown shows help
    print("\n8. POST /chat — unknown (help menu)")
    d = post("/chat", {"question": "Tell me a joke"})
    total += 1
    if test("intent=unknown", d.get("intent") == "unknown"):
        passed += 1
    total += 1
    if test("answer has help", "Conut Operations Agent" in d.get("answer", "")):
        passed += 1

    # Summary
    print(f"\n{'='*40}")
    print(f"  {passed}/{total} tests passed")
    if passed == total:
        print("  ALL TESTS PASSED — OpenClaw integration ready!")
    print(f"{'='*40}\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
