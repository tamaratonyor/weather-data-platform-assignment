"""
Parses ghcnd-stations.txt (fixed-width) into a clean CSV/Parquet that
DuckDB/dbt can ingest as a normal source.

Column positions below are the documented GHCN-Daily spec (see readme.txt
section III.1). VERIFY against your actual downloaded readme.txt before
trusting this blindly -- fixed-width specs are exactly the kind of thing
that drifts or has off-by-one surprises.

Documented (1-indexed, inclusive) layout:
  ID            1-11   Character
  LATITUDE     13-20   Real
  LONGITUDE    22-30   Real
  ELEVATION    32-37   Real
  STATE        39-40   Character
  NAME         42-71   Character
  GSN_FLAG     73-75   Character
  HCN_CRN_FLAG 77-79   Character
  WMO_ID       81-85   Character
"""
import csv
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
INPUT_FILE = RAW_DIR / "ghcnd-stations.txt"
OUTPUT_FILE = RAW_DIR / "stations_parsed.csv"

# (name, start_0idx, end_exclusive)
COLUMNS = [
    ("station_id", 0, 11),
    ("latitude", 12, 20),
    ("longitude", 21, 30),
    ("elevation", 31, 37),
    ("state", 38, 40),
    ("name", 41, 71),
    ("gsn_flag", 72, 75),
    ("hcn_crn_flag", 76, 79),
    ("wmo_id", 80, 85),
]


def parse_line(line: str) -> dict:
    row = {}
    for name, start, end in COLUMNS:
        value = line[start:end].strip() if len(line) >= start else ""
        row[name] = value
    return row


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} not found — run download_data.py first"
        )

    rows = []
    with open(INPUT_FILE, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(parse_line(line))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[c[0] for c in COLUMNS])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Parsed {len(rows)} stations -> {OUTPUT_FILE}")
    # quick sanity check on a target-ish row
    sample = [r for r in rows if r["state"] == "" and "CA" in r["station_id"]][:3]
    for s in sample[:3]:
        print("  sample:", s)


if __name__ == "__main__":
    main()
