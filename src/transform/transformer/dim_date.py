import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class DimDate:

    @staticmethod
    def create():
        now = datetime.now()
        year = now.year
        next_year = year + 1 if now.month == 12 else year
        start_date = f"{year}-01-01"
        end_date = f"{next_year}-12-31"
        logger.info(f"Creating date dimension from {year} to {next_year}")

        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        df = pd.DataFrame({
            "date_key": dates.strftime("%Y%m%d").astype(int),
            "full_date": dates,
            "year": dates.year,
            "month": dates.month,
            "day": dates.day,
            "day_of_week": dates.dayofweek,
            "quarter": dates.quarter,
        })

        logger.info(f"Created date dimension with {len(df)} records")
        return df
