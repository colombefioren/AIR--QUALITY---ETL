import pandas as pd

from config.logging import setup_logging
from config.settings import Settings
from src.extract.city_extractor import get_city_names, load_cities
from src.extract.aqi_extractor import extract_hourly
from src.load.csv import save_raw_hourly
from src.load.postgres import PostgresLoader
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import build_fact_aqi, rebuild_clean_from_raw, transform_hourly_aqi
from src.transform.transformer.dim_date import build_dim_date


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

    dim_city = load_cities()
    clean_df = pd.read_csv(Settings.HOURLY_COMBINED_PATH)
    dim_date = build_dim_date(clean_df)
    fact_aqi = build_fact_aqi(clean_df, dim_city, dim_date)
    fact_aqi.to_csv(Settings.FACT_AQI_PATH, index=False)

    loader = PostgresLoader(Settings.get_database_url())
    loader.save_star_schema(dim_city, dim_date, fact_aqi, Settings.POSTGRES_SCHEMA)
    print("Pipeline complete — star schema loaded to Postgres.")


if __name__ == "__main__":
    run_hourly_pipeline()
