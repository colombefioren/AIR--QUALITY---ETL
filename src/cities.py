import logging
from pathlib import Path

import pandas as pd

from config.settings import Settings

logger = logging.getLogger(__name__)

CITIES = [
    {"city_name": "Antananarivo", "country": "Madagascar", "latitude": -18.8792, "longitude": 47.5079},
    {"city_name": "Toamasina",    "country": "Madagascar", "latitude": -18.1443, "longitude": 49.3958},
    {"city_name": "Mahajanga",    "country": "Madagascar", "latitude": -15.7167, "longitude": 46.3167},
    {"city_name": "Fianarantsoa", "country": "Madagascar", "latitude": -21.4333, "longitude": 47.0833},
    {"city_name": "Toliara",      "country": "Madagascar", "latitude": -23.3500, "longitude": 43.6667},
    {"city_name": "Antsiranana",  "country": "Madagascar", "latitude": -12.2667, "longitude": 49.2833},
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
