"""
clean_00435.py
--------------
Cleans rep_s_00435_SMRY.csv — Average Sales by Menu/Channel.

Note: rep_s_00435_SMRY (1).csv is a byte-identical duplicate and is intentionally
      ignored. Only the canonical file is processed.

Raw structure (~22 lines, 1 page):
  - Rows 0-3:   Report header (company, title, year/page, date)
  - Row 4:      Column headers ("Menu Name,# Cust,Sales,Avg Customer,")
  - Data blocks: Branch name row → channel rows → "Total By Branch:" row
  - Last data row: "Total :" grand total
  - Footer / copyright row

Cleaning steps:
  1. Skip all junk rows: report header, column header, page markers, "Total By Branch",
     grand total, footer, blank rows.
  2. Detect branch-name rows (non-channel context rows) to carry branch as a column.
  3. Keep only channel rows (DELIVERY / TABLE / TAKE AWAY).
  4. Parse numeric columns (strip commas/quotes) → float.
  5. Output tidy CSV: branch, channel, num_customers, sales, avg_per_customer
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "rep_s_00435_SMRY.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "avg_sales_by_menu_channel.csv"

KNOWN_CHANNELS = {"DELIVERY", "TABLE", "TAKE AWAY"}

SKIP_PATTERNS = [
    r"Average Sales By Menu",
    r"Year:",
    r"Page \d+ of",
    r"Menu Name",
    r"Total By Branch",
    r"^Total\s*:",
    r"Copyright",
    r"omegapos",
    r"REP_S_00435",
]

KNOWN_BRANCHES = {"Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"}


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

        # Detect branch-name row: first cell matches a known branch, rest are empty
        first_cell = line[0].strip()
        rest_empty = all(c.strip() == "" for c in line[1:])
        if first_cell in KNOWN_BRANCHES and rest_empty:
            current_branch = first_cell
            continue

        # Data row: first cell is a channel name
        if first_cell in KNOWN_CHANNELS and current_branch:
            num_customers    = parse_number(line[1]) if len(line) > 1 else 0.0
            sales            = parse_number(line[2]) if len(line) > 2 else 0.0
            avg_per_customer = parse_number(line[3]) if len(line) > 3 else 0.0
            rows.append({
                "branch":           current_branch,
                "channel":          first_cell,
                "num_customers":    num_customers,
                "sales":            sales,
                "avg_per_customer": avg_per_customer,
            })

    # ── Write output ───────────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["branch", "channel", "num_customers", "sales", "avg_per_customer"]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"✅  Cleaned output → {OUT_PATH}")
    print(f"    Rows written : {len(rows)}")
    print(f"    Note: rep_s_00435_SMRY (1).csv is identical — skipped.\n")
    print(f"  {'Branch':<25} {'Channel':<12} {'# Cust':>8} {'Sales':>22} {'Avg/Cust':>18}")
    print("  " + "-" * 90)
    for r in rows:
        print(
            f"  {r['branch']:<25} {r['channel']:<12} {r['num_customers']:>8,.0f} "
            f"{r['sales']:>22,.2f} {r['avg_per_customer']:>18,.2f}"
        )
    grand_sales = sum(r["sales"] for r in rows)
    grand_cust  = sum(r["num_customers"] for r in rows)
    print("  " + "-" * 90)
    print(f"  {'GRAND TOTAL':<25} {'':12} {grand_cust:>8,.0f} {grand_sales:>22,.2f}")


if __name__ == "__main__":
    clean()
