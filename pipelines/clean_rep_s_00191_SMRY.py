import pandas as pd
import numpy as np
import csv, re

IN_PATH = "rep_s_00191_SMRY.csv"
OUT_PATH = "rep_s_00191_SMRY_cleaned.csv"

def read_csv_robust(path):
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as f:
                sample = f.read(10000)
            dialect = csv.Sniffer().sniff(sample, delimiters=[",",";","\t","|"])
            sep = dialect.delimiter
            df = pd.read_csv(
                path,
                encoding=enc,
                sep=sep,
                engine="python",
                dtype="string",
                keep_default_na=False,
                on_bad_lines="skip",
            )
            return df
        except Exception as e:
            last_err = e
    raise last_err

def is_numberish(x: str) -> bool:
    s = str(x).strip()
    if s == "" or s.lower() in {"<na>", "na", "nan", "none"}:
        return False
    s = s.replace(",", "")
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", s))

def to_float(x):
    return float(str(x).strip().replace(",", "")) if is_numberish(x) else np.nan

def clean_sales_items_report(df: pd.DataFrame) -> pd.DataFrame:
    raw = df.fillna("").astype("string")
    raw = raw.apply(lambda col: col.str.replace("\r\n", "\n").str.replace("\r", "\n"))

    report_date = None
    context = None
    date_pat = re.compile(r"^\s*\d{1,2}-[A-Za-z]{3}-\d{2}\s*$")

    for val in raw.iloc[:, 0].astype(str).tolist():
        if date_pat.match(val):
            report_date = val.strip()
            break

    for row in raw.astype(str).itertuples(index=False):
        for cell in row:
            if "Years:" in cell or "Year:" in cell:
                context = cell.strip()
                break
        if context:
            break

    def is_non_data_row(cells):
        cells = [str(c).strip() for c in cells]
        joined = " ".join([c for c in cells if c])
        if joined == "":
            return True
        if "Sales by Items By Group" in joined:
            return True
        if "Page" in joined and "of" in joined:
            return True
        if date_pat.match(cells[0]):
            return True
        if re.search(r"\bDescription\b", joined) and re.search(r"\bBarcode\b", joined) and re.search(r"\bQty\b", joined):
            return True
        return False

    keep = ~raw.apply(lambda row: is_non_data_row(list(row)), axis=1)
    data = raw.loc[keep].copy()

    records = []
    branch = None
    division = None
    group = None

    for _, r in data.iterrows():
        # up to 5 columns in this export
        cols = [str(x).strip() for x in r.tolist()]
        cols += [""] * (5 - len(cols))

        c0, c1, c2, c3, c4 = cols[:5]

        if c0.startswith("Branch:"):
            branch = c0.split("Branch:", 1)[1].strip() or None
            continue
        if c0.startswith("Division:"):
            division = c0.split("Division:", 1)[1].strip() or None
            continue
        if c0.startswith("Group:"):
            group = c0.split("Group:", 1)[1].strip() or None
            continue

        desc = c0
        barcode = c1 if c1 else None

        qty = to_float(c2)
        amount = to_float(c3) if is_numberish(c3) else to_float(c4)

        # fallback shifts
        if np.isnan(qty) and is_numberish(c1):
            qty = to_float(c1)
            barcode = None
        if np.isnan(amount) and is_numberish(c2):
            amount = to_float(c2)

        if desc and (not np.isnan(qty) or not np.isnan(amount)):
            records.append({
                "report_date": report_date,
                "context": context,
                "branch": branch,
                "division": division,
                "group": group,
                "description": desc,
                "barcode": barcode,
                "qty": qty,
                "total_amount": amount,
            })

    cleaned = pd.DataFrame.from_records(records)

    for col in ["report_date", "context", "branch", "division", "group", "description", "barcode"]:
        cleaned[col] = cleaned[col].astype("string").str.strip()
    cleaned["description"] = cleaned["description"].str.replace(r"\s+", " ", regex=True)

    # remove summary lines like "Total by Division: ..."
    cleaned = cleaned[~cleaned["description"].str.contains(r"^Total by ", regex=True, na=False)]

    cleaned = cleaned.drop_duplicates()
    sort_cols = [c for c in ["branch", "division", "group", "description"] if c in cleaned.columns]
    if sort_cols:
        cleaned = cleaned.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    return cleaned

if __name__ == "__main__":
    df = read_csv_robust(IN_PATH)
    cleaned = clean_sales_items_report(df)
    cleaned.to_csv(OUT_PATH, index=False)
    print(f"Saved: {OUT_PATH}  rows={len(cleaned)}  cols={cleaned.shape[1]}")
