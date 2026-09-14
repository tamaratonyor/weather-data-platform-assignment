"""
Parses ghcnd-inventory.txt (fixed-width) -> CSV.

This file is what drives DYNAMIC element selection: for each station it
tells us which elements (TMAX, PRCP, etc.) are reported and over what year
range. The dbt intermediate layer joins against this instead of assuming
a hardcoded list of elements.

Documented (1-indexed, inclusive) layout:
  ID          1-11   Character
  LATITUDE   13-20   Real
  LONGITUDE  22-30   Real
  ELEMENT    32-35   Character
  FIRSTYEAR  37-40   Integer
  LASTYEAR   42-45   Integer

VERIFY against your downloaded readme.txt.
"""
import csv
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
INPUT_FILE = RAW_DIR / "ghcnd-inventory.txt"
OUTPUT_FILE = RAW_DIR / "inventory_parsed.csv"

COLUMNS = [
    ("station_id", 0, 11),
    ("latitude", 12, 20),
    ("longitude", 21, 30),
    ("element", 31, 35),
    ("first_year", 36, 40),
    ("last_year", 41, 45),
]


def parse_line(line: str) -> dict:
    return {name: line[start:end].strip() for name, start, end in COLUMNS}


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

    print(f"Parsed {len(rows)} inventory rows -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
