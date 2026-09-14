"""
Generates daily weather narratives in bulk from fct_daily_weather using the
Gemini free tier, and writes results back into DuckDB as
marts.weather_narratives.

Usage:
    python generate_narratives.py [--limit N] [--dry-run]

Requires GEMINI_API_KEY in the environment (see .env.example).
"""
import argparse
import os
import time
from pathlib import Path

import duckdb
import google.generativeai as genai
from dotenv import load_dotenv

from prompts import SYSTEM_INSTRUCTION, build_prompt

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DB_PATH = os.environ.get("DUCKDB_PATH", str(ROOT / "weather.duckdb"))
MODEL_NAME = "gemini-1.5-flash"  # free-tier friendly
RATE_LIMIT_SLEEP_SECONDS = 4.5  # keep comfortably under free-tier RPM


def get_rows(con, limit=None):
    query = "select * from main_marts.fct_daily_weather order by city_name, obs_date"
    if limit:
        query += f" limit {limit}"
    return con.execute(query).fetch_df().to_dict(orient="records")


def ensure_output_table(con):
    con.execute("""
        CREATE SCHEMA IF NOT EXISTS main_marts;
        CREATE TABLE IF NOT EXISTS main_marts.weather_narratives (
            station_id VARCHAR,
            city_name VARCHAR,
            obs_date DATE,
            narrative VARCHAR,
            model VARCHAR,
            generated_at TIMESTAMP DEFAULT current_timestamp,
            PRIMARY KEY (station_id, obs_date)
        );
    """)


def already_generated(con) -> set:
    try:
        rows = con.execute(
            "select station_id, obs_date from main_marts.weather_narratives"
        ).fetchall()
        return {(r[0], str(r[1])) for r in rows}
    except duckdb.CatalogException:
        return set()


def generate_one(model, row: dict) -> str:
    prompt = build_prompt(row)
    response = model.generate_content(prompt)
    return response.text.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Cap rows processed (for testing)")
    parser.add_argument("--dry-run", action="store_true", help="Build prompts but don't call the API")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        raise RuntimeError("GEMINI_API_KEY not set. Copy .env.example to .env and fill it in.")

    con = duckdb.connect(DB_PATH)
    ensure_output_table(con)
    done = already_generated(con)

    rows = get_rows(con, args.limit)
    todo = [r for r in rows if (r["station_id"], str(r["obs_date"])) not in done]
    print(f"{len(rows)} total rows, {len(done)} already generated, {len(todo)} to process")

    if args.dry_run:
        for r in todo[:3]:
            print("---")
            print(build_prompt(r))
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)

    for i, row in enumerate(todo):
        try:
            narrative = generate_one(model, row)
        except Exception as e:
            print(f"  [{i}] FAILED {row['city_name']} {row['obs_date']}: {e}")
            time.sleep(RATE_LIMIT_SLEEP_SECONDS)
            continue

        con.execute(
            """
            INSERT INTO main_marts.weather_narratives
                (station_id, city_name, obs_date, narrative, model)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (station_id, obs_date) DO UPDATE SET
                narrative = excluded.narrative,
                model = excluded.model,
                generated_at = current_timestamp;
            """,
            [row["station_id"], row["city_name"], row["obs_date"], narrative, MODEL_NAME],
        )
        print(f"  [{i+1}/{len(todo)}] {row['city_name']} {row['obs_date']}: {narrative[:80]}...")
        time.sleep(RATE_LIMIT_SLEEP_SECONDS)

    con.close()
    print("Done.")


if __name__ == "__main__":
    main()
