from __future__ import annotations

import os
import sys
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.combo_service import compare_combo_solutions, recommend_combos
from main import app


class ComboCompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.payload = {
            "branch": "all",
            "top_k": 5,
            "include_modifiers": False,
            "min_support": 0.02,
            "min_confidence": 0.15,
            "min_lift": 1.0,
        }

    def test_combo_endpoint_shape_is_unchanged(self) -> None:
        result = recommend_combos(**self.payload)
        self.assertIn("branch", result)
        self.assertIn("total_baskets", result)
        self.assertIn("include_modifiers", result)
        self.assertIn("recommendations", result)
        self.assertIn("explanation", result)

    def test_compare_response_contains_required_lines(self) -> None:
        result = compare_combo_solutions(**self.payload)
        self.assertTrue(result["non_ai_answer_line"].startswith("The non AI answer:"))
        self.assertTrue(
            result["ml_answer_line"].startswith("The ML [Item-Item Cosine Similarity] answer:")
        )

    def test_compare_model_name(self) -> None:
        result = compare_combo_solutions(**self.payload)
        self.assertEqual(result["model_name"], "Item-Item Cosine Similarity")

    def test_precision_at_k_is_none_or_unit_interval(self) -> None:
        result = compare_combo_solutions(**self.payload)
        precision = result["ml_precision_at_k"]
        if precision is not None:
            self.assertGreaterEqual(precision, 0.0)
            self.assertLessEqual(precision, 1.0)

    def test_unknown_branch_returns_safe_structure(self) -> None:
        result = compare_combo_solutions(
            branch="branch-does-not-exist",
            top_k=5,
            include_modifiers=False,
            min_support=0.02,
            min_confidence=0.15,
            min_lift=1.0,
        )
        self.assertEqual(result["non_ai_recommendations"], [])
        self.assertEqual(result["ml_recommendations"], [])
        self.assertIsNone(result["ml_precision_at_k"])

    def test_ml_output_is_deterministic(self) -> None:
        first = compare_combo_solutions(**self.payload)
        second = compare_combo_solutions(**self.payload)
        self.assertEqual(first["ml_precision_at_k"], second["ml_precision_at_k"])
        self.assertEqual(first["ml_recommendations"], second["ml_recommendations"])

    def test_combo_compare_endpoint(self) -> None:
        response = self.client.post("/combo-compare", json=self.payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model_name"], "Item-Item Cosine Similarity")
        self.assertTrue(body["non_ai_answer_line"].startswith("The non AI answer:"))
        self.assertTrue(
            body["ml_answer_line"].startswith("The ML [Item-Item Cosine Similarity] answer:")
        )


if __name__ == "__main__":
    unittest.main()
