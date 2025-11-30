"""
Feature engineering for PM2.5 prediction
"""
import pandas as pd
import numpy as np
from utils.logger import main_logger as logger


def create_features_from_3hours(df_3hours: pd.DataFrame) -> pd.DataFrame:
    """Create 40 features from 3-hour DataFrame (vectorized)."""
    if len(df_3hours) < 3:
        raise ValueError(f"Need 3 hours of data, got {len(df_3hours)}")

    # LOG: Input data
    logger.debug(f"🔧 Creating features from {len(df_3hours)} rows")
    logger.debug(f"   Index: {df_3hours.index.tolist()}")
    logger.debug(f"   PM2.5 values: {df_3hours['pm2_5'].tolist()}")

    df = df_3hours.sort_index().copy()
    df_features = pd.DataFrame(index=df.index)

    # LAG FEATURES
    df_features["pm2_5_lag_1"] = df["pm2_5"].shift(1)
    df_features["pm2_5_lag_2"] = df["pm2_5"].shift(2)
    df_features["so2_lag_1"] = df["so2"].shift(1)
    df_features["co_lag_1"] = df["co"].shift(1)
    df_features["radiation_lag_1"] = df["shortwave_radiation"].shift(1)

    # ROLLING FEATURES
    rolling_3hr = df["pm2_5"].rolling(window=3, min_periods=1)
    df_features["pm2_5_roll_avg_3hr"] = rolling_3hr.mean()
    df_features["pm2_5_roll_std_3hr"] = rolling_3hr.std()
    df_features["temp_roll_avg_3hr"] = df["temperature_2m"].rolling(window=3, min_periods=1).mean()
    df_features["humid_roll_avg_3hr"] = df["relative_humidity_2m"].rolling(window=3, min_periods=1).mean()
    df_features["so2_roll_avg_3hr"] = df["so2"].rolling(window=3, min_periods=1).mean()

    wind_rolling = df["windspeed_10m"].rolling(window=3, min_periods=1)
    df_features["wind_roll_avg_3hr"] = wind_rolling.mean()
    df_features["wind_roll_min_3hr"] = wind_rolling.min()
    df_features["co_roll_avg_3hr"] = df["co"].rolling(window=3, min_periods=1).mean()
    df_features["precip_roll_sum_3hr"] = df["precipitation"].rolling(window=3, min_periods=1).sum()

    # DIFF FEATURES
    df_features["pm2_5_diff_1hr"] = df["pm2_5"].diff(1)
    df_features["temp_diff_1hr"] = df["temperature_2m"].diff(1)
    df_features["humid_diff_1hr"] = df["relative_humidity_2m"].diff(1)

    # ORIGINAL FEATURES
    original_cols = ["temperature_2m", "relative_humidity_2m", "precipitation",
                     "pressure_msl", "windspeed_10m", "shortwave_radiation",
                     "co", "no", "no2", "o3", "so2", "pm10", "nh3"]
    for col in original_cols:
        df_features[col] = df[col]

    # TIME FEATURES (vectorized)
    index_time = df_features.index
    hours = index_time.hour
    days = index_time.dayofweek
    months = index_time.month

    rainy_season_months = {5, 6, 7, 8, 9, 10}
    df_features["is_rainy_season"] = months.map(lambda x: 1 if x in rainy_season_months else 0)

    df_features["hour_sin"] = np.sin(2 * np.pi * hours / 24.0)
    df_features["hour_cos"] = np.cos(2 * np.pi * hours / 24.0)
    df_features["month_sin"] = np.sin(2 * np.pi * months / 12.0)
    df_features["month_cos"] = np.cos(2 * np.pi * months / 12.0)
    df_features["day_of_week_sin"] = np.sin(2 * np.pi * days / 7.0)
    df_features["day_of_week_cos"] = np.cos(2 * np.pi * days / 7.0)

    # INTERACTION FEATURES
    df_features["temp_humidity"] = df["temperature_2m"] * df["relative_humidity_2m"]
    wind_dir_rad = np.deg2rad(df["winddirection_10m"])
    wind_speed = df["windspeed_10m"]
    df_features["wind_U"] = wind_speed * np.cos(wind_dir_rad)
    df_features["wind_V"] = wind_speed * np.sin(wind_dir_rad)

    df_features = df_features.dropna()
    if df_features.empty:
        raise ValueError("Insufficient data to create features")

    # LOG: Output features
    logger.debug(f"   Features created: {df_features.shape}")
    logger.debug(f"   PM2.5 lag features: lag1={df_features['pm2_5_lag_1'].iloc[-1]:.2f}, "
                f"lag2={df_features['pm2_5_lag_2'].iloc[-1]:.2f}")

    return df_features.tail(1)