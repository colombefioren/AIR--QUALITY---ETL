import logging
import pandas as pd
import pytest

from src.transform.quality.data_validator import DataValidator


def test_validate_all_within_range(caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"pm2.5": [10, 20, 30], "pm10": [40, 50, 60]})
    DataValidator.validate(df, "Test")
    assert "all values within valid ranges" in caplog.text


def test_validate_out_of_range(caplog):
    caplog.set_level(logging.WARNING)
    df = pd.DataFrame({"pm2.5": [10, 999, 30]})
    DataValidator.validate(df, "Test")
    assert "has 1 values outside" in caplog.text


def test_validate_missing_column(caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"not_a_metric": [1, 2, 3]})
    DataValidator.validate(df, "Test")
    assert "all values within valid ranges" in caplog.text


def test_validate_empty_dataframe(caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame()
    DataValidator.validate(df, "Test")
    assert "all values within valid ranges" in caplog.text


def test_validate_all_nulls(caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"pm2.5": [None, None]})
    DataValidator.validate(df, "Test")
    assert "all values within valid ranges" in caplog.text


def test_ranges_structure():
    assert "pm2.5" in DataValidator.RANGES
    assert "pm10" in DataValidator.RANGES
    assert "no2" in DataValidator.RANGES
    assert "o3" in DataValidator.RANGES
    assert "co" in DataValidator.RANGES
    assert "so2" in DataValidator.RANGES
    for col, (lo, hi) in DataValidator.RANGES.items():
        assert lo < hi
