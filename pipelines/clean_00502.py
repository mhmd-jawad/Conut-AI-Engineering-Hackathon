"""
clean_00502.py
--------------
Cleans REP_S_00502.csv (Sales by customer in details - delivery) into a tidy table.

Output:
    data/processed/Delivery_Sales_By_Customer_Jan2026.csv
"""

import csv
import re
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "REP_S_00502.csv"
OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "Delivery_Sales_By_Customer_Jan2026.csv"


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

    rows = []
    current_branch = None
    current_customer = None

    for line in raw_lines:
        joined = ",".join(line).strip()
        if not joined:
            continue

        if re.search(r"Sales by customer in details|From Date:|To Date:|Page \d+ of|Full Name,Qty|REP_S_00502|Copyright|omegapos", joined, re.IGNORECASE):
            continue

        first = line[0].strip() if len(line) > 0 else ""

        branch_match = re.match(r"Branch\s*:(.+)$", first, re.IGNORECASE)
        if branch_match:
            current_branch = branch_match.group(1).strip()
            current_customer = None
            continue

        if re.match(r"Total\s*:|Total Branch:", first, re.IGNORECASE):
            continue

        if re.match(r"^(?:0\s+)?Person_\d+", first):
            current_customer = normalize_customer_name(first)
            continue

        # detail line format: "", qty, description, price, ...
        if first == "" and current_branch and current_customer:
            qty = parse_number(line[1]) if len(line) > 1 else 0.0
            description = line[2].strip() if len(line) > 2 else ""
            price = parse_number(line[3]) if len(line) > 3 else 0.0

            if not description:
                continue

            description = " ".join(description.split())
            line_total = round(qty * price, 2)

            is_cancellation = qty < 0 or price < 0

            rows.append(
                {
                    "Branch": current_branch,
                    "Customer Name": current_customer,
                    "Item Description": description,
                    "Qty": qty,
                    "Price": price,
                    "Line Total": line_total,
                    "Is Cancellation": int(is_cancellation),
                }
            )

    # remove pure cancellation rows for cleaned analytics table
    cleaned_rows = [r for r in rows if r["Qty"] > 0 and r["Price"] >= 0]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Branch",
                "Customer Name",
                "Item Description",
                "Qty",
                "Price",
                "Line Total",
                "Is Cancellation",
            ],
        )
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"✅ Cleaned: {OUT_PATH}")
    print(f"   Rows kept: {len(cleaned_rows)}")
    print(f"   Raw item rows parsed: {len(rows)}")


if __name__ == "__main__":
    clean()
