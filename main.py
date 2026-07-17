from datetime import datetime, timedelta

import pandas as pd

from config.logging import setup_logging
from config.settings import Settings
from src.cities import get_city_names, load_cities
from src.extract.aqi_extractor import extract_backfill, extract_hourly
from src.load.csv import save_raw_backfill, save_raw_hourly
from src.load.postgres import PostgresLoader
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import (
    build_fact_aqi,
    rebuild_clean_from_raw,
    transform_hourly_aqi,
)
from src.transform.transformer.dim_date import build_dim_date


def _save_star_schema():
    dim_city = load_cities()
    clean_df = pd.read_csv(Settings.HOURLY_COMBINED_PATH)
    dim_date = build_dim_date(clean_df)
    fact_aqi = build_fact_aqi(clean_df, dim_city, dim_date)
    loader = PostgresLoader(Settings.get_database_url())
    loader.save_star_schema(dim_city, dim_date, fact_aqi, Settings.POSTGRES_SCHEMA)


def run_backfill(months: int = 12):
    import logging

    logger = logging.getLogger(__name__)

    setup_logging()
    Settings.validate()
    Settings.ensure_directories()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)

    cities = get_city_names()
    for i, city in enumerate(cities, 1):
        logger.info(f"[{i}/{len(cities)}] Backfilling {city}...")
        raw = extract_backfill(city, start_date, end_date)
        if not raw:
            logger.warning(f"[{i}/{len(cities)}] {city}: no data, skipping")
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        df["_dt"] = pd.to_datetime(df["datetime"])
        month_groups = list(df.groupby([df["_dt"].dt.year, df["_dt"].dt.month]))
        logger.info(f"[{i}/{len(cities)}] {city}: {len(month_groups)} months to save")
        for (year, month), group in month_groups:
            save_raw_backfill(group, city, Settings.RAW_DIR, year, month)
        logger.info(f"[{i}/{len(cities)}] {city}: done")

    rebuild_clean_from_raw()
    _save_star_schema()
    logger.info(f"Backfill complete ({months} months).")


def run_hourly_pipeline():
    setup_logging()
    Settings.validate()
    Settings.ensure_directories()

    for city in get_city_names():
        raw = extract_hourly(city)
        if not raw:
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        save_raw_hourly(df, city, Settings.RAW_DIR)

    rebuild_clean_from_raw()
    _save_star_schema()
    print("Pipeline complete — star schema loaded to Postgres.")


if __name__ == "__main__":
    run_hourly_pipeline()
