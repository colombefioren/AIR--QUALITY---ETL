from unittest.mock import patch

import pytest
import requests

from src.extract.aqi_extractor import extract_hourly
from src.cities import CITIES, get_city_coords, get_city_names


def test_cities_count():
    assert len(CITIES) >= 6


def test_cities_have_required_fields():
    for city in CITIES:
        assert "city_name" in city
        assert "country" in city
        assert "latitude" in city
        assert "longitude" in city


def test_get_city_coords_known():
    coords = get_city_coords("Paris")
    assert coords is not None
    assert "lat" in coords
    assert "lon" in coords


def test_get_city_coords_unknown():
    assert get_city_coords("Atlantis") is None


def test_get_city_names():
    names = get_city_names()
    assert len(names) >= 6
    assert "Paris" in names
    assert "London" in names


@patch("src.extract.aqi_extractor._request_with_retry")
def test_extract_hourly_success(mock_request):
    mock_request.return_value = {
        "list": [{"main": {"aqi": 1}, "components": {
            "co": 200, "no": 1, "no2": 5, "o3": 30,
            "so2": 2, "pm2_5": 10, "pm10": 20, "nh3": 3
        }, "dt": 1700000000}]
    }
    result = extract_hourly("Paris")
    assert result is not None
    assert len(result) == 1


@patch("src.extract.aqi_extractor._request_with_retry")
def test_extract_hourly_api_error(mock_request):
    mock_request.return_value = None
    result = extract_hourly("Paris")
    assert result is None


def test_extract_hourly_unknown_city():
    result = extract_hourly("Atlantis")
    assert result is None
