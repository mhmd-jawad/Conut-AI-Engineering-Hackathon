from __future__ import annotations

import unittest

import pandas as pd

from app.services.staffing_service import _estimate_staffing
from pipelines.clean_00461 import extract_attendance_records


class AttendanceCleanerTests(unittest.TestCase):
    def test_extract_attendance_records_parses_expected_fields(self) -> None:
        raw_lines = [
            ["Conut - Tyre", "", "", "", "", ""],
            ["", "EMP ID :1.0", "NAME :Person_0001", "", "", ""],
            ["", "Main Street Coffee", "", "", "", ""],
            ["01-Dec-25", "", "07.39.35", "01-Dec-25", "15.00.00", "07.20.25"],
            ["01-Dec-25", "", "18.10.00", "01-Dec-25", "23.00.00", "04.50.00"],
        ]

        rows = extract_attendance_records(raw_lines)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["employee_id"], 1)
        self.assertEqual(rows[0]["employee_name"], "Person_0001")
        self.assertEqual(rows[0]["branch"], "Main Street Coffee")
        self.assertEqual(rows[0]["shift"], "morning")
        self.assertEqual(rows[1]["shift"], "evening")


class StaffingEstimatorTests(unittest.TestCase):
    def test_estimate_staffing_applies_demand_adjustment(self) -> None:
        attendance_records = []
        per_day_counts = [3, 3, 3, 4, 4, 3]
        dates = pd.date_range("2025-12-01", periods=len(per_day_counts), freq="D")

        for day, count in zip(dates, per_day_counts):
            for employee_id in range(1, count + 1):
                attendance_records.append(
                    {
                        "employee_id": employee_id,
                        "branch": "Conut",
                        "date": day,
                        "shift": "evening",
                        "hours_worked": 8.0,
                    }
                )

        attendance_df = pd.DataFrame(attendance_records)
        monthly_sales_df = pd.DataFrame(
            {
                "branch": ["Conut"] * 5,
                "month": ["August", "September", "October", "November", "December"],
                "year": [2025, 2025, 2025, 2025, 2025],
                "total": [100.0, 110.0, 120.0, 130.0, 140.0],
            }
        )

        result = _estimate_staffing(attendance_df, monthly_sales_df, "Conut", "evening")

        self.assertEqual(result["recommended_staff"], 4)
        self.assertGreater(result["demand_factor"], 1.0)
        self.assertGreaterEqual(result["scenarios"]["high"], result["recommended_staff"])
        self.assertEqual(result["shift"], "evening")


if __name__ == "__main__":
    unittest.main()
