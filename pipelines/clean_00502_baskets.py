"""
clean_00502_baskets.py
----------------------
Cleans REP_S_00502.csv (Sales by customer in details - delivery) into a
basket-oriented table for combo analysis.

Differences from clean_00502.py:
  - Adds `basket_id` column  (Branch + Customer Name)
  - Adds `Is_Modifier` flag   (Price == 0 → modifier / topping)
  - Keeps ALL rows (cancellations + modifiers flagged, not dropped)
    so the analytics layer can filter as needed.

Output:
    data/processed/basket_lines.csv
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "REP_S_00502.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "basket_lines.csv"

FIELDNAMES = [
    "basket_id",
    "Branch",
    "Customer Name",
    "Item Description",
    "Qty",
    "Price",
    "Line Total",
    "Is Cancellation",
    "Is_Modifier",
]


def parse_number(value: str) -> float:
    cleaned = value.strip().strip('"').replace(",", "")
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def normalize_customer_name(raw_name: str) -> str:
    name = raw_name.strip()
    name = re.sub(r"^0\s+", "", name)
    return name


def clean() -> None:
    with RAW_PATH.open(newline="", encoding="utf-8-sig") as f:
        raw_lines = list(csv.reader(f))

    rows: list[dict] = []
    current_branch: str | None = None
    current_customer: str | None = None

    for line in raw_lines:
        joined = ",".join(line).strip()
        if not joined:
            continue

        # Skip report chrome (headers, footers, page markers)
        if re.search(
            r"Sales by customer in details|From Date:|To Date:|Page \d+ of|"
            r"Full Name,Qty|REP_S_00502|Copyright|omegapos",
            joined,
            re.IGNORECASE,
        ):
            continue

        first = line[0].strip() if len(line) > 0 else ""

        # Branch header
        branch_match = re.match(r"Branch\s*:(.+)$", first, re.IGNORECASE)
        if branch_match:
            current_branch = branch_match.group(1).strip()
            current_customer = None
            continue

        # Totals – skip
        if re.match(r"Total\s*:|Total Branch:", first, re.IGNORECASE):
            continue

        # Customer header
        if re.match(r"^(?:0\s+)?Person_\d+", first):
            current_customer = normalize_customer_name(first)
            continue

        # Detail line:  "", qty, description, price, ...
        if first == "" and current_branch and current_customer:
            qty = parse_number(line[1]) if len(line) > 1 else 0.0
            description = line[2].strip() if len(line) > 2 else ""
            price = parse_number(line[3]) if len(line) > 3 else 0.0

            if not description:
                continue

            description = " ".join(description.split())
            line_total = round(qty * price, 2)
            is_cancellation = int(qty < 0 or price < 0)
            is_modifier = int(price == 0.0)

            basket_id = f"{current_branch}__{current_customer}"

            rows.append(
                {
                    "basket_id": basket_id,
                    "Branch": current_branch,
                    "Customer Name": current_customer,
                    "Item Description": description,
                    "Qty": qty,
                    "Price": price,
                    "Line Total": line_total,
                    "Is Cancellation": is_cancellation,
                    "Is_Modifier": is_modifier,
                }
            )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    n_cancel = sum(1 for r in rows if r["Is Cancellation"])
    n_mod = sum(1 for r in rows if r["Is_Modifier"])
    baskets = len({r["basket_id"] for r in rows})

    print(f"✅ basket_lines.csv written → {OUT_PATH}")
    print(f"   Total rows:        {len(rows)}")
    print(f"   Unique baskets:    {baskets}")
    print(f"   Cancellation rows: {n_cancel}")
    print(f"   Modifier rows:     {n_mod}")


if __name__ == "__main__":
    clean()
