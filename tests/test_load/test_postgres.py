from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.load.postgres import PostgresLoader


def _sample_dim_region():
    return pd.DataFrame({
        "region_id": [1, 2],
        "region_name": ["Analamanga", "Atsinanana"],
    })


def _sample_dim_pollutant_category():
    return pd.DataFrame({
        "category_id": [1, 2],
        "category_name": ["Gas", "Particulate"],
    })


def _sample_dim_city():
    return pd.DataFrame({
        "city_key": [1, 2],
        "city_name": ["Antananarivo", "Toamasina"],
        "country": ["Madagascar", "Madagascar"],
        "latitude": [-18.8792, -18.1443],
        "longitude": [47.5079, 49.3958],
        "region_id": [1, 2],
    })


def _sample_dim_pollutant():
    return pd.DataFrame({
        "pollutant_id": [1, 2, 3],
        "code": ["co", "no2", "pm2_5"],
        "name": ["Carbon Monoxide", "Nitrogen Dioxide", "Fine Particulate Matter"],
        "unit": ["μg/m³", "μg/m³", "μg/m³"],
        "category_id": [1, 1, 2],
        "who_threshold": [4000.0, 25.0, 15.0],
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


def _sample_fact():
    return pd.DataFrame({
        "city_key": [1, 1, 2],
        "date_key": [2026071710, 2026071710, 2026071710],
        "pollutant_id": [1, 2, 1],
        "value": [200.0, 5.0, 300.0],
        "aqi": [2, 2, 3],
    })


@patch("src.load.postgres.create_engine")
def test_postgres_loader_init(mock_engine):
    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    assert loader.db_url == "postgresql://user:pass@localhost/test"
    assert loader.engine is None


@patch("src.load.postgres.create_engine")
def test_save_snowflake_schema_calls_insert(mock_engine):
    mock_conn = MagicMock()
    mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_engine.return_value.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.return_value.begin.return_value.__exit__ = MagicMock(return_value=False)

    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    loader.engine = mock_engine.return_value

    with patch.object(loader, "_ensure_tables"), \
         patch.object(loader, "_insert_with_conflict") as mock_insert, \
         patch.object(loader, "_ensure_foreign_keys"):
        loader.save_snowflake_schema(
            _sample_dim_region(),
            _sample_dim_pollutant_category(),
            _sample_dim_city(),
            _sample_dim_pollutant(),
            _sample_dim_date(),
            _sample_fact(),
            "public",
        )
        assert mock_insert.call_count == 6


def test_save_snowflake_schema_skips_empty():
    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    loader.engine = MagicMock()

    with patch.object(loader, "_ensure_tables"), \
         patch.object(loader, "_insert_with_conflict") as mock_insert, \
         patch.object(loader, "_ensure_foreign_keys"), \
         patch.object(loader, "_get_engine"):
        empty_df = pd.DataFrame()
        loader.save_snowflake_schema(
            _sample_dim_region(),
            _sample_dim_pollutant_category(),
            empty_df,
            _sample_dim_pollutant(),
            _sample_dim_date(),
            _sample_fact(),
            "public",
        )
        assert mock_insert.call_count == 5
