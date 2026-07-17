from datetime import datetime
from unittest.mock import patch

import pytest

from src.extract.aqi_extractor import _month_chunks, extract_backfill


def test_month_chunks_three_full_months():
    start = datetime(2026, 4, 1)
    end = datetime(2026, 6, 30)
    chunks = _month_chunks(start, end)
    assert len(chunks) == 3
    assert chunks[0][0].month == 4
    assert chunks[1][0].month == 5
    assert chunks[2][0].month == 6


def test_month_chunks_partial():
    start = datetime(2026, 4, 15)
    end = datetime(2026, 7, 17)
    chunks = _month_chunks(start, end)
    assert len(chunks) == 4


def test_month_chunks_year_boundary():
    start = datetime(2025, 12, 15)
    end = datetime(2026, 2, 15)
    chunks = _month_chunks(start, end)
    assert len(chunks) == 3
    assert chunks[0][0].year == 2025
    assert chunks[0][0].month == 12
    assert chunks[1][0].year == 2026
    assert chunks[1][0].month == 1
    assert chunks[2][0].year == 2026
    assert chunks[2][0].month == 2


def test_month_chunks_single_month():
    start = datetime(2026, 4, 1)
    end = datetime(2026, 4, 30)
    chunks = _month_chunks(start, end)
    assert len(chunks) == 1


@patch("src.extract.aqi_extractor._request_with_retry")
def test_extract_backfill_success(mock_request):
    mock_request.return_value = {
        "list": [
            {"main": {"aqi": 1}, "components": {
                "co": 200, "no": 1, "no2": 5, "o3": 30,
                "so2": 2, "pm2_5": 10, "pm10": 20, "nh3": 3
            }, "dt": 1700000000}
        ]
    }
    start = datetime(2026, 4, 1)
    end = datetime(2026, 4, 30)
    result = extract_backfill("Antananarivo", start, end)
    assert result is not None
    assert len(result) == 1


@patch("src.extract.aqi_extractor._request_with_retry")
def test_extract_backfill_api_error(mock_request):
    mock_request.return_value = None
    start = datetime(2026, 4, 1)
    end = datetime(2026, 4, 30)
    result = extract_backfill("Antananarivo", start, end)
    assert result is None


def test_extract_backfill_unknown_city():
    start = datetime(2026, 4, 1)
    end = datetime(2026, 4, 30)
    result = extract_backfill("Atlantis", start, end)
    assert result is None
