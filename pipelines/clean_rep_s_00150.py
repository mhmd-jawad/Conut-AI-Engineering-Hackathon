import pandas as pd
import numpy as np
import csv, re

IN_PATH = "rep_s_00150.csv"
OUT_PATH = "rep_s_00150_cleaned.csv"

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

def clean_report(df: pd.DataFrame) -> pd.DataFrame:
    raw = df.fillna("").astype("string")

    # Metadata (optional)
    report_date = None
    year_context = None
    date_pat = re.compile(r"^\s*\d{1,2}-[A-Za-z]{3}-\d{2}\s*$")

    for val in raw.iloc[:, 0].astype(str).tolist():
        if date_pat.match(val):
            report_date = val.strip()
            break

    for row in raw.astype(str).itertuples(index=False):
        for cell in row:
            if "Year:" in cell:
                year_context = cell.strip()
                break
        if year_context:
            break

    def is_non_data_row(r):
        cells = [str(c).strip() for c in r]
        joined = " ".join([c for c in cells if c])
        if joined == "":
            return True
        if "Summary By Division" in joined:
            return True
        if joined.startswith("Year:"):
            return True
        if "Page" in joined and "of" in joined:
            return True
        if date_pat.match(cells[0]):
            return True
        if re.fullmatch(r"DELIVERY\s+TABLE\s+TAKE\s+AWAY\s+TOTAL", joined, flags=re.IGNORECASE):
            return True
        if re.fullmatch(r"DELIVERY\s+TABLE\s+TAKE\s+AWAY\s+TOTAL",
                        " ".join([cells[0], cells[1], cells[2], cells[3]]).strip(),
                        flags=re.IGNORECASE):
            return True
        return False

    keep = ~raw.apply(lambda row: is_non_data_row(list(row)), axis=1)
    data = raw.loc[keep].copy()

    records = []
    current_section = ""

    for _, r in data.iterrows():
        c0 = str(r.iloc[0]).strip()
        c1 = str(r.get("Unnamed: 1", "")).strip()
        c2 = str(r.get("Unnamed: 2", "")).strip()
        c3 = str(r.get("Unnamed: 3", "")).strip()
        c4 = str(r.get("Unnamed: 4", "")).strip()
        c5 = str(r.get("Unnamed: 5", "")).strip()
        c6 = str(r.get("Unnamed: 6", "")).strip()
        c7 = str(r.get("Unnamed: 7", "")).strip()

        if c0 and not is_numberish(c0) and c0.upper() not in {"DELIVERY", "TABLE", "TAKE AWAY", "TOTAL"}:
            current_section = c0

        item = c1 if c1 else c0
        if not item:
            continue

        # Two common layouts in these exported reports:
        # Layout A: numbers in columns 3/4/6/7  (DELIVERY, TABLE, TAKE AWAY, TOTAL)
        # Layout B: numbers shifted left to 2/3/4/5 (DELIVERY, TABLE, TAKE AWAY, TOTAL)
        prefer_a = is_numberish(c6) or is_numberish(c7)
        prefer_b = is_numberish(c2) or is_numberish(c3) or is_numberish(c4) or is_numberish(c5)

        if prefer_a:
            delivery = to_float(c3)
            table = to_float(c4)
            take_away = to_float(c6)
            total = to_float(c7)
        elif prefer_b and c1:
            delivery = to_float(c2)
            table = to_float(c3)
            take_away = to_float(c4)
            total = to_float(c5)
        else:
            continue

        records.append({
            "report_date": report_date,
            "context": year_context,
            "section": current_section if current_section else None,
            "item": item,
            "delivery": delivery,
            "table": table,
            "take_away": take_away,
            "total": total,
        })

    cleaned = pd.DataFrame.from_records(records)

    for col in ["report_date", "context", "section", "item"]:
        cleaned[col] = cleaned[col].astype("string").str.strip()
    cleaned["item"] = cleaned["item"].str.replace(r"\s+", " ", regex=True)

    cleaned = cleaned[cleaned["item"].notna() & (cleaned["item"].str.len() > 0)].drop_duplicates()
    cleaned = cleaned.sort_values(["section", "item"], kind="stable").reset_index(drop=True)

    return cleaned

if __name__ == "__main__":
    df = read_csv_robust(IN_PATH)
    cleaned = clean_report(df)
    cleaned.to_csv(OUT_PATH, index=False)
    print(f"Saved: {OUT_PATH}  rows={len(cleaned)}  cols={cleaned.shape[1]}")
