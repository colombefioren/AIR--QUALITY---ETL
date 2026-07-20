from datetime import datetime
from pathlib import Path

import pandas as pd

from aqi_config.settings import Settings
from src.cities import get_city_coords
from src.transform.quality.data_validator import DataValidator


def transform_hourly_aqi(raw_list: list[dict], city_name: str) -> pd.DataFrame:
    coords = get_city_coords(city_name)
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


def _collect_all_csv() -> list[Path]:
    files = []
    for d in [Settings.RAW_BACKFILL_DIR, Settings.RAW_HOURLY_DIR]:
        files.extend(sorted(d.glob("*.csv")))
    return files


def rebuild_clean_from_raw(
    clean_path: Path = Settings.HOURLY_COMBINED_PATH,
) -> Path:
    csv_files = _collect_all_csv()
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


def build_fact_aqi(clean_df: pd.DataFrame, dim_city: pd.DataFrame, dim_date: pd.DataFrame) -> pd.DataFrame:
    city_key_map = dim_city.set_index("city_name")["city_key"].to_dict()
    date_key_map = {}
    for _, row in dim_date.iterrows():
        date_key_map[(str(row["full_date"]), int(row["hour"]))] = row["date_key"]

    df = clean_df.copy()
    df["city_key"] = df["city_name"].map(city_key_map)
    df["date_key"] = df.apply(
        lambda row: date_key_map.get((str(row["date"]), int(row["hour"])), None), axis=1
    )

    df = df.dropna(subset=["city_key", "date_key"])
    df["city_key"] = df["city_key"].astype(int)
    df["date_key"] = df["date_key"].astype(int)

    fact_cols = [
        "city_key", "date_key",
        "aqi", "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3",
    ]
    df = df[fact_cols]
    return df
