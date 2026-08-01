import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from aqi_config.settings import Settings
from src.cities import get_city_coords

logger = logging.getLogger(__name__)


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
    url: str, api_key: str, params: Optional[dict] = None, retries: int = 3, timeout: int = 30
) -> Optional[dict]:
    params = params or {}
    params["appid"] = api_key
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                wait = 2 ** attempt
                logger.warning(f"Rate limited — retry {attempt+1}/{retries} in {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
        except requests.RequestException as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Attempt {attempt+1}/{retries} failed: {e} — retry in {wait}s")
                time.sleep(wait)
                continue
            logger.error(f"All {retries} attempts failed for {url}")
            return None
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
    chunks = _month_chunks(start_date, end_date)
    logger.info(f"[{city_name}] Backfill: {len(chunks)} month chunks to fetch")
    for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
        logger.info(f"[{city_name}] Fetching chunk {i}/{len(chunks)}: {chunk_start.date()} → {chunk_end.date()}")
        url = Settings.OPENWEATHER_BASE_URL + "/history"
        data = _request_with_retry(url, Settings.OPENWEATHER_API_KEY, params={
            "lat": coords["lat"],
            "lon": coords["lon"],
            "start": int(chunk_start.timestamp()),
            "end": int(chunk_end.timestamp()),
        })
        if data and "list" in data:
            all_entries.extend(data["list"])
            logger.info(f"[{city_name}] Chunk {i}/{len(chunks)}: got {len(data['list'])} entries")
        else:
            logger.warning(f"[{city_name}] Chunk {i}/{len(chunks)}: no data returned")
    logger.info(f"[{city_name}] Backfill complete: {len(all_entries)} total entries")
    return all_entries if all_entries else None
