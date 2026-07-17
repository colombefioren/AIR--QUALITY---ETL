import time
from typing import Optional

import requests

from config.settings import Settings
from src.extract.city_extractor import CITIES, get_city_coords

OPENWEATHER_BASE = "http://api.openweathermap.org/data/2.5"
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
    url = f"{OPENWEATHER_BASE}/air_pollution"
    data = _request_with_retry(url, Settings.OPENWEATHER_API_KEY, params={
        "lat": coords["lat"],
        "lon": coords["lon"],
    })
    return data.get("list") if data else None
