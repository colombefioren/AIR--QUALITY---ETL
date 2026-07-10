import numpy as np
import pandas as pd
import pytest

from src.transform.quality.dataframe_cleaner import DataFrameCleaner


def test_normalize_empty_strings():
    df = pd.DataFrame({"a": ["hello", "", "  ", None, "world"]})
    result = DataFrameCleaner.normalize_empty_strings(df)
    assert pd.isna(result["a"].iloc[1])
    assert pd.isna(result["a"].iloc[2])
    assert result["a"].iloc[0] == "hello"
    assert result["a"].iloc[4] == "world"


def test_remove_duplicates():
    df = pd.DataFrame({"x": [1, 2, 2, 3], "y": ["a", "b", "b", "c"]})
    result = DataFrameCleaner.remove_duplicates(df)
    assert len(result) == 3


def test_fill_numeric_nulls():
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [np.nan, np.nan, np.nan]})
    result = DataFrameCleaner.fill_numeric_nulls(df, ["a", "b"])
    assert result["a"].iloc[1] == 0.0
    assert result["b"].iloc[0] == 0.0


def test_fill_categorical_nulls():
    df = pd.DataFrame({"cat": ["x", None, np.nan, "y"]})
    result = DataFrameCleaner.fill_categorical_nulls(df)
    assert result["cat"].iloc[1] == "unknown"
    assert result["cat"].iloc[2] == "unknown"


def test_drop_all_null_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [np.nan, np.nan], "c": [3, 4]})
    result = DataFrameCleaner.drop_all_null_columns(df)
    assert "b" not in result.columns
    assert list(result.columns) == ["a", "c"]


def test_dropna_rows_any():
    df = pd.DataFrame({"a": [1, np.nan, 3], "b": [4, 5, np.nan]})
    result = DataFrameCleaner.dropna_rows(df, how="any")
    assert len(result) == 1


def test_dropna_rows_subset():
    df = pd.DataFrame({"a": [1, np.nan, 3], "b": [4, 5, np.nan]})
    result = DataFrameCleaner.dropna_rows(df, subset=["a"])
    assert len(result) == 2


def test_clean_air_quality_data_empty():
    df = pd.DataFrame()
    result = DataFrameCleaner.clean_air_quality_data(df)
    assert result.empty


def test_clean_air_quality_data_full():
    df = pd.DataFrame({
        "pm2.5": [10.0, np.nan, 20.0],
        "pm10": [np.nan, 15.0, 25.0],
        "city_name": ["A", "B", None],
    })
    result = DataFrameCleaner.clean_air_quality_data(df)
    assert result["pm2.5"].isnull().sum() == 0
    assert result["pm10"].isnull().sum() == 0
    assert result["city_name"].iloc[2] == "unknown"
