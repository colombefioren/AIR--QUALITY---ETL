from unittest.mock import patch

import pytest
import requests

from src.extract.aqi_extractor import CITIES, extract_hourly


def test_cities_defined():
    assert len(CITIES) >= 6
    for city, coords in CITIES.items():
        assert "lat" in coords
        assert "lon" in coords


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
