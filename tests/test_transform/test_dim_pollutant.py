import pandas as pd
import pytest

from src.transform.transformer.dim_pollutant import (
    POLLUTANTS,
    POLLUTANT_CATEGORIES,
    POLLUTANT_CODE_TO_ID,
    build_dim_pollutant,
    build_dim_pollutant_category,
)


def test_pollutant_categories_count():
    assert len(POLLUTANT_CATEGORIES) >= 2


def test_pollutants_count():
    assert len(POLLUTANTS) >= 8


def test_code_to_id_mapping():
    assert POLLUTANT_CODE_TO_ID["co"] == 1
    assert POLLUTANT_CODE_TO_ID["pm2_5"] == 6
    assert POLLUTANT_CODE_TO_ID["nh3"] == 8


def test_build_dim_pollutant_category_creates_csv(tmp_path):
    csv_path = tmp_path / "dim_pollutant_category.csv"
    df = build_dim_pollutant_category(csv_path)
    assert csv_path.exists()
    assert "category_id" in df.columns
    assert "category_name" in df.columns


def test_build_dim_pollutant_creates_csv(tmp_path):
    csv_path = tmp_path / "dim_pollutant.csv"
    df = build_dim_pollutant(csv_path)
    assert csv_path.exists()
    assert "pollutant_id" in df.columns
    assert "code" in df.columns
    assert "who_threshold" in df.columns


def test_build_dim_pollutant_category_reads_existing(tmp_path):
    csv_path = tmp_path / "dim_pollutant_category.csv"
    build_dim_pollutant_category(csv_path)
    df2 = build_dim_pollutant_category(csv_path)
    assert len(df2) == len(POLLUTANT_CATEGORIES)


def test_build_dim_pollutant_reads_existing(tmp_path):
    csv_path = tmp_path / "dim_pollutant.csv"
    build_dim_pollutant(csv_path)
    df2 = build_dim_pollutant(csv_path)
    assert len(df2) == len(POLLUTANTS)
