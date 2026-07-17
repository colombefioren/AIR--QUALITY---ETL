import pandas as pd

from config.settings import Settings
from src.extract.aqi_extractor import CITIES, extract_hourly
from src.load.csv import save_processed_data, save_raw_hourly
from src.transform.quality.data_validator import DataValidator
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import transform_hourly_aqi


def validate_settings(**context):
    Settings.validate()
    Settings.ensure_directories()
    return "settings_ok"


def extract_hourly_task(**context):
    results = {}
    for city in CITIES:
        raw = extract_hourly(city)
        results[city] = raw
    context["ti"].xcom_push(key="hourly_raw", value=str(results))
    return list(results.keys())


def clean_and_transform_task(**context):
    raw_str = context["ti"].xcom_pull(key="hourly_raw")
    raw_dict = eval(raw_str)
    dfs = []
    for city, raw_list in raw_dict.items():
        if not raw_list:
            continue
        df = transform_hourly_aqi(raw_list, city)
        df = DataFrameCleaner.clean_aqi_data(df)
        DataValidator.validate(df, name=city)
        save_raw_hourly(df, city, Settings.RAW_DIR)
        dfs.append(df)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        save_processed_data(combined, Settings.HOURLY_COMBINED_PATH)
        DataValidator.validate(combined, name="hourly_aqi_combined")
    return "transform_ok"


def load_to_warehouse(**context):
    return "load_ok"
