import pandas as pd
import pytest
from pathlib import Path

from src.load.csv import save_raw_hourly, save_processed_data


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city_name": ["Paris"],
        "aqi": [2],
        "co": [300],
    })


def test_save_raw_hourly_creates_file(sample_df, tmp_path):
    path = save_raw_hourly(sample_df, "Paris", tmp_path)
    assert path.exists()
    assert "paris" in path.name


def test_save_raw_hourly_directories_created(sample_df, tmp_path):
    path = save_raw_hourly(sample_df, "London", tmp_path)
    assert path.parent.exists()


def test_save_processed_data(sample_df, tmp_path):
    dest = tmp_path / "clean" / "test.csv"
    path = save_processed_data(sample_df, dest)
    assert path == dest
    assert path.exists()
