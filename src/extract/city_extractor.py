from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class CityExtractor:

    def __init__(self, csv_path):
        self.csv_path = csv_path
        logger.info(f"CityExtractor initialized with path: {self.csv_path}")

    def extract(self):
        logger.info(f"Extracting city data from: {self.csv_path}")

        if not self.csv_path.exists():
            logger.error(f"City CSV file not found: {self.csv_path}")
            raise FileNotFoundError(f"{self.csv_path} not found")

        try:
            df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(df)} cities from CSV")
            logger.debug(f"Columns found: {list(df.columns)}")
            logger.debug(f"DataFrame shape: {df.shape}")
            logger.info("City data extraction completed successfully")
            return df

        except Exception as e:
            logger.error(f"Error extracting city data: {str(e)}")
            raise
