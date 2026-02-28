"""
clean_00334.py
--------------
Cleans rep_s_00334_1_SMRY.csv — Monthly Sales by Branch.

Raw structure:
  - Rows 0-3:   Report header (company, title, date, year/page info)
  - Row 4:      Column headers ("Month,,Year,Total,")
  - Data blocks: "Branch Name: X" row → monthly rows → "Total for 2025" → "Total by Branch" 
  - Page 2 header repeats (date + page info)
  - Grand Total row
  - Footer / copyright row

Cleaning steps:
  1. Strip all junk rows: report header, column header repeats, page markers,
     "Total for YYYY", "Total by Branch", Grand Total, footer, blanks.
  2. Detect "Branch Name:" rows to capture current branch.
  3. Keep only month/year/total data rows; attach branch.
  4. Parse numeric total (strip commas/quotes) → float.
  5. Output tidy CSV: branch, month, year, total
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "rep_s_00334_1_SMRY.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "monthly_sales_by_branch.csv"

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SKIP_PATTERNS = [
    r"Monthly Sales",
    r"Page \d+ of",
    r"Year:",
    r"^Month",
    r"Total for\s+\d{4}",
    r"Total by Branch",
    r"Grand Total",
    r"Copyright",
    r"omegapos",
    r"REP_S_00334",
]


def parse_number(value: str) -> float:
    cleaned = value.strip().strip('"').replace(",", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean():
    with RAW_PATH.open(newline="", encoding="utf-8-sig") as f:
        raw_lines = list(csv.reader(f))

    rows = []
    current_branch = None

    for line in raw_lines:
        joined = ",".join(line).strip()

        # Skip blank rows
        if not joined:
            continue

        # Skip known junk
        if any(re.search(p, joined, re.IGNORECASE) for p in SKIP_PATTERNS):
            continue

        # Capture branch name
        branch_match = re.match(r"Branch Name:\s*(.+?)(?:,|$)", joined, re.IGNORECASE)
        if branch_match:
            current_branch = branch_match.group(1).strip()
            continue

        # Data row: Month,,Year,Total  (line[0]=month, line[2]=year, line[3]=total)
        if len(line) >= 4 and line[0].strip() in MONTH_ORDER and current_branch:
            month = line[0].strip()
            year  = line[2].strip()
            total = parse_number(line[3])
            rows.append({
                "branch": current_branch,
                "month":  month,
                "year":   int(year) if year.isdigit() else year,
                "total":  total,
            })

    # ── Write output ───────────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["branch", "month", "year", "total"]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"✅  Cleaned output → {OUT_PATH}")
    print(f"    Rows written : {len(rows)}\n")
    print(f"  {'Branch':<25} {'Month':<12} {'Year':>6} {'Total':>22}")
    print("  " + "-" * 68)
    for r in rows:
        print(f"  {r['branch']:<25} {r['month']:<12} {r['year']:>6} {r['total']:>22,.2f}")

    grand = sum(r["total"] for r in rows)
    print("  " + "-" * 68)
    print(f"  {'GRAND TOTAL':<25} {'':12} {'':>6} {grand:>22,.2f}")


if __name__ == "__main__":
    clean()
