import pandas as pd

from config.logging import setup_logging
from config.settings import Settings
from src.extract.aqi_extractor import CITIES, extract_hourly
from src.load.csv import save_processed_data, save_raw_hourly
from src.transform.quality.data_validator import DataValidator
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import transform_hourly_aqi


def run_hourly_pipeline():
    setup_logging()
    Settings.validate()
    Settings.ensure_directories()

    all_facts = []
    for city in CITIES:
        raw = extract_hourly(city)
        if not raw:
            continue
        df = transform_hourly_aqi(raw, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        DataValidator.validate(df, name=city)
        save_raw_hourly(df, city, Settings.RAW_DIR)
        all_facts.append(df)

    if all_facts:
        combined = pd.concat(all_facts, ignore_index=True)
        save_processed_data(combined, Settings.HOURLY_COMBINED_PATH)
        DataValidator.validate(combined, name="hourly_aqi_combined")

    print("Hourly pipeline complete.")


if __name__ == "__main__":
    run_hourly_pipeline()
