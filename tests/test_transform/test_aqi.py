import pandas as pd
import pytest

from src.transform.transformer.aqi import transform_hourly_aqi


def _sample_raw():
    return [{
        "main": {"aqi": 2},
        "components": {
            "co": 300, "no": 2, "no2": 10,
            "o3": 40, "so2": 3, "pm2_5": 15,
            "pm10": 25, "nh3": 5,
        },
        "dt": 1700000000,
    }]


def test_transform_returns_dataframe():
    result = transform_hourly_aqi(_sample_raw(), "Paris")
    assert isinstance(result, pd.DataFrame)


def test_transform_columns_present():
    result = transform_hourly_aqi(_sample_raw(), "Paris")
    expected = {"city_name", "timestamp", "date", "hour", "aqi",
                "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"}
    assert expected.issubset(set(result.columns))


def test_transform_dedup_same_hour():
    raw = _sample_raw() + _sample_raw()
    result = transform_hourly_aqi(raw, "Paris")
    assert len(result) == 1


def test_transform_aqi_range():
    result = transform_hourly_aqi(_sample_raw(), "Paris")
    assert 1 <= result["aqi"].iloc[0] <= 5
