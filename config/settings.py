import os
from pathlib import Path
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:

    VISUAL_CROSSING_API_KEY = os.getenv("VISUAL_CROSSING_API_KEY")
    VISUAL_CROSSING_BASE_URL = "https://air_quality.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA", "public")

    DATA_DIR = Path("data")
    RAW_DIR = DATA_DIR / "raw"
    CLEAN_DIR = DATA_DIR / "clean"
    STAR_SCHEMA_DIR = DATA_DIR / "star_schema"

    HISTORICAL_DIR = RAW_DIR / "historical"
    FORECAST_DIR = RAW_DIR / "forecast"
    TODAY_HOURLY_DIR = RAW_DIR / "today_hourly"

    DAILY_COMBINED_PATH = CLEAN_DIR / "daily_air_quality_combined.csv"

    CITY_CSV_PATH = STAR_SCHEMA_DIR / "dim_city.csv"
    DATE_CSV_PATH = STAR_SCHEMA_DIR / "dim_date.csv"
    AIR_QUALITY_FACT_PATH = STAR_SCHEMA_DIR / "fact_air_quality.csv"
    AIR_QUALITY_TODAY_FACT_PATH = STAR_SCHEMA_DIR / "fact_air_quality_today.csv"

    @classmethod
    def get_database_url(cls):
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )

    @classmethod
    def validate(cls):
        if not cls.VISUAL_CROSSING_API_KEY:
            error_msg = "VISUAL_CROSSING_API_KEY is not set in environment variables"
            logger.error(error_msg)
            raise ValueError(error_msg)
        pg_vars = {
            "POSTGRES_PORT": cls.POSTGRES_PORT,
            "POSTGRES_DB": cls.POSTGRES_DB,
            "POSTGRES_USER": cls.POSTGRES_USER,
            "POSTGRES_PASSWORD": cls.POSTGRES_PASSWORD,
        }
        missing = [k for k, v in pg_vars.items() if not v]
        if missing:
            error_msg = f"Missing Postgres env vars: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("Configuration validated successfully")

    @classmethod
    def ensure_directories(cls):
        directories = [
            cls.DATA_DIR,
            cls.RAW_DIR,
            cls.CLEAN_DIR,
            cls.STAR_SCHEMA_DIR,
            cls.HISTORICAL_DIR,
            cls.FORECAST_DIR,
            cls.TODAY_HOURLY_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
        logger.info("All directories ensured")
