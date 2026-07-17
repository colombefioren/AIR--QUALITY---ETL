from pathlib import Path

import pandas as pd


def save_raw_hourly(df: pd.DataFrame, city_name: str, raw_dir: Path) -> Path:
    city_dir = raw_dir / "hourly"
    city_dir.mkdir(parents=True, exist_ok=True)
    path = city_dir / f"{city_name.lower().replace(' ', '_')}.csv"
    df.to_csv(path, index=False)
    return path


def save_processed_data(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
