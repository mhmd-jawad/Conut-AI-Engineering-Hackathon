"""
clean_00150.py
--------------
Cleans rep_s_00150.csv — Customer Orders (Delivery) by Branch.

Raw structure (581 lines, 15 pages):
  - Row 0-1:  Report header (company name, report title)
  - Row 2:    Page 1 date + page marker
  - Row 3:    Column headers
  - Row 4:    First branch name row ("Conut - Tyre,,,...")
  - Data rows: Person_XXXX, address, phone, first_order, <empty>, last_order, <empty>, total, num_orders
  - Every ~35 rows: page header repeat (date + page marker) then column header repeat
  - Branch transitions: branch name row then next block of customers
  - Per-branch footer: ",,Total By Branch, <first_ts>,,<last_ts>,,<total>,<count>,"
  - Last page (page 15): an EXTRA empty column is inserted, shifting Total to index 8
  - Footer: REP_S_00150, copyright line

Cleaning steps:
  1. Skip all junk: report header, page-date rows, column-header rows, total-by-branch
     rows, copyright/footer rows, blank rows.
  2. Detect branch-name rows (first cell matches a known branch, all other cells empty)
     and carry branch name as context.
  3. Keep only customer data rows (first cell starts with "Person_").
  4. Extract: customer_name, phone, first_order, last_order, total, num_orders.
     - Handle the column-shift on the last page by checking length: if len >= 11,
       Total is at index 8; otherwise Total is at index 7.
  5. Clean timestamps: strip trailing colon, standardise to "YYYY-MM-DD HH:MM".
  6. Clean address: strip leading/trailing whitespace; replace blank-only to empty string.
  7. Parse numeric columns (strip commas/quotes) → float / int.
  8. Output tidy CSV: branch, customer_name, phone, address, first_order, last_order,
     total, num_orders.
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "rep_s_00150.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "customer_orders_delivery.csv"

KNOWN_BRANCHES = {"Conut", "Conut - Tyre", "Conut Jnah", "Main Street Coffee"}

SKIP_PATTERNS = [
    r"Customer Orders",
    r"Page \d+ of",
    r"From Date:",
    r"^Customer Name",
    r"^,,Total By Branch",
    r"Copyright",
    r"omegapos",
    r"REP_S_00150",
]


def clean_timestamp(raw: str) -> str:
    """Strip trailing colon/whitespace from truncated timestamps like '2025-12-31 19:04:'."""
    ts = raw.strip().rstrip(":")
    return ts if ts else ""


def parse_number(value: str) -> float:
    cleaned = value.strip().strip('"').replace(",", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean_address(raw: str) -> str:
    """Return stripped address; blank/whitespace-only → empty string."""
    stripped = raw.strip()
    return "" if not stripped else stripped


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

        # Skip known junk rows
        if any(re.search(p, joined, re.IGNORECASE) for p in SKIP_PATTERNS):
            continue

        first_cell = line[0].strip()

        # Detect branch-name rows: first cell is a known branch, all others empty
        rest_empty = all(c.strip() == "" for c in line[1:])
        if first_cell in KNOWN_BRANCHES and rest_empty:
            current_branch = first_cell
            continue

        # Customer data rows
        if first_cell.startswith("Person_") and current_branch:
            # Normal pages (1-14): layout is
            #   [0] name  [1] address  [2] phone  [3] first_order  [4] empty
            #   [5] last_order  [6] empty  [7] total  [8] num_orders  [9] empty
            #
            # Last page (15): an extra empty column pushes Total to index 8:
            #   [0] name  [1] address  [2] phone  [3] first_order  [4] empty
            #   [5] last_order  [6] empty  [7] empty  [8] total  [9] num_orders  [10] empty
            #
            # Heuristic: if column 7 is blank and column 8 has a value → last-page layout

            col7 = line[7].strip() if len(line) > 7 else ""
            col8 = line[8].strip() if len(line) > 8 else ""

            if col7 == "" and col8 != "":
                # Last-page shifted layout
                total_raw      = col8
                num_orders_raw = line[9].strip() if len(line) > 9 else ""
            else:
                # Normal layout
                total_raw      = col7
                num_orders_raw = line[8].strip() if len(line) > 8 else ""

            rows.append({
                "branch":       current_branch,
                "customer_name": first_cell,
                "address":      clean_address(line[1]) if len(line) > 1 else "",
                "phone":        line[2].strip()        if len(line) > 2 else "",
                "first_order":  clean_timestamp(line[3]) if len(line) > 3 else "",
                "last_order":   clean_timestamp(line[5]) if len(line) > 5 else "",
                "total":        parse_number(total_raw),
                "num_orders":   int(parse_number(num_orders_raw)),
            })

    # ── Write output ───────────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "branch", "customer_name", "address", "phone",
        "first_order", "last_order", "total", "num_orders",
    ]

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"✅  Cleaned output → {OUT_PATH}")
    print(f"    Total rows written : {len(rows)}\n")

    # Per-branch counts
    from collections import Counter
    branch_counts = Counter(r["branch"] for r in rows)
    zero_total    = sum(1 for r in rows if r["total"] == 0.0)
    with_address  = sum(1 for r in rows if r["address"] != "")
    repeat_buyers = sum(1 for r in rows if r["num_orders"] > 1)

    print(f"  {'Branch':<25} {'Customers':>10} {'Total Revenue':>22}")
    print("  " + "-" * 60)
    for branch, count in sorted(branch_counts.items()):
        rev = sum(r["total"] for r in rows if r["branch"] == branch)
        print(f"  {branch:<25} {count:>10,} {rev:>22,.2f}")
    grand_rev = sum(r["total"] for r in rows)
    print("  " + "-" * 60)
    print(f"  {'GRAND TOTAL':<25} {len(rows):>10,} {grand_rev:>22,.2f}")
    print(f"\n  Zero-total rows (likely cancelled) : {zero_total}")
    print(f"  Rows with non-blank address        : {with_address}")
    print(f"  Repeat buyers (num_orders > 1)     : {repeat_buyers}")


if __name__ == "__main__":
    clean()
