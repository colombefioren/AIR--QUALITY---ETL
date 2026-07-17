import logging
from pathlib import Path

import pandas as pd

from config.settings import Settings

logger = logging.getLogger(__name__)

CITIES = [
    {"city_name": "Paris",        "country": "France",     "latitude": 48.8566,  "longitude": 2.3522},
    {"city_name": "London",       "country": "UK",         "latitude": 51.5074,  "longitude": -0.1278},
    {"city_name": "New York",     "country": "USA",        "latitude": 40.7128,  "longitude": -74.0060},
    {"city_name": "Beijing",      "country": "China",      "latitude": 39.9042,  "longitude": 116.4074},
    {"city_name": "Mumbai",       "country": "India",      "latitude": 19.0760,  "longitude": 72.8777},
    {"city_name": "Antananarivo", "country": "Madagascar",  "latitude": -18.8792, "longitude": 47.5079},
]


def load_cities(csv_path: Path = Settings.CITY_CSV_PATH) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} cities from {csv_path}")
        return df

    df = pd.DataFrame(CITIES)
    df.insert(0, "city_key", range(1, len(df) + 1))
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
