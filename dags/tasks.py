from datetime import datetime, timedelta

import pandas as pd

from aqi_config.settings import Settings
from src.cities import get_city_names, load_cities, load_regions
from src.extract.aqi_extractor import extract_backfill, extract_hourly
from src.load.csv import save_raw_backfill, save_raw_hourly
from src.load.postgres import PostgresLoader
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import build_fact_air_quality, rebuild_clean_from_raw, transform_hourly_aqi
from src.transform.transformer.dim_date import build_dim_date
from src.transform.transformer.dim_pollutant import build_dim_pollutant, build_dim_pollutant_category


def validate_settings(**context):
    Settings.validate()
    Settings.ensure_directories()
    return "settings_ok"


def extract_hourly_task(**context):
    for city in get_city_names():
        raw = extract_hourly(city)
        if not raw:
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        save_raw_hourly(df, city, Settings.RAW_DIR)
    return "extract_ok"


def rebuild_clean_task(**context):
    rebuild_clean_from_raw()
    return "rebuild_ok"


def extract_backfill_task(**context):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    for city in get_city_names():
        raw = extract_backfill(city, start_date, end_date)
        if not raw:
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        df["_dt"] = pd.to_datetime(df["datetime"])
        for (year, month), group in df.groupby([df["_dt"].dt.year, df["_dt"].dt.month]):
            save_raw_backfill(group, city, Settings.RAW_DIR, year, month)
    return "backfill_ok"


def load_to_warehouse(**context):
    dim_region = load_regions()
    dim_pollutant_category = build_dim_pollutant_category()
    dim_city = load_cities()
    dim_pollutant = build_dim_pollutant()
    clean_df = pd.read_csv(Settings.HOURLY_COMBINED_PATH)
    dim_date = build_dim_date(clean_df)
    fact_air_quality = build_fact_air_quality(clean_df, dim_city, dim_date, dim_pollutant)
    loader = PostgresLoader(Settings.get_database_url())
    loader.save_snowflake_schema(dim_region, dim_pollutant_category, dim_city, dim_pollutant, dim_date, fact_air_quality, Settings.POSTGRES_SCHEMA)
    return "load_ok"
