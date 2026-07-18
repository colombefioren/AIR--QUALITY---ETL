import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.cities import CITIES, REGIONS, get_city_coords, get_city_names, load_cities, load_regions


def test_cities_list_not_empty():
    assert len(CITIES) >= 6


def test_cities_have_coords():
    for city in CITIES:
        assert isinstance(city["latitude"], (int, float))
        assert isinstance(city["longitude"], (int, float))


def test_load_cities_creates_csv(tmp_path):
    csv_path = tmp_path / "dim_city.csv"
    df = load_cities(csv_path)
    assert csv_path.exists()
    assert len(df) == len(CITIES)
    assert "city_key" in df.columns
    assert "city_name" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns


def test_load_cities_reads_existing_csv(tmp_path):
    csv_path = tmp_path / "dim_city.csv"
    load_cities(csv_path)
    df2 = load_cities(csv_path)
    assert len(df2) == len(CITIES)


def test_city_keys_are_sequential(tmp_path):
    csv_path = tmp_path / "dim_city.csv"
    df = load_cities(csv_path)
    assert list(df["city_key"]) == list(range(1, len(CITIES) + 1))


def test_get_city_names_returns_list():
    names = get_city_names()
    assert isinstance(names, list)
    assert "Antananarivo" in names


def test_regions_defined():
    assert len(REGIONS) >= 6


def test_load_regions_creates_csv(tmp_path):
    csv_path = tmp_path / "dim_region.csv"
    df = load_regions(csv_path)
    assert csv_path.exists()
    assert "region_id" in df.columns
    assert "region_name" in df.columns


def test_load_regions_reads_existing(tmp_path):
    csv_path = tmp_path / "dim_region.csv"
    load_regions(csv_path)
    df2 = load_regions(csv_path)
    assert len(df2) == len(REGIONS)
