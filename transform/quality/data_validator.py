import logging

logger = logging.getLogger(__name__)


class DataValidator:

    RANGES = {
        "temp": (-50, 60),
        "tempmax": (-50, 60),
        "tempmin": (-50, 60),
        "feelslike": (-50, 60),
        "dew": (-50, 40),
        "humidity": (0, 100),
        "precip": (0, 500),
        "precipprob": (0, 100),
        "precipcover": (0, 100),
        "windgust": (0, 200),
        "windspeed": (0, 200),
        "winddir": (0, 360),
        "pressure": (800, 1100),
        "cloudcover": (0, 100),
        "visibility": (0, 50),
        "uvindex": (0, 20),
        "latitude": (-90, 90),
        "longitude": (-180, 180),
        "elevation_m": (-500, 9000),
    }

    @staticmethod
    def validate(df, name="DataFrame"):
        issues = 0

        for col, (lo, hi) in DataValidator.RANGES.items():
            if col not in df.columns:
                continue
            numeric = df[col].dropna()
            if numeric.empty:
                continue

            out = numeric[(numeric < lo) | (numeric > hi)]
            if not out.empty:
                logger.warning(f"{name}: {col} has {len(out)} values outside [{lo}, {hi}] "
                              f"(min={numeric.min():.2f}, max={numeric.max():.2f})")
                issues += 1

        if issues == 0:
            logger.info(f"{name}: all values within valid ranges")
        else:
            logger.warning(f"{name}: {issues} column(s) have out-of-range values")
