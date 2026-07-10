import logging

logger = logging.getLogger(__name__)


class DataValidator:

    RANGES = {
        "pm2.5": (0, 500),
        "pm10": (0, 500),
        "no2": (0, 1000),
        "o3": (0, 500),
        "co": (0, 50000),
        "so2": (0, 1000),
        "aqi": (0, 500),
        "us-epa-index": (0, 6),
        "gb-defra-index": (0, 10),
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
