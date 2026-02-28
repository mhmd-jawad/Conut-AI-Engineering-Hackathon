"""
Tests for the Operational AI Agent:
  - intent classification
  - entity extraction
  - end-to-end ask()
"""

from __future__ import annotations

import sys
import os
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agent.intent import classify_intent, _extract_branch, _extract_shift, _extract_horizon, _extract_top_k


# ════════════════════════════════════════════════════════════════════════
#  1. Intent classification
# ════════════════════════════════════════════════════════════════════════

class TestIntentClassification(unittest.TestCase):
    """Each intent should be correctly identified from natural language."""

    # ── combo ───────────────────────────────────────────────────────────
    def test_combo_basic(self):
        self.assertEqual(classify_intent("What are the top combos?").action, "combo")

    def test_combo_bundle(self):
        self.assertEqual(classify_intent("Suggest product bundles for Conut Jnah").action, "combo")

    def test_combo_pairing(self):
        self.assertEqual(classify_intent("Which items are frequently bought together?").action, "combo")

    def test_combo_cross_sell(self):
        self.assertEqual(classify_intent("Cross-sell opportunities at Conut Tyre").action, "combo")

    # ── forecast ────────────────────────────────────────────────────────
    def test_forecast_basic(self):
        self.assertEqual(classify_intent("Forecast demand for next 3 months").action, "forecast")

    def test_forecast_predict(self):
        self.assertEqual(classify_intent("Predict sales for Conut Jnah").action, "forecast")

    def test_forecast_trend(self):
        self.assertEqual(classify_intent("What is the sales trend for Conut?").action, "forecast")

    def test_forecast_future(self):
        self.assertEqual(classify_intent("What are the future sales projections?").action, "forecast")

    # ── staffing ────────────────────────────────────────────────────────
    def test_staffing_basic(self):
        self.assertEqual(classify_intent("How many staff for morning shift?").action, "staffing")

    def test_staffing_schedule(self):
        self.assertEqual(classify_intent("Schedule employees for Conut Jnah evening").action, "staffing")

    def test_staffing_headcount(self):
        self.assertEqual(classify_intent("What is the headcount needed?").action, "staffing")

    def test_staffing_how_many(self):
        self.assertEqual(classify_intent("How many people should work the midday shift?").action, "staffing")

    # ── expansion ───────────────────────────────────────────────────────
    def test_expansion_basic(self):
        self.assertEqual(classify_intent("Should we expand?").action, "expansion")

    def test_expansion_new_branch(self):
        self.assertEqual(classify_intent("Is opening a new branch feasible?").action, "expansion")

    def test_expansion_where(self):
        self.assertEqual(classify_intent("Where should we open a new store?").action, "expansion")

    def test_expansion_candidate(self):
        self.assertEqual(classify_intent("What are the candidate locations?").action, "expansion")

    # ── growth ──────────────────────────────────────────────────────────
    def test_growth_basic(self):
        self.assertEqual(classify_intent("Give me a growth strategy").action, "growth")

    def test_growth_coffee(self):
        self.assertEqual(classify_intent("How do we increase coffee sales?").action, "growth")

    def test_growth_milkshake(self):
        self.assertEqual(classify_intent("Milkshake strategy for Conut - Tyre").action, "growth")

    def test_growth_beverage(self):
        self.assertEqual(classify_intent("Improve beverage attachment rate").action, "growth")

    # ── unknown ─────────────────────────────────────────────────────────
    def test_unknown_gibberish(self):
        self.assertEqual(classify_intent("asdf jkl;").action, "unknown")

    def test_unknown_greeting(self):
        self.assertEqual(classify_intent("hello there").action, "unknown")


# ════════════════════════════════════════════════════════════════════════
#  2. Entity extraction
# ════════════════════════════════════════════════════════════════════════

class TestEntityExtraction(unittest.TestCase):

    # ── branch ──────────────────────────────────────────────────────────
    def test_branch_tyre(self):
        self.assertEqual(_extract_branch("combos for Conut - Tyre"), "Conut - Tyre")

    def test_branch_tyre_no_dash(self):
        self.assertEqual(_extract_branch("forecast Conut Tyre"), "Conut - Tyre")

    def test_branch_jnah(self):
        self.assertEqual(_extract_branch("staffing at Conut Jnah"), "Conut Jnah")

    def test_branch_jnah_short(self):
        self.assertEqual(_extract_branch("jnah evening shift"), "Conut Jnah")

    def test_branch_msc(self):
        self.assertEqual(_extract_branch("Main Street Coffee growth"), "Main Street Coffee")

    def test_branch_conut_alone(self):
        self.assertEqual(_extract_branch("demand for Conut next month"), "Conut")

    def test_branch_all(self):
        self.assertEqual(_extract_branch("all branches forecast"), "all")

    def test_branch_none(self):
        self.assertIsNone(_extract_branch("what are the top combos?"))

    # ── shift ───────────────────────────────────────────────────────────
    def test_shift_morning(self):
        self.assertEqual(_extract_shift("morning shift staffing"), "morning")

    def test_shift_evening(self):
        self.assertEqual(_extract_shift("How many staff for the evening?"), "evening")

    def test_shift_midday(self):
        self.assertEqual(_extract_shift("midday schedule"), "midday")

    def test_shift_none(self):
        self.assertIsNone(_extract_shift("how many staff?"))

    # ── horizon ─────────────────────────────────────────────────────────
    def test_horizon_next_4(self):
        self.assertEqual(_extract_horizon("forecast next 4 months"), 4)

    def test_horizon_6_ahead(self):
        self.assertEqual(_extract_horizon("6 months ahead prediction"), 6)

    def test_horizon_default(self):
        self.assertEqual(_extract_horizon("forecast demand"), 3)

    def test_horizon_cap_12(self):
        self.assertEqual(_extract_horizon("forecast next 24 months"), 12)

    # ── top_k ───────────────────────────────────────────────────────────
    def test_top_k_10(self):
        self.assertEqual(_extract_top_k("top 10 combos"), 10)

    def test_top_k_default(self):
        self.assertEqual(_extract_top_k("best combos"), 5)


# ════════════════════════════════════════════════════════════════════════
#  3. End-to-end ask() — integration tests
# ════════════════════════════════════════════════════════════════════════

class TestAgentEndToEnd(unittest.TestCase):
    """These call real services → need processed CSV data on disk."""

    def test_ask_combo(self):
        from app.agent.agent import ask
        resp = ask("What are the top 3 combos for Conut Jnah?")
        self.assertEqual(resp.intent, "combo")
        self.assertEqual(resp.branch, "Conut Jnah")
        self.assertIn("Combo", resp.answer)
        self.assertIsNone(resp.error)
        self.assertGreater(resp.elapsed_ms, 0)

    def test_ask_forecast(self):
        from app.agent.agent import ask
        resp = ask("Forecast demand for Conut - Tyre next 4 months")
        self.assertEqual(resp.intent, "forecast")
        self.assertEqual(resp.branch, "Conut - Tyre")
        self.assertIn("Forecast", resp.answer)
        self.assertIsNone(resp.error)

    def test_ask_expansion(self):
        from app.agent.agent import ask
        resp = ask("Should we expand? Where should we open?")
        self.assertEqual(resp.intent, "expansion")
        self.assertIn("Expansion", resp.answer)
        self.assertIsNone(resp.error)

    def test_ask_unknown_gives_help(self):
        from app.agent.agent import ask
        resp = ask("Tell me a joke")
        self.assertEqual(resp.intent, "unknown")
        self.assertIn("Conut Operations Agent", resp.answer)

    def test_ask_growth(self):
        from app.agent.agent import ask
        resp = ask("Give me a coffee growth strategy for Main Street Coffee")
        self.assertEqual(resp.intent, "growth")
        self.assertEqual(resp.branch, "Main Street Coffee")
        self.assertIn("Growth", resp.answer)


# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main()
