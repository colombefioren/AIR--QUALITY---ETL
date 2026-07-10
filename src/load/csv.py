import logging
import pandas as pd

from src.transform.quality.data_validator import DataValidator

logger = logging.getLogger(__name__)


class CsvLoader:

    def __init__(self, raw_dirs, star_schema_dir):
        self.raw_dirs = raw_dirs
        self.star_schema_dir = star_schema_dir

    @staticmethod
    def _save(df, file_path, index=False):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=index)
        logger.info(f"Saved {len(df)} records to {file_path}")

    def save_raw_air_quality_data(self, df, city_name, data_type):
        if df.empty:
            logger.warning(f"No data to save for {city_name} ({data_type})")
            return

        directory = self.raw_dirs.get(data_type)
        if directory is None:
            raise ValueError(f"Unknown data type: {data_type}")

        file_path = directory / f"{city_name.lower()}_{data_type}.csv"

        if file_path.exists():
            existing = pd.read_csv(file_path)
            df = pd.concat([existing, df], ignore_index=True).drop_duplicates(subset=["datetime", "city_name"])

        DataValidator.validate(df, f"{city_name}_{data_type}")
        CsvLoader._save(df, file_path)

    def save_processed_data(self, df, file_path):
        DataValidator.validate(df, "processed_daily")
        CsvLoader._save(df, file_path)

    def save_star_schema(self, dim_date, dim_city, fact_air_quality, fact_air_quality_today):
        logger.info("Saving star schema tables to CSV")

        tables = {
            "dim_date": dim_date,
            "dim_city": dim_city,
            "fact_air_quality": fact_air_quality,
            "fact_air_quality_today": fact_air_quality_today,
        }

        for table_name, df in tables.items():
            if df.empty:
                logger.warning(f"Skipping empty table: {table_name}")
                continue
            DataValidator.validate(df, table_name)
            CsvLoader._save(df, self.star_schema_dir / f"{table_name}.csv")

        logger.info("Star schema CSV files saved successfully")
