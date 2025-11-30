"""
PM2.5 Prediction logic với detailed logging (NO AQI)
"""
import pandas as pd
from datetime import datetime, timedelta
import traceback
from core.data_fetcher import get_15_features_at_time
from core.feature_engineering import create_features_from_3hours
from utils.logger import main_logger as logger, pm25_logger
from config.settings import TZ_VN


def predict_pm25_for_district(district: dict, year: int, month: int, day: int,
                              hour: int, minute: int, api_key: str,
                              model, scaler, feature_columns: list,
                              include_raw_data: bool = True) -> dict:
    """
    Predict PM2.5 for one district with detailed PM2.5 logging.
    
    Args:
        district: District information dict
        year, month, day, hour, minute: Target time
        api_key: OpenWeather API key
        model: Trained model
        scaler: Feature scaler
        feature_columns: List of feature column names
        include_raw_data: Whether to include raw 15 features in response
    
    Returns:
        dict: Prediction result with status
    """
    district_name = district.get('name', 'Unknown')
    district_id = district.get('id', 'Unknown')

    try:
        # LOG: Request
        pm25_logger.log_request(district_id, district_name, year, month, day, hour, minute)
        logger.debug(f"🔄 Predicting for {district_name} (ID: {district_id})")

        # ✅ FIX: Get all 3 timestamps CLEARLY
        target_time = TZ_VN.localize(datetime(year, month, day, hour, minute))
        time_t1 = target_time - timedelta(hours=1)
        time_t2 = target_time - timedelta(hours=2)

        # ✅ FIX: Get features for ALL 3 times in correct order
        logger.debug(f"  Fetching t-2: {time_t2.strftime('%Y-%m-%d %H:%M')}")
        features_t2 = get_15_features_at_time(time_t2, api_key, district['lat'], district['lon'])
        
        logger.debug(f"  Fetching t-1: {time_t1.strftime('%Y-%m-%d %H:%M')}")
        features_t1 = get_15_features_at_time(time_t1, api_key, district['lat'], district['lon'])
        
        logger.debug(f"  Fetching t-0: {target_time.strftime('%Y-%m-%d %H:%M')}")
        features_t0 = get_15_features_at_time(target_time, api_key, district['lat'], district['lon'])

        # ✅ LOG: Raw PM2.5 values
        pm25_logger.log_raw_pm25(
            district_name,
            target_time.strftime('%Y-%m-%d %H:%M'),
            features_t2['pm2_5'],
            features_t1['pm2_5'],
            features_t0['pm2_5']
        )

        # ✅ FIX: Create DataFrame with correct order
        df_3hours = pd.DataFrame([features_t2, features_t1, features_t0])
        df_3hours = df_3hours.set_index("datetime").sort_index()
        
        # Verify we have 3 rows
        if len(df_3hours) != 3:
            raise ValueError(f"Expected 3 hours of data, got {len(df_3hours)}")
        
        logger.debug(f"  DataFrame shape: {df_3hours.shape}")
        logger.debug(f"  PM2.5 sequence (t-2, t-1, t-0): {df_3hours['pm2_5'].tolist()}")

        # Create 40 features
        df_features = create_features_from_3hours(df_3hours)
        
        # ✅ LOG: Key engineered features
        features_dict = df_features.iloc[0].to_dict()
        pm25_logger.log_features(district_name, features_dict)

        if feature_columns:
            df_features = df_features[feature_columns]

        # Scale and predict
        X_scaled = scaler.transform(df_features)
        prediction = float(model.predict(X_scaled)[0])

        # ✅ LOG: Prediction result
        pm25_logger.log_prediction(district_name, prediction, features_t0['pm2_5'])
        logger.debug(f"✅ {district_name}: PM2.5={prediction:.2f} μg/m³")

        result = {
            "id": district['id'],
            "name": district['name'],
            "name_en": district['name_en'],
            "lat": district['lat'],
            "lon": district['lon'],
            "pm25_prediction": round(prediction, 2),
            "population": district['population'],
            "area_km2": district['area_km2'],
            "type": district['type'],
            "status": "success"
        }

        # ✅ Include 15 raw features from t=0
        if include_raw_data:
            result["raw_data"] = {
                "timestamp": features_t0['datetime'].isoformat(),
                # Air quality data (8 fields)
                "air_quality": {
                    "co": round(float(features_t0['co']), 2),
                    "no": round(float(features_t0['no']), 2),
                    "no2": round(float(features_t0['no2']), 2),
                    "o3": round(float(features_t0['o3']), 2),
                    "so2": round(float(features_t0['so2']), 2),
                    "pm2_5": round(float(features_t0['pm2_5']), 2),
                    "pm10": round(float(features_t0['pm10']), 2),
                    "nh3": round(float(features_t0['nh3']), 2)
                },
                # Weather data (7 fields)
                "weather": {
                    "temperature_2m": round(float(features_t0['temperature_2m']), 2),
                    "relative_humidity_2m": round(float(features_t0['relative_humidity_2m']), 2),
                    "precipitation": round(float(features_t0['precipitation']), 2),
                    "pressure_msl": round(float(features_t0['pressure_msl']), 2),
                    "windspeed_10m": round(float(features_t0['windspeed_10m']), 2),
                    "winddirection_10m": round(float(features_t0['winddirection_10m']), 2),
                    "shortwave_radiation": round(float(features_t0['shortwave_radiation']), 2)
                }
            }

        return result

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        # ✅ LOG: Error
        pm25_logger.log_error(district_name, f"{error_type}: {error_msg}")
        logger.error(f"❌ {district_name}: {error_type}: {error_msg}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        return {
            "id": district['id'],
            "name": district['name'],
            "name_en": district['name_en'],
            "lat": district['lat'],
            "lon": district['lon'],
            "status": "error",
            "error": error_msg,
            "error_type": error_type
        }