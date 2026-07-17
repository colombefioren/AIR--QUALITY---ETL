from config.logging import setup_logging
from config.settings import Settings
from src.extract.aqi_extractor import CITIES, extract_hourly
from src.load.csv import save_raw_hourly
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import rebuild_clean_from_raw, transform_hourly_aqi


def run_hourly_pipeline():
    setup_logging()
    Settings.validate()
    Settings.ensure_directories()

    for city in CITIES:
        raw = extract_hourly(city)
        if not raw:
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        save_raw_hourly(df, city, Settings.RAW_DIR)

    rebuild_clean_from_raw()
    print("Hourly pipeline complete.")


if __name__ == "__main__":
    run_hourly_pipeline()
