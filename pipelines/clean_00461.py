"""
clean_00461.py
--------------
Cleans REP_S_00461.csv - Time & Attendance report.

Output: data/processed/attendance.csv with columns:
  - employee_id
  - employee_name
  - branch
  - date
  - punch_in
  - punch_out
  - hours_worked
  - shift
  - day_of_week
  - is_weekend
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "REP_S_00461.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "attendance.csv"

KNOWN_BRANCHES = {"Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"}

EMPLOYEE_ID_RE = re.compile(r"EMP ID\s*:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
EMPLOYEE_NAME_RE = re.compile(r"NAME\s*:\s*([^,]+)", re.IGNORECASE)


def _is_date(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    try:
        datetime.strptime(value, "%d-%b-%y")
        return True
    except ValueError:
        return False


def _is_time(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    try:
        datetime.strptime(value, "%H.%M.%S")
        return True
    except ValueError:
        return False


def parse_duration_to_hours(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None

    sep = "." if "." in value else ":" if ":" in value else None
    if sep is None:
        return None

    parts = value.split(sep)
    if len(parts) != 3:
        return None

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
    except ValueError:
        return None

    if minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59:
        return None

    total_hours = hours + (minutes / 60.0) + (seconds / 3600.0)
    return round(total_hours, 4)


def bucket_shift(punch_in_dt: datetime) -> str:
    hour = punch_in_dt.hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "midday"
    return "evening"


def extract_attendance_records(raw_lines: list[list[str]]) -> list[dict]:
    records: list[dict] = []

    current_employee_id: int | None = None
    current_employee_name: str | None = None
    current_branch: str | None = None

    for line in raw_lines:
        cells = [cell.strip() for cell in line]
        if len(cells) < 6:
            cells.extend([""] * (6 - len(cells)))

        c0, c1, c2, c3, c4, c5 = cells[:6]
        joined = ",".join(cell for cell in (c0, c1, c2, c3, c4, c5) if cell)

        if not joined:
            continue

        if (
            "Time & Attendance Report" in joined
            or "From Date:" in joined
            or "PUNCH IN" in joined
            or "REP_S_00461" in joined
            or "Copyright" in joined
            or "omegapos" in joined
        ):
            continue

        employee_id_match = EMPLOYEE_ID_RE.search(joined)
        if employee_id_match:
            current_employee_id = int(float(employee_id_match.group(1)))
            name_match = EMPLOYEE_NAME_RE.search(joined)
            current_employee_name = name_match.group(1).strip() if name_match else None
            continue

        branch_candidate = c1 or c0
        if branch_candidate in KNOWN_BRANCHES:
            current_branch = branch_candidate
            continue

        if c4.lower().startswith("total"):
            continue

        if not (_is_date(c0) and _is_time(c2) and _is_date(c3) and _is_time(c4)):
            continue
        if current_employee_id is None or current_branch is None:
            continue

        punch_in_dt = datetime.strptime(f"{c0} {c2}", "%d-%b-%y %H.%M.%S")
        punch_out_dt = datetime.strptime(f"{c3} {c4}", "%d-%b-%y %H.%M.%S")

        hours_worked = parse_duration_to_hours(c5)
        if hours_worked is None:
            delta_hours = (punch_out_dt - punch_in_dt).total_seconds() / 3600.0
            if delta_hours < 0:
                delta_hours += 24.0
            hours_worked = round(delta_hours, 4)

        records.append(
            {
                "employee_id": current_employee_id,
                "employee_name": current_employee_name or "",
                "branch": current_branch,
                "date": punch_in_dt.date().isoformat(),
                "punch_in": punch_in_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "punch_out": punch_out_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "hours_worked": hours_worked,
                "shift": bucket_shift(punch_in_dt),
                "day_of_week": punch_in_dt.strftime("%A"),
                "is_weekend": punch_in_dt.weekday() >= 5,
            }
        )

    return records


def clean(raw_path: Path = RAW_PATH, out_path: Path = OUT_PATH) -> int:
    with raw_path.open(newline="", encoding="utf-8-sig") as f:
        raw_lines = list(csv.reader(f))

    rows = extract_attendance_records(raw_lines)
    rows.sort(key=lambda r: (r["date"], r["branch"], r["employee_id"], r["punch_in"]))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "employee_id",
        "employee_name",
        "branch",
        "date",
        "punch_in",
        "punch_out",
        "hours_worked",
        "shift",
        "day_of_week",
        "is_weekend",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    by_branch = Counter(r["branch"] for r in rows)
    by_shift = Counter(r["shift"] for r in rows)

    print(f"Cleaned output -> {out_path}")
    print(f"Rows written   -> {len(rows)}")
    print(f"Branches       -> {dict(by_branch)}")
    print(f"Shift split    -> {dict(by_shift)}")
    return len(rows)


if __name__ == "__main__":
    clean()
