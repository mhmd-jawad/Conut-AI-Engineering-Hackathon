"""
clean_00461.py
--------------
Cleans REP_S_00461.csv (Time & Attendance Report) into a tidy table.

Output:
    data/processed/Time_Attendance_Dec2025.csv
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "REP_S_00461.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "Time_Attendance_Dec2025.csv"


def duration_to_hours(duration: str) -> float:
    value = duration.strip()
    if not value:
        return 0.0
    parts = value.split(".") if "." in value else value.split(":")
    if len(parts) != 3:
        return 0.0
    try:
        hours, minutes, seconds = map(int, parts)
    except ValueError:
        return 0.0
    return round(hours + minutes / 60 + seconds / 3600, 2)


def clean() -> None:
    with RAW_PATH.open(newline="", encoding="utf-8-sig") as f:
        raw_lines = list(csv.reader(f))

    rows = []
    current_emp_id = None
    current_employee_name = None
    current_branch = None

    for line in raw_lines:
        joined = ",".join(line).strip()
        if not joined:
            continue

        if re.search(r"Time\s*&\s*Attendance Report|From Date:|PUNCH IN|PUNCH OUT|REP_S_00461|Copyright|omegapos", joined, re.IGNORECASE):
            continue

        first = line[0].strip() if len(line) > 0 else ""
        stripped_cells = [cell.strip() for cell in line if cell.strip()]

        if re.match(r",,,,Total\s*:", joined, re.IGNORECASE):
            continue

        emp_match = re.search(r"EMP ID\s*:(\d+(?:\.\d+)?)", joined, re.IGNORECASE)
        name_match = re.search(r"NAME\s*:(Person_\d+)", joined, re.IGNORECASE)
        if emp_match and name_match:
            current_emp_id = int(float(emp_match.group(1)))
            current_employee_name = name_match.group(1)
            continue

        branch_candidates = {"Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"}
        branch_found = next((cell for cell in stripped_cells if cell in branch_candidates), None)
        if branch_found and not re.search(r"EMP ID|NAME", joined, re.IGNORECASE):
            current_branch = branch_found
            continue

        # data row format: in_date, empty, in_time, out_date, out_time, work_duration
        is_data_row = bool(re.match(r"\d{2}-[A-Za-z]{3}-\d{2}$", first))
        if is_data_row and current_emp_id and current_employee_name and current_branch:
            in_date = first
            in_time = line[2].strip() if len(line) > 2 else ""
            out_date = line[3].strip() if len(line) > 3 else ""
            out_time = line[4].strip() if len(line) > 4 else ""
            duration = line[5].strip() if len(line) > 5 else ""

            duration_hours = duration_to_hours(duration)
            if duration_hours <= 0.02:
                continue

            rows.append(
                {
                    "Emp ID": current_emp_id,
                    "Employee Name": current_employee_name,
                    "Branch": current_branch,
                    "Punch In Date": in_date,
                    "Punch In Time": in_time,
                    "Punch Out Date": out_date,
                    "Punch Out Time": out_time,
                    "Work Duration": duration,
                    "Duration Hours": duration_hours,
                }
            )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Emp ID",
                "Employee Name",
                "Branch",
                "Punch In Date",
                "Punch In Time",
                "Punch Out Date",
                "Punch Out Time",
                "Work Duration",
                "Duration Hours",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Cleaned: {OUT_PATH}")
    print(f"   Rows: {len(rows)}")


if __name__ == "__main__":
    clean()
