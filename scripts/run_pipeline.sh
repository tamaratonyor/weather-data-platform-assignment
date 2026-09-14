#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== 1/6 downloading raw data =="
python ingestion/download_data.py

echo "== 2/6 parsing fixed-width metadata =="
python ingestion/parse_stations.py
python ingestion/parse_inventory.py

echo "== 3/6 loading raw schema into DuckDB =="
python ingestion/load_to_duckdb.py

echo "== 4/6 installing dbt packages =="
(cd dbt_project && dbt deps)

echo "== 5/6 running dbt (seed + build) =="
(cd dbt_project && dbt seed && dbt build)

echo "== 6/6 generating narratives =="
(cd narrative_pipeline && python generate_narratives.py)

echo "Pipeline complete. Query weather.duckdb to inspect results."
