import logging
from pathlib import Path

import pandas as pd

from aqi_config.settings import Settings

logger = logging.getLogger(__name__)

POLLUTANT_CATEGORIES = [
    {"category_id": 1, "category_name": "Gas"},
    {"category_id": 2, "category_name": "Particulate"},
]

POLLUTANTS = [
    {"pollutant_id": 1, "code": "co",    "name": "Carbon Monoxide",       "unit": "μg/m³", "category_id": 1, "who_threshold": 4000.0},
    {"pollutant_id": 2, "code": "no",    "name": "Nitrogen Monoxide",     "unit": "μg/m³", "category_id": 1, "who_threshold": None},
    {"pollutant_id": 3, "code": "no2",   "name": "Nitrogen Dioxide",      "unit": "μg/m³", "category_id": 1, "who_threshold": 25.0},
    {"pollutant_id": 4, "code": "o3",    "name": "Ozone",                 "unit": "μg/m³", "category_id": 1, "who_threshold": 100.0},
    {"pollutant_id": 5, "code": "so2",   "name": "Sulphur Dioxide",       "unit": "μg/m³", "category_id": 1, "who_threshold": 40.0},
    {"pollutant_id": 6, "code": "pm2_5", "name": "Fine Particulate Matter", "unit": "μg/m³", "category_id": 2, "who_threshold": 15.0},
    {"pollutant_id": 7, "code": "pm10",  "name": "Particulate Matter",    "unit": "μg/m³", "category_id": 2, "who_threshold": 45.0},
    {"pollutant_id": 8, "code": "nh3",   "name": "Ammonia",               "unit": "μg/m³", "category_id": 1, "who_threshold": None},
]

POLLUTANT_CODE_TO_ID = {p["code"]: p["pollutant_id"] for p in POLLUTANTS}


def build_dim_pollutant_category(csv_path: Path = Settings.POLLUTANT_CATEGORY_CSV_PATH) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} pollutant categories from {csv_path}")
        return df
    df = pd.DataFrame(POLLUTANT_CATEGORIES)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Created {csv_path} with {len(df)} pollutant categories")
    return df


def build_dim_pollutant(csv_path: Path = Settings.POLLUTANT_CSV_PATH) -> pd.DataFrame:
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} pollutants from {csv_path}")
        return df
    df = pd.DataFrame(POLLUTANTS)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Created {csv_path} with {len(df)} pollutants")
    return df
