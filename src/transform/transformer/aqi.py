from datetime import datetime

import pandas as pd


def transform_hourly_aqi(raw_list: list[dict], city_name: str) -> pd.DataFrame:
    rows = []
    for entry in raw_list:
        dt = datetime.fromtimestamp(entry["dt"])
        rows.append({
            "city_name": city_name,
            "timestamp": dt,
            "date": dt.date(),
            "hour": dt.hour,
            "aqi": entry["main"]["aqi"],
            "co": entry["components"]["co"],
            "no": entry["components"]["no"],
            "no2": entry["components"]["no2"],
            "o3": entry["components"]["o3"],
            "so2": entry["components"]["so2"],
            "pm2_5": entry["components"]["pm2_5"],
            "pm10": entry["components"]["pm10"],
            "nh3": entry["components"]["nh3"],
        })
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["city_name", "date", "hour"], keep="last")
    return df
