import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from sqlalchemy import text

from src.load.postgres import PostgresLoader


class TestPostgresLoader:

    def test_init_sets_db_url(self):
        loader = PostgresLoader("postgresql://user:pass@localhost:5432/db")
        assert loader.db_url == "postgresql://user:pass@localhost:5432/db"
        assert loader.engine is None

    @patch("src.load.postgres.create_engine")
    def test_get_engine_creates_connection(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        loader = PostgresLoader("postgresql://user:pass@localhost:5432/db")
        engine = loader._get_engine()

        assert engine is mock_engine
        mock_create_engine.assert_called_once()

    def test_get_engine_reuses_existing(self):
        loader = PostgresLoader("postgresql://user:pass@localhost:5432/db")
        mock_engine = MagicMock()
        loader.engine = mock_engine

        engine = loader._get_engine()
        assert engine is mock_engine

    @patch("src.load.postgres.create_engine")
    def test_delete_all_executes_delete(self, mock_create_engine):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        loader = PostgresLoader("postgresql://user:pass@localhost:5432/db")
        loader._delete_all("fact_aqi", "air_quality")

        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        assert isinstance(call_args, text)
        assert "DELETE" in str(call_args)
        assert "air_quality.fact_aqi" in str(call_args)
        mock_conn.commit.assert_called_once()

    @patch("src.load.postgres.DataValidator.validate")
    @patch("src.load.postgres.create_engine")
    def test_save_calls_to_sql(self, mock_create_engine, mock_validate):
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = MagicMock()
        mock_create_engine.return_value = mock_engine

        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        loader = PostgresLoader("postgresql://user:pass@localhost:5432/db")
        loader.save(df, "fact_aqi", "air_quality")

        mock_validate.assert_called_once_with(df, "fact_aqi")
