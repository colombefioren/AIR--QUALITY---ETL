import logging
from pathlib import Path

import pandas as pd

from aqi_config.settings import Settings

logger = logging.getLogger(__name__)

CITIES = [
    {"city_name": "Antananarivo", "country": "Madagascar", "latitude": -18.8792, "longitude": 47.5079, "region": "Analamanga"},
    {"city_name": "Toamasina",    "country": "Madagascar", "latitude": -18.1443, "longitude": 49.3958, "region": "Atsinanana"},
    {"city_name": "Mahajanga",    "country": "Madagascar", "latitude": -15.7167, "longitude": 46.3167, "region": "Boeny"},
    {"city_name": "Fianarantsoa", "country": "Madagascar", "latitude": -21.4333, "longitude": 47.0833, "region": "Haute Matsiatra"},
    {"city_name": "Toliara",      "country": "Madagascar", "latitude": -23.3500, "longitude": 43.6667, "region": "Atsimo-Andrefana"},
    {"city_name": "Antsiranana",  "country": "Madagascar", "latitude": -12.2667, "longitude": 49.2833, "region": "Diana"},
]

REGIONS = sorted({c["region"] for c in CITIES})


def load_regions(csv_path: Path = Settings.REGION_CSV_PATH) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} regions from {csv_path}")
        return df
    rows = [{"region_id": i + 1, "region_name": r} for i, r in enumerate(REGIONS)]
    df = pd.DataFrame(rows)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Created {csv_path} with {len(df)} regions")
    return df


def load_cities(csv_path: Path = Settings.CITY_CSV_PATH) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} cities from {csv_path}")
        return df

    region_df = load_regions()
    region_map = region_df.set_index("region_name")["region_id"].to_dict()

    rows = []
    for i, city in enumerate(CITIES, 1):
        rows.append({
            "city_key": i,
            "city_name": city["city_name"],
            "country": city["country"],
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "region_id": region_map[city["region"]],
        })
    df = pd.DataFrame(rows)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Created {csv_path} with {len(df)} cities")
    return df


def get_city_coords(city_name: str) -> dict | None:
    for city in CITIES:
        if city["city_name"] == city_name:
            return {"lat": city["latitude"], "lon": city["longitude"]}
    return None


def get_city_names() -> list[str]:
    return [c["city_name"] for c in CITIES]
