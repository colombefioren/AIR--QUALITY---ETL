from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.load.postgres import PostgresLoader


def _sample_dim_city():
    return pd.DataFrame({
        "city_key": [1, 2],
        "city_name": ["Paris", "London"],
        "country": ["France", "UK"],
        "latitude": [48.8566, 51.5074],
        "longitude": [2.3522, -0.1278],
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
    })


def _sample_fact_aqi():
    return pd.DataFrame({
        "city_key": [1, 2],
        "date_key": [2026071710, 2026071710],
        "aqi": [2, 3],
        "co": [200.0, 300.0],
        "no": [1.0, 2.0],
        "no2": [5.0, 10.0],
        "o3": [30.0, 40.0],
        "so2": [2.0, 3.0],
        "pm2_5": [10.0, 15.0],
        "pm10": [20.0, 25.0],
        "nh3": [3.0, 5.0],
    })


@patch("src.load.postgres.create_engine")
def test_postgres_loader_init(mock_engine):
    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    assert loader.db_url == "postgresql://user:pass@localhost/test"
    assert loader.engine is None


@patch("src.load.postgres.create_engine")
def test_save_star_schema_calls_to_sql(mock_engine):
    mock_conn = MagicMock()
    mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)

    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    loader.engine = mock_engine.return_value

    with patch.object(loader, "_delete_all"), \
         patch.object(loader, "save") as mock_save, \
         patch.object(loader, "_ensure_unique_constraint"), \
         patch.object(loader, "_create_fk_if_not_exists"):
        loader.save_star_schema(_sample_dim_city(), _sample_dim_date(), _sample_fact_aqi(), "public")
        assert mock_save.call_count == 3


def test_save_star_schema_skips_empty():
    loader = PostgresLoader("postgresql://user:pass@localhost/test")
    loader.engine = MagicMock()

    with patch.object(loader, "_delete_all") as mock_delete, \
         patch.object(loader, "save") as mock_save, \
         patch.object(loader, "_get_engine"):
        empty_df = pd.DataFrame()
        loader.save_star_schema(empty_df, _sample_dim_date(), _sample_fact_aqi(), "public")
        assert mock_save.call_count == 2
