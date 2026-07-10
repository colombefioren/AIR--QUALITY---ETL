import logging
import pandas as pd

logger = logging.getLogger(__name__)


def validate_settings():
    from config.settings import Settings
    from config.logging import setup_logging

    setup_logging()
    Settings.validate()
    Settings.ensure_directories()


def extract_historical(city_name):
    from config.settings import Settings
    from src.extract.weather_extractor import WeatherExtractor
    from src.load.csv import CsvLoader

    extractor = WeatherExtractor(
        api_key=Settings.VISUAL_CROSSING_API_KEY,
        base_url=Settings.VISUAL_CROSSING_BASE_URL,
    )
    df = extractor.extract_historical(city_name)
    if not df.empty:
        loader = CsvLoader(
            raw_dirs={
                "historical": Settings.HISTORICAL_DIR,
                "forecast": Settings.FORECAST_DIR,
                "today_hourly": Settings.TODAY_HOURLY_DIR,
            },
            star_schema_dir=Settings.STAR_SCHEMA_DIR,
        )
        loader.save_raw_air_quality_data(df, city_name, "historical")


def extract_forecast(city_name):
    from config.settings import Settings
    from src.extract.weather_extractor import WeatherExtractor
    from src.load.csv import CsvLoader

    extractor = WeatherExtractor(
        api_key=Settings.VISUAL_CROSSING_API_KEY,
        base_url=Settings.VISUAL_CROSSING_BASE_URL,
    )
    df = extractor.extract_forecast(city_name)
    if not df.empty:
        loader = CsvLoader(
            raw_dirs={
                "historical": Settings.HISTORICAL_DIR,
                "forecast": Settings.FORECAST_DIR,
                "today_hourly": Settings.TODAY_HOURLY_DIR,
            },
            star_schema_dir=Settings.STAR_SCHEMA_DIR,
        )
        loader.save_raw_air_quality_data(df, city_name, "forecast")


def extract_today_hourly(city_name):
    from config.settings import Settings
    from src.extract.weather_extractor import WeatherExtractor
    from src.load.csv import CsvLoader

    extractor = WeatherExtractor(
        api_key=Settings.VISUAL_CROSSING_API_KEY,
        base_url=Settings.VISUAL_CROSSING_BASE_URL,
    )
    df = extractor.extract_today_hourly(city_name)
    if not df.empty:
        loader = CsvLoader(
            raw_dirs={
                "historical": Settings.HISTORICAL_DIR,
                "forecast": Settings.FORECAST_DIR,
                "today_hourly": Settings.TODAY_HOURLY_DIR,
            },
            star_schema_dir=Settings.STAR_SCHEMA_DIR,
        )
        loader.save_raw_air_quality_data(df, city_name, "today_hourly")


def prepare_dimensions():
    from config.settings import Settings
    from src.extract.city_extractor import CityExtractor
    from src.transform.quality.dataframe_cleaner import DataFrameCleaner
    from src.transform.transformer.dim_date import DimDate

    cities_df = CityExtractor(Settings.CITY_CSV_PATH).extract()
    dim_city = DataFrameCleaner.normalize_empty_strings(cities_df.copy())
    dim_city = DataFrameCleaner.drop_all_null_columns(dim_city)
    dim_city = DataFrameCleaner.dropna_rows(dim_city, how="all")
    dim_date = DimDate.create()
    dim_date.to_csv(Settings.DATE_CSV_PATH, index=False)
    logger.info(f"Saved dim_date ({len(dim_date)} records)")


def transform_facts():
    from config.settings import Settings
    from src.transform.quality.dataframe_cleaner import DataFrameCleaner
    from src.transform.quality.data_validator import DataValidator
    from src.transform.transformer.air_quality import AirQualityTransformer
    from src.load.csv import CsvLoader

    dim_city = pd.read_csv(Settings.CITY_CSV_PATH)

    raw_historical = [pd.read_csv(p) for p in sorted(Settings.HISTORICAL_DIR.glob("*.csv"))]
    raw_forecast = [pd.read_csv(p) for p in sorted(Settings.FORECAST_DIR.glob("*.csv"))]
    raw_hourly = [pd.read_csv(p) for p in sorted(Settings.TODAY_HOURLY_DIR.glob("*.csv"))]

    historical_clean = [DataFrameCleaner.clean_air_quality_data(df) for df in raw_historical]
    forecast_clean = [DataFrameCleaner.clean_air_quality_data(df) for df in raw_forecast]
    hourly_clean = [DataFrameCleaner.clean_air_quality_data(df) for df in raw_hourly]

    all_daily = pd.concat(historical_clean + forecast_clean, ignore_index=True)
    all_daily = all_daily.drop_duplicates(subset=["datetime", "city_name"])
    csv_loader = CsvLoader(
        raw_dirs={
            "historical": Settings.HISTORICAL_DIR,
            "forecast": Settings.FORECAST_DIR,
            "today_hourly": Settings.TODAY_HOURLY_DIR,
        },
        star_schema_dir=Settings.STAR_SCHEMA_DIR,
    )
    csv_loader.save_processed_data(all_daily, Settings.DAILY_COMBINED_PATH)
    logger.info(f"Combined daily data: {len(all_daily)} records")

    fact_air_quality = AirQualityTransformer.create_fact_air_quality(all_daily, dim_city)
    DataValidator.validate(fact_air_quality, "Fact Air Quality")

    fact_air_quality_today = AirQualityTransformer.create_fact_air_quality_today(hourly_clean, dim_city)
    DataValidator.validate(fact_air_quality_today, "Fact Air Quality Today")

    dim_date = pd.read_csv(Settings.DATE_CSV_PATH)
    csv_loader.save_star_schema(dim_date, dim_city, fact_air_quality, fact_air_quality_today)
    logger.info(f"Saved fact_air_quality ({len(fact_air_quality)} records) and "
                f"fact_air_quality_today ({len(fact_air_quality_today)} records)")


def save_postgres():
    from config.settings import Settings
    from src.load.postgres import PostgresLoader
    from src.transform.quality.data_validator import DataValidator

    pg_loader = PostgresLoader(db_url=Settings.get_database_url())

    tables = {
        "dim_date": Settings.DATE_CSV_PATH,
        "dim_city": Settings.CITY_CSV_PATH,
        "fact_air_quality": Settings.AIR_QUALITY_FACT_PATH,
        "fact_air_quality_today": Settings.AIR_QUALITY_TODAY_FACT_PATH,
    }

    for table_name, csv_path in tables.items():
        if not csv_path.exists():
            logger.warning(f"Skipping {table_name}: {csv_path} not found")
            continue
        df = pd.read_csv(csv_path)
        DataValidator.validate(df, table_name)
        pg_loader.save(df=df, table_name=table_name, schema=Settings.POSTGRES_SCHEMA)

    logger.info("Star schema loaded to Postgres")
