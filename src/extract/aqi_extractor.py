import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from config.settings import Settings
from src.cities import get_city_coords

OPENWEATHER_BASE = "http://api.openweathermap.org/data/2.5"


def _month_chunks(
    start_date: datetime, end_date: datetime
) -> list[tuple[datetime, datetime]]:
    chunks = []
    current = datetime(start_date.year, start_date.month, 1)
    while current < end_date:
        if current.month == 12:
            next_month = datetime(current.year + 1, 1, 1)
        else:
            next_month = datetime(current.year, current.month + 1, 1)
        chunk_end = min(next_month - timedelta(seconds=1), end_date)
        chunks.append((current, chunk_end))
        current = next_month
    return chunks


def _request_with_retry(
    url: str, api_key: str, params: Optional[dict] = None, retries: int = 3
) -> Optional[dict]:
    params = params or {}
    params["appid"] = api_key
    for attempt in range(retries):
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
    return None


def extract_hourly(city_name: str) -> Optional[list[dict]]:
    coords = get_city_coords(city_name)
    if not coords:
        return None
    url = Settings.OPENWEATHER_BASE_URL
    data = _request_with_retry(url, Settings.OPENWEATHER_API_KEY, params={
        "lat": coords["lat"],
        "lon": coords["lon"],
    })
    return data.get("list") if data else None


def extract_backfill(
    city_name: str, start_date: datetime, end_date: datetime
) -> Optional[list[dict]]:
    coords = get_city_coords(city_name)
    if not coords:
        return None

    all_entries = []
    for chunk_start, chunk_end in _month_chunks(start_date, end_date):
        url = Settings.OPENWEATHER_BASE_URL + "/history"
        data = _request_with_retry(url, Settings.OPENWEATHER_API_KEY, params={
            "lat": coords["lat"],
            "lon": coords["lon"],
            "start": int(chunk_start.timestamp()),
            "end": int(chunk_end.timestamp()),
        })
        if data and "list" in data:
            all_entries.extend(data["list"])
    return all_entries if all_entries else None
