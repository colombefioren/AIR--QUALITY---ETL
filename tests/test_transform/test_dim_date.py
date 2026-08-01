from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.transform.transformer.dim_date import build_dim_date


def _sample_df():
    return pd.DataFrame({
        "city_name": ["Paris", "Paris", "Paris"],
        "datetime": [
            datetime(2026, 7, 17, 10, 0),
            datetime(2026, 7, 17, 11, 0),
            datetime(2026, 7, 18, 10, 0),
        ],
        "date": ["2026-07-17", "2026-07-17", "2026-07-18"],
        "hour": [10, 11, 10],
        "aqi": [2, 3, 1],
    })


def test_build_dim_date_returns_df():
    df = build_dim_date(_sample_df())
    assert isinstance(df, pd.DataFrame)


def test_build_dim_date_unique_hours():
    df = build_dim_date(_sample_df())
    assert len(df) == 3


def test_build_dim_date_columns():
    df = build_dim_date(_sample_df())
    expected = {"date_key", "full_date", "hour", "day_of_week", "is_weekend", "month", "year"}
    assert expected.issubset(set(df.columns))


def test_build_dim_date_key_format():
    df = build_dim_date(_sample_df())
    key = df["date_key"].iloc[0]
    assert isinstance(key, (int, np.integer))
    assert len(str(key)) == 10


def test_build_dim_date_weekend():
    saturday = pd.DataFrame({
        "datetime": [datetime(2026, 7, 18, 10, 0)],
        "date": ["2026-07-18"],
        "hour": [10],
    })
    df = build_dim_date(saturday)
    assert bool(df["is_weekend"].iloc[0]) is True


def test_build_dim_date_saves_csv(tmp_path):
    csv_path = tmp_path / "dim_date.csv"
    build_dim_date(_sample_df(), csv_path=csv_path)
    assert csv_path.exists()
    loaded = pd.read_csv(csv_path)
    assert len(loaded) == 3
