"""
clean_00194.py
--------------
Cleans REP_S_00194_SMRY.csv — Tax Summary by Branch.

Raw structure (15 lines):
  - Row 0:       Report company/branch header  (e.g. "Conut - Tyre,,,...")
  - Row 1:       Report title                  ("Tax Report,,,...")
  - Row 2:       Print date + page info        ("30-Jan-26,,,...,Page 1 of, 1")
  - Row 3:       Year/period line              (",Year: 2025 - All Months,,...")
  - Row 4:       Column headers                ("TAX DESCRIPTION,VAT 11 %,Tax 2,...")
  - Rows 5-6:    Branch block (Conut)
  - Rows 7-8:    Branch block (Conut - Tyre)
  - Rows 9-10:   Branch block (Conut Jnah)
  - Rows 11-12:  Branch block (Main Street Coffee)
  - Row 13:      Footer / copyright
  - Row 14:      (empty)

Cleaning steps:
  1. Skip all non-data rows (header, title, date, period, footer, empty rows).
  2. Detect "Branch Name:" rows to extract the branch name as context.
  3. Keep only "Total By Branch" rows and attach the branch name.
  4. Parse and cast numeric columns (strip commas from quoted numbers).
  5. Output a tidy CSV: branch, vat_11_pct, service, total
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "REP_S_00194_SMRY.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "tax_summary_by_branch.csv"


def parse_number(value: str) -> float:
    """Strip commas and quotes, then cast to float. Returns 0.0 for blanks."""
    cleaned = value.strip().strip('"').replace(",", "")
    if cleaned == "" or cleaned == "0.00":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean():
    rows = []

    with RAW_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        raw_lines = list(reader)

    current_branch = None

    for line in raw_lines:
        # Join to a single string for pattern checks
        joined = ",".join(line).strip()

        # ── Skip blank / whitespace-only rows ──────────────────────────────────
        if not joined:
            continue

        # ── Skip known junk rows ───────────────────────────────────────────────
        if re.search(r"Tax Report|Copyright|omegapos|REP_S_00194", joined, re.IGNORECASE):
            continue
        if re.search(r"Page \d+ of", joined, re.IGNORECASE):
            continue
        if re.search(r"Year:", joined, re.IGNORECASE):
            continue
        if re.search(r"TAX DESCRIPTION", joined, re.IGNORECASE):
            continue

        # ── Capture branch name ────────────────────────────────────────────────
        branch_match = re.match(r"Branch Name:\s*(.+?)(?:,|$)", joined, re.IGNORECASE)
        if branch_match:
            current_branch = branch_match.group(1).strip()
            continue

        # ── Keep "Total By Branch" data rows ──────────────────────────────────
        if re.match(r"Total By Branch", joined, re.IGNORECASE):
            # line layout: Total By Branch, VAT11%, Tax2, Tax3, Tax4, Tax5, <empty>, Service, Total
            # indices:          0              1       2     3     4     5      6        7       8
            vat_11   = parse_number(line[1]) if len(line) > 1 else 0.0
            service  = parse_number(line[7]) if len(line) > 7 else 0.0
            total    = parse_number(line[8]) if len(line) > 8 else 0.0

            rows.append({
                "branch":     current_branch,
                "vat_11_pct": vat_11,
                "service":    service,
                "total":      total,
            })
            continue

    # ── Write output ───────────────────────────────────────────────────────────
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["branch", "vat_11_pct", "service", "total"]
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Pretty-print summary ───────────────────────────────────────────────────
    print(f"✅  Cleaned output written to: {OUT_PATH}")
    print(f"    Rows written: {len(rows)}\n")
    print(f"  {'Branch':<25} {'VAT 11%':>20} {'Service':>12} {'Total':>20}")
    print("  " + "-" * 80)
    for r in rows:
        print(f"  {r['branch']:<25} {r['vat_11_pct']:>20,.2f} {r['service']:>12,.2f} {r['total']:>20,.2f}")

    grand_total = sum(r["total"] for r in rows)
    print("  " + "-" * 80)
    print(f"  {'GRAND TOTAL':<25} {sum(r['vat_11_pct'] for r in rows):>20,.2f} {sum(r['service'] for r in rows):>12,.2f} {grand_total:>20,.2f}")


if __name__ == "__main__":
    clean()
