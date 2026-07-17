import pandas as pd
import pytest
from pathlib import Path

from src.load.csv import save_processed_data, save_raw_backfill, save_raw_hourly


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city_name": ["Paris"],
        "date": ["2026-07-17"],
        "hour": [14],
        "aqi": [2],
        "co": [300],
    })


def test_save_raw_hourly_creates_file(sample_df, tmp_path):
    path = save_raw_hourly(sample_df, "Paris", tmp_path)
    assert path.exists()
    assert "paris_2026-07-17_14" in path.name


def test_save_raw_hourly_directories_created(sample_df, tmp_path):
    path = save_raw_hourly(sample_df, "London", tmp_path)
    assert path.parent.exists()


def test_save_raw_backfill_creates_file(sample_df, tmp_path):
    path = save_raw_backfill(sample_df, "Paris", tmp_path, 2026, 4)
    assert path.exists()
    assert "paris_2026-04" in path.name


def test_save_raw_backfill_directories_created(sample_df, tmp_path):
    path = save_raw_backfill(sample_df, "London", tmp_path, 2026, 4)
    assert path.parent.exists()


def test_save_processed_data(sample_df, tmp_path):
    dest = tmp_path / "clean" / "test.csv"
    path = save_processed_data(sample_df, dest)
    assert path == dest
    assert path.exists()
