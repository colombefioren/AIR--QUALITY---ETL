import logging
from datetime import datetime
import pandas as pd

from config.settings import Settings
from config.logging import setup_logging
from src.extract.city_extractor import CityExtractor
from src.extract.air_quality_extractor import AirQualityExtractor
from src.transform.quality.data_auditor import DataAuditor
from src.transform.quality.dataframe_cleaner import DataFrameCleaner
from src.transform.quality.data_validator import DataValidator
from src.transform.transformer.dim_date import DimDate
from src.transform.transformer.air_quality import AirQualityTransformer
from src.load.csv import CsvLoader
from src.load.postgres import PostgresLoader

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    logger.info("Air Quality ETL Pipeline starting...")

    try:
        Settings.validate()
        Settings.ensure_directories()

        city_extractor = CityExtractor(Settings.CITY_CSV_PATH)
        air_quality_extractor = AirQualityExtractor(
            api_key=Settings.VISUAL_CROSSING_API_KEY,
            base_url=Settings.VISUAL_CROSSING_BASE_URL,
        )
        data_auditor = DataAuditor()

        csv_loader = CsvLoader(
            raw_dirs={
                "historical": Settings.HISTORICAL_DIR,
                "forecast": Settings.FORECAST_DIR,
                "today_hourly": Settings.TODAY_HOURLY_DIR,
            },
            star_schema_dir=Settings.STAR_SCHEMA_DIR,
        )
        pg_loader = PostgresLoader(db_url=Settings.get_database_url())

        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("Starting Air Quality ETL Pipeline")
        logger.info("=" * 50)

        cities_df = city_extractor.extract()
        cities_df = DataFrameCleaner.normalize_empty_strings(cities_df)
        cities_df = DataFrameCleaner.drop_all_null_columns(cities_df)
        cities_df = DataFrameCleaner.dropna_rows(cities_df, how='all')
        data_auditor.audit_dataframe(cities_df, "City Data")

        historical_data = []
        forecast_data = []
        today_hourly_data = []

        for _, city in cities_df.iterrows():
            city_name = city["city_name"]

            logger.info(f"\n{'─'*40}")
            logger.info(f"Processing city: {city_name}")
            logger.info(f"{'─'*40}")

            try:
                logger.info(f"Extracting historical data for {city_name}...")
                historical_df = air_quality_extractor.extract_historical(city_name)
                if not historical_df.empty:
                    historical_data.append(historical_df)
                    csv_loader.save_raw_air_quality_data(historical_df, city_name, "historical")
                    logger.info(f"Historical data extracted: {len(historical_df)} records")
            except Exception as e:
                logger.error(f"Failed to extract historical data for {city_name}: {str(e)}")

            try:
                logger.info(f"Extracting forecast data for {city_name}...")
                forecast_df = air_quality_extractor.extract_forecast(city_name)
                if not forecast_df.empty:
                    forecast_data.append(forecast_df)
                    csv_loader.save_raw_air_quality_data(forecast_df, city_name, "forecast")
                    logger.info(f"Forecast data extracted: {len(forecast_df)} records")
            except Exception as e:
                logger.error(f"Failed to extract forecast data for {city_name}: {str(e)}")

            try:
                logger.info(f"Extracting hourly data for {city_name}...")
                hourly_df = air_quality_extractor.extract_today_hourly(city_name)
                if not hourly_df.empty:
                    today_hourly_data.append(hourly_df)
                    csv_loader.save_raw_air_quality_data(hourly_df, city_name, "today_hourly")
                    logger.info(f"Hourly data extracted: {len(hourly_df)} records")
            except Exception as e:
                logger.error(f"Failed to extract hourly data for {city_name}: {str(e)}")

        if not historical_data and not forecast_data and not today_hourly_data:
            logger.error("No air quality data extracted for any city")
            raise ValueError("Pipeline cannot continue without air quality data")

        logger.info("\nCleaning air quality data...")
        try:
            historical_data = [DataFrameCleaner.clean_air_quality_data(df) for df in historical_data]
            forecast_data = [DataFrameCleaner.clean_air_quality_data(df) for df in forecast_data]
            today_hourly_data = [DataFrameCleaner.clean_air_quality_data(df) for df in today_hourly_data]
        except Exception as e:
            logger.error(f"Failed to clean air quality data: {str(e)}")
            raise

        try:
            dim_date = DimDate.create()
            dim_city = cities_df.copy()
            data_auditor.audit_dataframe(dim_date, "Dim Date")
            data_auditor.audit_dataframe(dim_city, "Dim City")

            all_daily = pd.concat(historical_data + forecast_data, ignore_index=True)
            all_daily = all_daily.drop_duplicates(subset=["datetime", "city_name"])
            logger.info(f"Combined daily data: {len(all_daily)} records")
            csv_loader.save_processed_data(all_daily, Settings.DAILY_COMBINED_PATH)
        except Exception as e:
            logger.error(f"Failed to combine and save daily data: {str(e)}")
            raise

        try:
            fact_aqi = AirQualityTransformer.create_fact_aqi(all_daily, dim_city)
            data_auditor.audit_dataframe(fact_aqi, "Fact AQI")
            DataValidator.validate(fact_aqi, "Fact AQI")

            fact_aqi_today = AirQualityTransformer.create_fact_aqi_today(today_hourly_data, dim_city)
            data_auditor.audit_dataframe(fact_aqi_today, "Fact AQI Today")
            DataValidator.validate(fact_aqi_today, "Fact AQI Today")
        except Exception as e:
            logger.error(f"Failed to build star schema: {str(e)}")
            raise

        try:
            csv_loader.save_star_schema(dim_date, dim_city, fact_aqi, fact_aqi_today)
            pg_loader.save_star_schema(dim_date, dim_city, fact_aqi, fact_aqi_today, schema=Settings.POSTGRES_SCHEMA)
        except Exception as e:
            logger.error(f"Failed to load star schema to CSV or Postgres: {str(e)}")
            raise

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 50)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Status: SUCCESS")
        logger.info(f"Duration: {duration:.2f}s | Cities: {len(cities_df)}")
        logger.info(f"Historical: {sum(len(df) for df in historical_data)} | "
                    f"Forecast: {sum(len(df) for df in forecast_data)} | "
                    f"Hourly: {sum(len(df) for df in today_hourly_data)}")
        logger.info("=" * 50 + "\n")

        logger.info("Pipeline execution completed successfully")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
