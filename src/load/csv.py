from pathlib import Path

import pandas as pd


def save_raw_hourly(df: pd.DataFrame, city_name: str, raw_dir: Path) -> Path:
    city_dir = raw_dir / "hourly"
    city_dir.mkdir(parents=True, exist_ok=True)
    date_str = df["date"].iloc[0]
    hour_str = f"{df['hour'].iloc[0]:02d}"
    slug = city_name.lower().replace(" ", "_")
    path = city_dir / f"{slug}_{date_str}_{hour_str}.csv"
    df.to_csv(path, index=False)
    return path


def save_raw_backfill(df: pd.DataFrame, city_name: str, raw_dir: Path, year: int, month: int) -> Path:
    backfill_dir = raw_dir / "backfill"
    backfill_dir.mkdir(parents=True, exist_ok=True)
    slug = city_name.lower().replace(" ", "_")
    path = backfill_dir / f"{slug}_{year}-{month:02d}.csv"
    df.to_csv(path, index=False)
    return path


def save_processed_data(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path
