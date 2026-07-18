import pandas as pd
import pytest

from src.transform.transformer.aqi import build_fact_air_quality, transform_hourly_aqi


def _sample_raw():
    return [
        {
            "main": {"aqi": 2},
            "components": {
                "co": 300,
                "no": 2,
                "no2": 10,
                "o3": 40,
                "so2": 3,
                "pm2_5": 15,
                "pm10": 25,
                "nh3": 5,
            },
            "dt": 1784271600,
        }
    ]


def test_transform_returns_dataframe():
    result = transform_hourly_aqi(_sample_raw(), "Antananarivo")
    assert isinstance(result, pd.DataFrame)


def test_transform_columns_present():
    result = transform_hourly_aqi(_sample_raw(), "Antananarivo")
    expected = {
        "city_name",
        "latitude",
        "longitude",
        "datetime",
        "date",
        "hour",
        "aqi",
        "co",
        "no",
        "no2",
        "o3",
        "so2",
        "pm2_5",
        "pm10",
        "nh3",
    }
    assert expected.issubset(set(result.columns))


def test_transform_dedup_same_hour():
    raw = _sample_raw() + _sample_raw()
    result = transform_hourly_aqi(raw, "Antananarivo")
    assert len(result) == 1


def test_transform_aqi_range():
    result = transform_hourly_aqi(_sample_raw(), "Antananarivo")
    assert 1 <= result["aqi"].iloc[0] <= 5


def _sample_dim_city():
    return pd.DataFrame({
        "city_key": [1, 2],
        "city_name": ["Antananarivo", "Toamasina"],
        "country": ["Madagascar", "Madagascar"],
        "latitude": [-18.8792, -18.1443],
        "longitude": [47.5079, 49.3958],
        "region_id": [1, 2],
    })


def _sample_dim_date():
    return pd.DataFrame({
        "date_key": [2026071710, 2026071711],
        "full_date": ["2026-07-17", "2026-07-17"],
        "hour": [10, 11],
        "day_of_week": ["Thursday", "Thursday"],
        "is_weekend": [False, False],
        "month": [7, 7],
        "year": [2026, 2026],
        "season": ["dry", "dry"],
    })


def _sample_dim_pollutant():
    return pd.DataFrame({
        "pollutant_id": [1, 2],
        "code": ["co", "no2"],
        "name": ["Carbon Monoxide", "Nitrogen Dioxide"],
        "unit": ["μg/m³", "μg/m³"],
        "category_id": [1, 1],
        "who_threshold": [4000.0, 25.0],
    })


def test_build_fact_air_quality_returns_long_format():
    raw = _sample_raw()
    df = transform_hourly_aqi(raw, "Antananarivo")
    dim_city = _sample_dim_city()
    dim_pollutant = _sample_dim_pollutant()

    date_rows = []
    for _, row in df.iterrows():
        date_key = int(pd.Timestamp(row["datetime"]).strftime("%Y%m%d%H"))
        date_rows.append({
            "date_key": date_key,
            "full_date": str(row["date"]),
            "hour": int(row["hour"]),
            "day_of_week": "Monday",
            "is_weekend": False,
            "month": int(pd.Timestamp(row["datetime"]).month),
            "year": int(pd.Timestamp(row["datetime"]).year),
            "season": "dry",
        })
    dim_date = pd.DataFrame(date_rows).drop_duplicates(subset=["date_key"])

    fact = build_fact_air_quality(df, dim_city, dim_date, dim_pollutant)
    assert isinstance(fact, pd.DataFrame)
    assert "city_key" in fact.columns
    assert "date_key" in fact.columns
    assert "pollutant_id" in fact.columns
    assert "value" in fact.columns
    assert "aqi" in fact.columns
    assert len(fact) >= 1
    assert "co" not in fact.columns
