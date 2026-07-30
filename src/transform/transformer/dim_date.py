import logging
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

from aqi_config.settings import Settings

logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_dim_date(
    source_df: pd.DataFrame,
    csv_path: Path = Settings.DATE_CSV_PATH,
) -> pd.DataFrame:
    if "datetime" not in source_df.columns:
        logger.warning("No 'datetime' column found — building dim_date from date/hour cols")
        source_df = source_df.copy()
        source_df["datetime"] = pd.to_datetime(source_df["date"]) + pd.to_timedelta(source_df["hour"], unit="h")

    dt_series = pd.to_datetime(source_df["datetime"], utc=True).dt.tz_convert(timezone(timedelta(hours=3))).dt.floor("h").drop_duplicates().sort_values().reset_index(drop=True)

    rows = []
    for dt in dt_series:
        date_key = int(dt.strftime("%Y%m%d%H"))
        rows.append({
            "date_key": date_key,
            "full_date": dt.date(),
            "hour": dt.hour,
            "day_of_week": DAY_NAMES[dt.weekday()],
            "is_weekend": dt.weekday() >= 5,
            "month": dt.month,
            "year": dt.year,
        })

    df = pd.DataFrame(rows)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info(f"Built dim_date with {len(df)} rows → {csv_path}")
    return df
