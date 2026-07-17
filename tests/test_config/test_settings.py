from pathlib import Path
from unittest.mock import patch
import pytest

from config.settings import Settings


def test_default_values():
    assert Settings.POSTGRES_HOST == "localhost"
    assert Settings.POSTGRES_SCHEMA == "public"
    assert Settings.DATA_DIR == Path("data")
    assert Settings.RAW_BACKFILL_DIR == Path("data/raw/backfill")
    assert Settings.RAW_HOURLY_DIR == Path("data/raw/hourly")
    assert Settings.HOURLY_COMBINED_PATH == Path("data/clean/hourly_aqi_combined.csv")
    assert Settings.CITY_CSV_PATH == Path("data/star_schema/dim_city.csv")


def test_openweather_base_url():
    assert "openweathermap" in Settings.OPENWEATHER_BASE_URL
    assert "air_pollution" in Settings.OPENWEATHER_BASE_URL
    assert Settings.OPENWEATHER_BASE_URL.startswith("http")


def test_get_database_url():
    with patch.object(Settings, "POSTGRES_HOST", "localhost"):
        with patch.object(Settings, "POSTGRES_PORT", "5432"):
            with patch.object(Settings, "POSTGRES_DB", "air_quality"):
                with patch.object(Settings, "POSTGRES_USER", "user"):
                    with patch.object(Settings, "POSTGRES_PASSWORD", "pass"):
                        url = Settings.get_database_url()
                        assert url == "postgresql://user:pass@localhost:5432/air_quality"


def test_validate_missing_api_key():
    with patch.object(Settings, "OPENWEATHER_API_KEY", None):
        with pytest.raises(ValueError, match="OPENWEATHER_API_KEY"):
            Settings.validate()


def test_validate_missing_postgres_vars():
    with patch.object(Settings, "OPENWEATHER_API_KEY", "test-key"):
        with patch.object(Settings, "POSTGRES_PORT", None):
            with patch.object(Settings, "POSTGRES_DB", None):
                with pytest.raises(ValueError, match="POSTGRES"):
                    Settings.validate()


def test_validate_success():
    with patch.object(Settings, "OPENWEATHER_API_KEY", "test-key"):
        with patch.object(Settings, "POSTGRES_PORT", "5432"):
            with patch.object(Settings, "POSTGRES_DB", "test_db"):
                with patch.object(Settings, "POSTGRES_USER", "test_user"):
                    with patch.object(Settings, "POSTGRES_PASSWORD", "test_pass"):
                        Settings.validate()


def test_ensure_directories_creates_paths(tmp_path):
    test_data = tmp_path / "data"
    with patch.object(Settings, "DATA_DIR", test_data):
        with patch.object(Settings, "RAW_DIR", test_data / "raw"):
            with patch.object(Settings, "CLEAN_DIR", test_data / "clean"):
                with patch.object(Settings, "STAR_SCHEMA_DIR", test_data / "star_schema"):
                    with patch.object(Settings, "RAW_BACKFILL_DIR", test_data / "raw" / "backfill"):
                        with patch.object(Settings, "RAW_HOURLY_DIR", test_data / "raw" / "hourly"):
                            Settings.ensure_directories()
                            assert (test_data / "raw" / "backfill").exists()
                            assert (test_data / "raw" / "hourly").exists()
                            assert (test_data / "clean").exists()
                            assert (test_data / "star_schema").exists()
