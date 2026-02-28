"""
test_expansion.py
-----------------
Validates the expansion feasibility service end-to-end.
Run:  python tests/test_expansion.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.expansion_service import evaluate_expansion


def test_all_branches():
    print("=" * 70)
    print("TEST 1 — Score all branches (default)")
    print("=" * 70)
    result = evaluate_expansion("")

    assert "error" not in result, f"Unexpected error: {result}"
    assert result["verdict"] in ("GO", "CAUTION", "NO-GO")
    print(f"Verdict: {result['verdict']}")
    print(f"Detail:  {result['verdict_detail']}")

    # Scorecards
    assert len(result["scorecards"]) == 4, f"Expected 4 scorecards, got {len(result['scorecards'])}"
    print(f"\nBranch Scorecards ({len(result['scorecards'])} branches):")
    for sc in result["scorecards"]:
        print(f"  {sc['branch']:25s}  composite={sc['composite_score']:.2f}")
        for dim, info in sc["dimensions"].items():
            s = info["score"]
            print(f"    {dim:25s} {s:6.2f}")
        assert 0 <= sc["composite_score"] <= 100, f"Score out of range: {sc['composite_score']}"

    # Archetype
    arch = result["best_archetype"]
    print(f"\nBest archetype: {arch['branch']}  (score={arch['composite_score']})")
    print(f"  Channel mix: {arch['channel_mix']}")
    print(f"  Top categories: {list(arch['top_categories'].keys())}")
    print(f"  Beverage %: {arch['beverage_pct']:.1f}%")
    print(f"  Recommendation: {arch['recommendation']}")

    # Candidate locations
    locs = result["candidate_locations"]
    assert len(locs) > 0, "No candidate locations returned"
    # None should have conut_present
    print(f"\nCandidate Locations (top {len(locs)}):")
    for loc in locs:
        print(f"  {loc['area']:25s} ({loc['governorate']:15s})  score={loc['score']:.2f}  "
              f"pop={loc['population']:>7,}  uni={'Y' if loc['university_nearby'] else 'N'}  "
              f"foot={loc['foot_traffic_tier']}  rent={loc['rent_tier']}  cafe={loc['cafe_density']}")
        if loc["pros"]:
            print(f"    + {', '.join(loc['pros'])}")
        if loc["cons"]:
            print(f"    - {', '.join(loc['cons'])}")

    # Risks
    assert len(result["risks"]) >= 3, "Expected at least 3 risk items"
    print(f"\nRisks ({len(result['risks'])}):")
    for r in result["risks"]:
        print(f"  • {r}")

    print(f"\nExplanation: {result['explanation']}")
    print("\n✅ TEST 1 PASSED\n")


def test_specific_branch():
    print("=" * 70)
    print("TEST 2 — Specific branch input ('Conut Jnah')")
    print("=" * 70)
    result = evaluate_expansion("Conut Jnah")
    assert "error" not in result
    assert result["verdict"] in ("GO", "CAUTION", "NO-GO")
    print(f"Verdict: {result['verdict']}  |  Best archetype: {result['best_archetype']['branch']}")
    print("✅ TEST 2 PASSED\n")


def test_unknown_branch():
    print("=" * 70)
    print("TEST 3 — Unknown branch ('Mars Base')")
    print("=" * 70)
    result = evaluate_expansion("Mars Base")
    assert "error" in result, "Expected error for unknown branch"
    print(f"Error: {result['error']}")
    print(f"Available: {result['available_branches']}")
    print("✅ TEST 3 PASSED\n")


def test_all_keyword():
    print("=" * 70)
    print("TEST 4 — Branch = 'all'")
    print("=" * 70)
    result = evaluate_expansion("all")
    assert "error" not in result
    assert len(result["scorecards"]) == 4
    print(f"Verdict: {result['verdict']}  |  Scorecards: {len(result['scorecards'])}")
    print("✅ TEST 4 PASSED\n")


if __name__ == "__main__":
    test_all_branches()
    test_specific_branch()
    test_unknown_branch()
    test_all_keyword()
    print("=" * 70)
    print("ALL EXPANSION TESTS PASSED ✅")
    print("=" * 70)
