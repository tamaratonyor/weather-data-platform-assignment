"""
Downloads GHCN-Daily raw files needed for the pipeline.

Station selection for *download* is still limited to the 5 target stations
(no point pulling every station on earth for a take-home), but note that
this is a network-efficiency decision, not a modeling decision — the dbt
layer does NOT hardcode these IDs; it resolves them from metadata via
seeds/target_cities.csv. If you add a 6th city, add its station ID here
too (this list stays admin-config, same spirit as the dbt seed).
"""
import gzip
import shutil
import urllib.request
from pathlib import Path

BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"

# Station IDs to fetch observation files for. This is download-scoping only.
TARGET_STATION_IDS = [
    "CA006158731",  # Toronto Pearson Intl A
    "CA007025251",  # Montreal Intl A (Trudeau)
    "CA001108395",  # Vancouver Intl A (YVR)
    "CA003031092",  # Calgary Intl A (YYC)
    "CA006106001",  # Ottawa Macdonald-Cartier Intl
]

REFERENCE_FILES = [
    "ghcnd-stations.txt",
    "ghcnd-inventory.txt",
    "ghcnd-countries.txt",
    "readme.txt",
]

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
BY_STATION_DIR = RAW_DIR / "by_station"


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"  skip (exists): {dest.name}")
        return
    print(f"  downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    BY_STATION_DIR.mkdir(parents=True, exist_ok=True)

    print("Reference files:")
    for fname in REFERENCE_FILES:
        download(f"{BASE_URL}/{fname}", RAW_DIR / fname)

    print("Station observation files:")
    for station_id in TARGET_STATION_IDS:
        fname = f"{station_id}.csv.gz"
        download(f"{BASE_URL}/by_station/{fname}", BY_STATION_DIR / fname)

    print("Done.")


if __name__ == "__main__":
    main()
