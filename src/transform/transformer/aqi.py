from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import Settings
from src.extract.aqi_extractor import CITIES
from src.transform.quality.data_validator import DataValidator


def transform_hourly_aqi(raw_list: list[dict], city_name: str) -> pd.DataFrame:
    coords = CITIES[city_name]
    rows = []
    for entry in raw_list:
        dt = datetime.fromtimestamp(entry["dt"])
        rows.append({
            "city_name": city_name,
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "datetime": dt,
            "date": dt.date(),
            "hour": dt.hour,
            "aqi": entry["main"]["aqi"],
            "co": entry["components"]["co"],
            "no": entry["components"]["no"],
            "no2": entry["components"]["no2"],
            "o3": entry["components"]["o3"],
            "so2": entry["components"]["so2"],
            "pm2_5": entry["components"]["pm2_5"],
            "pm10": entry["components"]["pm10"],
            "nh3": entry["components"]["nh3"],
        })
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["city_name", "date", "hour"], keep="last")
    return df


def rebuild_clean_from_raw(
    raw_dir: Path = Settings.RAW_HOURLY_DIR,
    clean_path: Path = Settings.HOURLY_COMBINED_PATH,
) -> Path:
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        return clean_path

    dfs = [pd.read_csv(f) for f in csv_files]
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["city_name", "date", "hour"], keep="last")
    combined = combined.sort_values(["datetime", "city_name"]).reset_index(drop=True)

    clean_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(clean_path, index=False)

    DataValidator.validate(combined, name="hourly_aqi_combined")
    return clean_path
