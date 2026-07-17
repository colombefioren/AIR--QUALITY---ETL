import time
from typing import Optional

import requests

from config.settings import Settings

OPENWEATHER_BASE = "http://api.openweathermap.org/data/2.5"

# TODO: replace with Dev 3's city_extractor on merge
CITIES = {
    "Paris":        {"lat": 48.8566,  "lon": 2.3522},
    "London":       {"lat": 51.5074,  "lon": -0.1278},
    "New York":     {"lat": 40.7128,  "lon": -74.0060},
    "Beijing":      {"lat": 39.9042,  "lon": 116.4074},
    "Mumbai":       {"lat": 19.0760,  "lon": 72.8777},
    "Antananarivo": {"lat": -18.8792, "lon": 47.5079},
}

# TODO: refactor — replace with Dev 1's shared retry helper on merge
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
    coords = CITIES.get(city_name)
    if not coords:
        return None
    url = f"{OPENWEATHER_BASE}/air_pollution"
    data = _request_with_retry(url, Settings.OPENWEATHER_API_KEY, params={
        "lat": coords["lat"],
        "lon": coords["lon"],
    })
    return data.get("list") if data else None
