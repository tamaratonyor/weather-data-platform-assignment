"""
Loads raw + parsed files into DuckDB as the `raw` schema that dbt sources
point at. This is the boundary between "files on disk" and "the warehouse" —
everything after this is dbt's job.

Run order: download_data.py -> parse_stations.py -> parse_inventory.py -> this.
"""
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
BY_STATION_DIR = RAW_DIR / "by_station"
DB_PATH = os.environ.get("DUCKDB_PATH", str(ROOT / "weather.duckdb"))

OBSERVATION_COLUMNS = [
    "station_id",
    "date_raw",
    "element",
    "value",
    "mflag",
    "qflag",
    "sflag",
    "obs_time",
]


def main():
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # --- Daily observations: read every gzipped per-station CSV at once ---
    station_files = sorted(BY_STATION_DIR.glob("*.csv.gz"))
    if not station_files:
        raise FileNotFoundError(
            f"No station files found in {BY_STATION_DIR} — run download_data.py first"
        )
    glob_pattern = str(BY_STATION_DIR / "*.csv.gz")
    col_defs = ", ".join(f"'{c}': 'VARCHAR'" for c in OBSERVATION_COLUMNS)
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.observations AS
        SELECT *
        FROM read_csv(
            '{glob_pattern}',
            header = false,
            columns = {{{col_defs}}},
            filename = true
        );
    """)
    n_obs = con.execute("SELECT COUNT(*) FROM raw.observations").fetchone()[0]
    print(f"raw.observations: {n_obs} rows from {len(station_files)} station files")

    # --- Parsed reference files ---
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.stations AS
        SELECT * FROM read_csv_auto('{RAW_DIR / "stations_parsed.csv"}', header = true);
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.inventory AS
        SELECT * FROM read_csv_auto('{RAW_DIR / "inventory_parsed.csv"}', header = true);
    """)

    countries_file = RAW_DIR / "ghcnd-countries.txt"
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.countries AS
        SELECT
            trim(substr(line, 1, 2)) AS country_code,
            trim(substr(line, 4)) AS country_name
        FROM read_csv('{countries_file}', columns = {{'line': 'VARCHAR'}}, header = false, delim = E'\\x01');
    """)

    for tbl in ["stations", "inventory", "countries"]:
        n = con.execute(f"SELECT COUNT(*) FROM raw.{tbl}").fetchone()[0]
        print(f"raw.{tbl}: {n} rows")

    con.close()
    print(f"Loaded into {DB_PATH}")


if __name__ == "__main__":
    main()
