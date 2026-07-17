from config.settings import Settings
from src.extract.city_extractor import get_city_names
from src.extract.aqi_extractor import extract_hourly
from src.load.csv import save_raw_hourly
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.transformer.aqi import rebuild_clean_from_raw, transform_hourly_aqi


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


def load_to_warehouse(**context):
    return "load_ok"
