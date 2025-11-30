"""
Data fetching logic for air quality and weather data
"""
from datetime import datetime, timedelta
import pandas as pd
import pytz
from utils.http_session import http_session
from utils.cache_manager import CacheManager
from utils.logger import main_logger as logger
from config.settings import (
    CACHE_TTL_AIR, CACHE_TTL_WEATHER, TIMEOUT, TZ_VN
)

# Initialize cache
cache_manager = CacheManager()


def fetch_air_quality_at_time(timestamp_utc: int, api_key: str, 
                              lat: float, lon: float) -> dict:
    """Fetch air quality data with caching."""
    cache_key = cache_manager._generate_key('air', timestamp_utc, lat, lon)

    # Try cache first
    cached = cache_manager.get(cache_key, CACHE_TTL_AIR)
    if cached is not None:
        return cached

    # Fetch from API
    url = (
        f"http://api.openweathermap.org/data/2.5/air_pollution/history"
        f"?lat={lat}&lon={lon}&start={timestamp_utc - 600}&end={timestamp_utc + 600}&appid={api_key}"
    )

    try:
        r = http_session.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        if not data.get("list"):
            raise ValueError(f"No air quality data at timestamp {timestamp_utc}")

        closest = min(data["list"], key=lambda x: abs(x["dt"] - timestamp_utc))
        result = {
            "co": closest["components"]["co"],
            "no": closest["components"]["no"],
            "no2": closest["components"]["no2"],
            "o3": closest["components"]["o3"],
            "so2": closest["components"]["so2"],
            "pm2_5": closest["components"]["pm2_5"],
            "pm10": closest["components"]["pm10"],
            "nh3": closest["components"]["nh3"]
        }

        # Cache result
        cache_manager.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"❌ Air Quality API error: {e}")
        raise


def fetch_weather_at_time(target_time_vn: datetime, lat: float, lon: float) -> dict:
    """
    Fetch weather data with caching.
    Automatically uses archive API for past data and forecast API for current/future data.
    """
    # Check if we need archive or forecast
    now_vn = datetime.now(TZ_VN)
    target_naive = target_time_vn.replace(tzinfo=None)
    now_naive = now_vn.replace(tzinfo=None)
    
    # If target is today or in the future, use forecast API
    if target_naive.date() >= now_naive.date():
        logger.debug(f"Using FORECAST API for {target_time_vn.strftime('%Y-%m-%d %H:%M')}")
        return fetch_weather_forecast(target_time_vn, lat, lon)
    else:
        logger.debug(f"Using ARCHIVE API for {target_time_vn.strftime('%Y-%m-%d %H:%M')}")
        return fetch_weather_archive(target_time_vn, lat, lon)


def fetch_weather_archive(target_time_vn: datetime, lat: float, lon: float) -> dict:
    """Fetch PAST weather data from archive API."""
    day_str = target_time_vn.strftime("%Y-%m-%d")
    cache_key = cache_manager._generate_key('weather_archive', day_str, lat, lon, target_time_vn.hour)

    # Try cache first
    cached = cache_manager.get(cache_key, CACHE_TTL_WEATHER)
    if cached is not None:
        return cached

    # Fetch from API
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": day_str,
        "end_date": day_str,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,pressure_msl,"
                  "windspeed_10m,winddirection_10m,shortwave_radiation",
        "timezone": "UTC"  # ✅ FIX: Use UTC to avoid timezone confusion
    }

    try:
        r = http_session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        hourly_data = data.get("hourly", {})
        if not hourly_data:
            raise ValueError("No weather data available")

        df = pd.DataFrame(hourly_data)
        df["time"] = pd.to_datetime(df["time"])
        
        # ✅ FIX: API returns UTC, localize then convert to VN timezone
        df["time"] = df["time"].dt.tz_localize("UTC").dt.tz_convert(TZ_VN)
        
        target_hour = target_time_vn.replace(minute=0, second=0, microsecond=0)
        
        # Debug logging
        logger.debug(f"🔍 Archive API - Target: {target_hour}")
        logger.debug(f"   Available times: {df['time'].tolist()[:3]} ... {df['time'].tolist()[-3:]}")
        
        matched = df[df["time"] == target_hour]

        if matched.empty:
            # Try to find closest hour
            df["time_diff"] = abs((df["time"] - target_hour).dt.total_seconds())
            closest_idx = df["time_diff"].idxmin()
            row = df.loc[closest_idx]
            closest_time = row["time"]
            time_diff_hours = abs((closest_time - target_hour).total_seconds()) / 3600
            
            logger.warning(
                f"⚠️  No exact match for {target_hour}. "
                f"Using closest: {closest_time} (diff: {time_diff_hours:.1f}h)"
            )
        else:
            row = matched.iloc[0]
            logger.debug(f"✅ Found exact match for {target_hour}")

        result = {
            "temperature_2m": float(row["temperature_2m"]),
            "relative_humidity_2m": float(row["relative_humidity_2m"]),
            "precipitation": float(row["precipitation"]),
            "pressure_msl": float(row["pressure_msl"]),
            "windspeed_10m": float(row["windspeed_10m"]),
            "winddirection_10m": float(row["winddirection_10m"]),
            "shortwave_radiation": float(row["shortwave_radiation"])
        }

        # Cache result
        cache_manager.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"❌ Weather Archive API error: {e}")
        raise


def fetch_weather_forecast(target_time_vn: datetime, lat: float, lon: float) -> dict:
    """Fetch CURRENT/FUTURE weather data from forecast API."""
    cache_key = cache_manager._generate_key(
        'weather_forecast', 
        target_time_vn.strftime("%Y-%m-%d-%H"), 
        lat, lon
    )

    # Try cache first (shorter TTL for forecast)
    cached = cache_manager.get(cache_key, 1800)  # 30 min cache for forecast
    if cached is not None:
        return cached

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,pressure_msl,"
                  "wind_speed_10m,wind_direction_10m,shortwave_radiation",
        "timezone": "UTC",  # ✅ Use UTC
        "forecast_days": 3  # Get 3 days to be safe
    }

    try:
        r = http_session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()

        hourly_data = data.get("hourly", {})
        if not hourly_data:
            raise ValueError("No forecast weather data available")

        df = pd.DataFrame(hourly_data)
        df["time"] = pd.to_datetime(df["time"])
        
        # ✅ API returns UTC, localize then convert to VN timezone
        df["time"] = df["time"].dt.tz_localize("UTC").dt.tz_convert(TZ_VN)
        
        target_hour = target_time_vn.replace(minute=0, second=0, microsecond=0)
        
        # Debug logging
        logger.debug(f"🔍 Forecast API - Target: {target_hour}")
        logger.debug(f"   Available times: {df['time'].tolist()[:5]}")
        
        matched = df[df["time"] == target_hour]

        if matched.empty:
            # Try to find closest hour
            df["time_diff"] = abs((df["time"] - target_hour).dt.total_seconds())
            closest_idx = df["time_diff"].idxmin()
            row = df.loc[closest_idx]
            closest_time = row["time"]
            time_diff_hours = abs((closest_time - target_hour).total_seconds()) / 3600
            
            logger.warning(
                f"⚠️  Forecast: No exact match for {target_hour}. "
                f"Using closest: {closest_time} (diff: {time_diff_hours:.1f}h)"
            )
        else:
            row = matched.iloc[0]
            logger.debug(f"✅ Forecast: Found exact match for {target_hour}")

        # ✅ Handle both field name variations (wind_speed_10m vs windspeed_10m)
        result = {
            "temperature_2m": float(row["temperature_2m"]),
            "relative_humidity_2m": float(row["relative_humidity_2m"]),
            "precipitation": float(row["precipitation"]),
            "pressure_msl": float(row["pressure_msl"]),
            "windspeed_10m": float(row.get("wind_speed_10m", row.get("windspeed_10m", 0))),
            "winddirection_10m": float(row.get("wind_direction_10m", row.get("winddirection_10m", 0))),
            "shortwave_radiation": float(row["shortwave_radiation"])
        }

        cache_manager.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"❌ Weather Forecast API error: {e}")
        raise


def get_15_features_at_time(target_time_vn: datetime, api_key: str, 
                           lat: float, lon: float) -> dict:
    """Get 15 raw features (8 air + 7 weather) at specific time."""
    target_utc = target_time_vn.astimezone(pytz.UTC)
    timestamp_utc = int(target_utc.timestamp())
    
    air_data = fetch_air_quality_at_time(timestamp_utc, api_key, lat, lon)
    weather_data = fetch_weather_at_time(target_time_vn, lat, lon)
    
    return {"datetime": target_time_vn, **air_data, **weather_data}