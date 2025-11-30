"""
Flask API Routes - PM2.5 Prediction Only (NO AQI)
With standardized error handling and validation
"""
from flask import request
import time
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple, Dict
from utils.logger import main_logger as logger, pm25_logger
from utils.cache_manager import PredictionCache
from core.predictor import predict_pm25_for_district
from config.settings import TZ_VN, MAX_WORKERS, DEFAULT_API_KEY, CACHE_TTL_PREDICTION
import traceback

# Initialize prediction cache
prediction_cache = PredictionCache(ttl=CACHE_TTL_PREDICTION)


# ==================== ERROR HANDLING ====================
def error_response(json_response_func, error_code: str, message: str, details: dict = None, status_code: int = 400):
    """
    Standardized error response format.
    
    Args:
        json_response_func: The json_response function passed from app
        error_code: ERROR_CODE (e.g. FUTURE_TIME, TIME_TOO_RECENT, MISSING_FIELD)
        message: Human-readable message (Vietnamese)
        details: Additional info for debugging
        status_code: HTTP status code
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.now(TZ_VN).isoformat()
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    return json_response_func(response, status_code)


def success_response(json_response_func, data: dict, message: str = None):
    """
    Standardized success response format.
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.now(TZ_VN).isoformat()
    }
    
    if message:
        response["message"] = message
    
    return json_response_func(response)


# ==================== VALIDATION ====================
def validate_prediction_request(year: int, month: int, day: int, hour: int, minute: int = 0) -> Tuple[bool, str, str, Dict]:
    """
    Validate prediction request time.
    
    Returns:
        (is_valid, error_code, error_message, info_dict)
    """
    now = datetime.now(TZ_VN)
    target_time = TZ_VN.localize(datetime(year, month, day, hour, minute))
    
    # Calculate prediction time (target + 1 hour)
    prediction_time = target_time + timedelta(hours=1)
    
    # RULE 1: Target time must be <= current time (no future queries)
    if target_time > now:
        time_diff_hours = (target_time - now).total_seconds() / 3600
        time_diff_minutes = int((target_time - now).total_seconds() / 60)
        
        message = f"Không thể dự đoán tương lai. Vui lòng chọn thời gian trước {now.strftime('%H:%M ngày %d/%m/%Y')}"
        
        details = {
            "target_time": target_time.strftime('%Y-%m-%d %H:%M'),
            "current_time": now.strftime('%Y-%m-%d %H:%M'),
            "difference_hours": round(time_diff_hours, 2),
            "difference_minutes": time_diff_minutes,
            "suggestion": f"Thử với thời gian <= {now.strftime('%H:%M')}"
        }
        
        return False, "FUTURE_TIME", message, details
    
    # RULE 2: Target time should be at least 30 minutes ago for data availability
    safe_time = now - timedelta(minutes=30)
    if target_time > safe_time:
        minutes_diff = int((now - target_time).total_seconds() / 60)
        wait_time = 30 - minutes_diff
        
        message = f"Dữ liệu chưa sẵn sàng. Vui lòng đợi thêm {wait_time} phút hoặc chọn thời gian trước {safe_time.strftime('%H:%M')}"
        
        details = {
            "target_time": target_time.strftime('%Y-%m-%d %H:%M'),
            "current_time": now.strftime('%Y-%m-%d %H:%M'),
            "safe_time": safe_time.strftime('%Y-%m-%d %H:%M'),
            "wait_minutes": wait_time,
            "reason": "Weather API cần thời gian đồng bộ dữ liệu (30 phút)"
        }
        
        return False, "TIME_TOO_RECENT", message, details
    
    # RULE 3: Don't allow too far in past (90 days)
    oldest_allowed = now - timedelta(days=90)
    if target_time < oldest_allowed:
        message = f"Thời gian quá xa trong quá khứ. Chỉ hỗ trợ dữ liệu trong vòng 90 ngày gần đây"
        
        details = {
            "target_time": target_time.strftime('%Y-%m-%d %H:%M'),
            "oldest_allowed": oldest_allowed.strftime('%Y-%m-%d %H:%M'),
            "days_difference": (now - target_time).days
        }
        
        return False, "TIME_TOO_OLD", message, details
    
    # ✅ All good! Return info
    t_minus_2 = target_time - timedelta(hours=2)
    t_minus_1 = target_time - timedelta(hours=1)
    
    info = {
        "target_time": target_time.strftime('%Y-%m-%d %H:%M'),
        "prediction_for": prediction_time.strftime('%Y-%m-%d %H:%M'),
        "data_from": {
            "t-2": t_minus_2.strftime('%Y-%m-%d %H:%M'),
            "t-1": t_minus_1.strftime('%Y-%m-%d %H:%M'),
            "t-0": target_time.strftime('%Y-%m-%d %H:%M')
        },
        "explanation": f"Sử dụng dữ liệu từ {t_minus_2.strftime('%H:%M')} - {target_time.strftime('%H:%M')} để dự đoán PM2.5 lúc {prediction_time.strftime('%H:%M')}",
        "explanation_en": f"Using data from {t_minus_2.strftime('%H:%M')} - {target_time.strftime('%H:%M')} to predict PM2.5 at {prediction_time.strftime('%H:%M')}"
    }
    
    return True, None, None, info


# ==================== ROUTE REGISTRATION ====================
def register_routes(app, model, scaler, feature_columns, districts, model_info, 
                   cache_manager, json_response):
    """Register all API routes."""
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return json_response({
            "status": "healthy",
            "version": "2.0-modular-pm25-only",
            "optimizations": {
                "cache_enabled": True,
                "prediction_cache_enabled": True,
                "modular_design": True,
                "pm25_detailed_logging": True,
                "smart_data_fetching": True,
                "standardized_error_handling": True
            },
            "cache_stats": cache_manager.stats(),
            "prediction_cache_stats": prediction_cache.stats(),
            "model": {
                "type": model_info.get('best_model'),
                "features": len(feature_columns),
                "rmse": model_info.get('best_rmse'),
                "r2": model_info.get('best_r2')
            },
            "districts_loaded": len(districts),
            "timestamp": datetime.now(TZ_VN).isoformat(),
            "usage": {
                "description": "Predict PM2.5 for NEXT HOUR based on LAST 3 HOURS",
                "example": "Query 10:00 uses data from 08:00, 09:00, 10:00 to predict 11:00",
                "validation_rules": {
                    "rule_1": "Target time must be <= current time (no future)",
                    "rule_2": "Target time must be >= 30 minutes ago (data availability)",
                    "rule_3": "Target time must be within 90 days (maximum history)"
                }
            }
        })

    @app.route('/api/v2/cache/clear', methods=['POST'])
    def clear_all_cache():
        """Clear all caches."""
        cache_manager.clear()
        prediction_cache.clear()
        return json_response({
            "success": True,
            "message": "All caches cleared successfully",
            "cache_stats": cache_manager.stats(),
            "prediction_cache_stats": prediction_cache.stats()
        })

    @app.route('/api/v2/districts', methods=['GET'])
    def get_districts_list():
        """Get all districts information."""
        return json_response({
            "success": True,
            "data": {
                "total": len(districts),
                "districts": districts
            },
            "timestamp": datetime.now(TZ_VN).isoformat()
        })

    @app.route('/api/v2/districts/<int:district_id>', methods=['GET'])
    def get_district_by_id(district_id: int):
        """Get specific district by ID."""
        district = next((d for d in districts if d['id'] == district_id), None)
        if not district:
            return error_response(
                json_response,
                "DISTRICT_NOT_FOUND",
                f"Không tìm thấy quận/huyện có ID {district_id}",
                {"available_ids": [d['id'] for d in districts]},
                404
            )

        return success_response(json_response, district)

    @app.route('/api/v2/predict/single', methods=['POST'])
    def predict_single():
        """
        Predict PM2.5 for NEXT HOUR based on LAST 3 HOURS for a single district.
        
        Request body:
        {
            "year": 2025,
            "month": 11,
            "day": 25,
            "hour": 8,
            "minute": 0,
            "district_id": 1,
            "api_key": "optional"
        }
        """
        try:
            payload = request.get_json()
            if not payload:
                return error_response(
                    json_response,
                    "MISSING_BODY",
                    "Thiếu dữ liệu JSON trong request"
                )

            required = ['year', 'month', 'day', 'hour', 'district_id']
            missing = [f for f in required if f not in payload]
            if missing:
                return error_response(
                    json_response,
                    "MISSING_FIELDS",
                    f"Thiếu các trường bắt buộc: {', '.join(missing)}",
                    {"required_fields": required, "missing_fields": missing}
                )

            year = int(payload['year'])
            month = int(payload['month'])
            day = int(payload['day'])
            hour = int(payload['hour'])
            minute = int(payload.get('minute', 0))
            district_id = int(payload['district_id'])
            api_key = payload.get('api_key', DEFAULT_API_KEY)

            # ✅ VALIDATE REQUEST
            is_valid, error_code, error_msg, info = validate_prediction_request(year, month, day, hour, minute)
            if not is_valid:
                return error_response(json_response, error_code, error_msg, info)

            logger.info(f"📍 Single prediction: district {district_id} at {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
            logger.info(f"   → {info['explanation']}")

            district = next((d for d in districts if d['id'] == district_id), None)
            if not district:
                return error_response(
                    json_response,
                    "DISTRICT_NOT_FOUND",
                    f"Không tìm thấy quận/huyện có ID {district_id}",
                    {"available_ids": [d['id'] for d in districts]},
                    404
                )

            result = predict_pm25_for_district(
                district, year, month, day, hour, minute, api_key,
                model, scaler, feature_columns
            )

            if result['status'] == 'error':
                return error_response(
                    json_response,
                    "PREDICTION_FAILED",
                    f"Không thể dự đoán cho {result['name']}",
                    result,
                    400
                )

            result['prediction_info'] = info
            result['timestamp_query'] = datetime.now(TZ_VN).isoformat()

            return success_response(json_response, result, "Dự đoán thành công")

        except ValueError as e:
            logger.error(f"❌ ValueError in predict_single: {e}")
            return error_response(
                json_response,
                "INVALID_INPUT",
                "Dữ liệu đầu vào không hợp lệ",
                {"error": str(e)},
                400
            )
        except Exception as e:
            logger.error(f"❌ Error in predict_single: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return error_response(
                json_response,
                "INTERNAL_ERROR",
                "Lỗi hệ thống. Vui lòng thử lại sau",
                {"error_type": type(e).__name__, "error_message": str(e)},
                500
            )

    @app.route('/api/v2/predict/all', methods=['POST'])
    def predict_all_districts():
        """
        Predict PM2.5 for NEXT HOUR based on LAST 3 HOURS for all districts.
        
        Request body:
        {
            "year": 2025,
            "month": 11,
            "day": 25,
            "hour": 11,
            "minute": 0,
            "api_key": "optional"
        }
        """
        try:
            start_time = time.time()

            payload = request.get_json()
            if not payload:
                return error_response(
                    json_response,
                    "MISSING_BODY",
                    "Thiếu dữ liệu JSON trong request"
                )

            required = ['year', 'month', 'day', 'hour']
            missing = [f for f in required if f not in payload]
            if missing:
                return error_response(
                    json_response,
                    "MISSING_FIELDS",
                    f"Thiếu các trường bắt buộc: {', '.join(missing)}",
                    {"required_fields": required, "missing_fields": missing}
                )

            year = int(payload['year'])
            month = int(payload['month'])
            day = int(payload['day'])
            hour = int(payload['hour'])
            minute = int(payload.get('minute', 0))
            api_key = payload.get('api_key', DEFAULT_API_KEY)

            # ✅ VALIDATE REQUEST
            is_valid, error_code, error_msg, info = validate_prediction_request(year, month, day, hour, minute)
            if not is_valid:
                logger.warning(f"⚠️  Validation failed: {error_code}")
                logger.warning(f"   Message: {error_msg}")
                return error_response(json_response, error_code, error_msg, info)

            # Check prediction cache first
            cached_result = prediction_cache.get(year, month, day, hour, minute)
            if cached_result:
                logger.info(f"⚡ Returning cached prediction result")
                # Wrap cached result in success format if not already
                if 'success' not in cached_result:
                    return success_response(json_response, cached_result, "Dự đoán thành công (từ cache)")
                return json_response(cached_result)

            target_time = TZ_VN.localize(datetime(year, month, day, hour, minute))

            logger.info(f"\n{'='*70}")
            logger.info(f"🌆 BATCH PREDICTION - ALL DISTRICTS")
            logger.info(f"   Query time: {target_time.strftime('%Y-%m-%d %H:%M')} VN")
            logger.info(f"   {info['explanation']}")
            logger.info(f"   Total: {len(districts)} districts")
            logger.info(f"{'='*70}")

            # Parallel prediction
            results = []
            errors = []

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(
                        predict_pm25_for_district,
                        district, year, month, day, hour, minute, api_key,
                        model, scaler, feature_columns
                    ): district for district in districts
                }

                for future in as_completed(futures):
                    result = future.result()

                    if result['status'] == 'success':
                        results.append(result)
                    else:
                        errors.append(result)

            results.sort(key=lambda x: x['id'])
            errors.sort(key=lambda x: x['id'])

            # Summary logging
            expected = len(districts)
            success = len(results)
            failed = len(errors)

            logger.info(f"\n{'='*70}")
            logger.info(f"📊 BATCH RESULTS: {success}/{expected} success, {failed} failed ({success/expected*100:.1f}%)")

            if failed > 0:
                logger.warning(f"⚠️  {failed} districts failed:")
                for err in errors[:5]:
                    logger.warning(f"   • {err['name']}: {err.get('error_type')}")
            else:
                logger.info(f"   ✅ ALL {expected} DISTRICTS SUCCESS!")

            logger.info(f"{'='*70}\n")

            # Calculate statistics
            if results:
                pm25_values = [r['pm25_prediction'] for r in results]
                statistics = {
                    "city_average": round(np.mean(pm25_values), 2),
                    "city_max": round(np.max(pm25_values), 2),
                    "city_min": round(np.min(pm25_values), 2),
                    "city_median": round(np.median(pm25_values), 2),
                    "city_std": round(np.std(pm25_values), 2),
                    "total_districts_successful": success,
                    "total_districts_expected": expected,
                    "total_districts_failed": failed,
                    "success_rate_percent": round(success/expected*100, 2),
                    "who_standard_15": {
                        "above": sum(1 for v in pm25_values if v > 15),
                        "below": sum(1 for v in pm25_values if v <= 15)
                    },
                    "unhealthy_threshold_55": sum(1 for v in pm25_values if v > 55.4)
                }
                
                pm25_logger.log_summary(
                    expected, success, failed, 
                    statistics['city_average'], 
                    time.time() - start_time
                )
            else:
                statistics = {
                    "error": "No successful predictions",
                    "total_districts_expected": expected,
                    "total_districts_failed": failed
                }

            execution_time = round(time.time() - start_time, 2)
            logger.info(f"⏱️  Total execution time: {execution_time}s")

            response_data = {
                "prediction_info": info,
                "districts": results,
                "statistics": statistics,
                "execution_time_seconds": execution_time,
                "cache_info": {
                    "cached": False,
                    "ttl_seconds": CACHE_TTL_PREDICTION
                },
                "model_info": {
                    "type": model_info.get('best_model'),
                    "rmse": model_info.get('best_rmse'),
                    "r2": model_info.get('best_r2')
                }
            }

            if errors:
                response_data["errors"] = errors
                response_data["warning"] = f"Failed {failed}/{expected} districts"

            # Cache the SUCCESS response (wrapped)
            success_wrapped = {
                "success": True,
                "data": response_data,
                "message": "Dự đoán thành công",
                "timestamp": datetime.now(TZ_VN).isoformat()
            }
            prediction_cache.set(year, month, day, hour, minute, success_wrapped)

            return success_response(json_response, response_data, "Dự đoán thành công")

        except ValueError as e:
            logger.error(f"❌ ValueError: {e}")
            return error_response(
                json_response,
                "INVALID_INPUT",
                "Dữ liệu đầu vào không hợp lệ",
                {"error": str(e)},
                400
            )
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR: {type(e).__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return error_response(
                json_response,
                "INTERNAL_ERROR",
                "Lỗi hệ thống. Vui lòng thử lại sau",
                {"error_type": type(e).__name__, "error_message": str(e)},
                500
            )

    @app.route('/api/v2/ranking', methods=['POST'])
    def get_ranking():
        """
        Get ranked list of districts by PM2.5 or population.
        Reuses cached prediction result if available.
        """
        try:
            payload = request.get_json()
            if not payload:
                return error_response(
                    json_response,
                    "MISSING_BODY",
                    "Thiếu dữ liệu JSON trong request"
                )

            year = int(payload['year'])
            month = int(payload['month'])
            day = int(payload['day'])
            hour = int(payload['hour'])
            minute = int(payload.get('minute', 0))

            # ✅ VALIDATE REQUEST
            is_valid, error_code, error_msg, info = validate_prediction_request(year, month, day, hour, minute)
            if not is_valid:
                return error_response(json_response, error_code, error_msg, info)

            # Try to reuse cached prediction
            cached = prediction_cache.get(year, month, day, hour, minute)
            if cached:
                logger.info("⚡ Reusing cached prediction for ranking")
                # Handle both wrapped and unwrapped cache formats
                if 'data' in cached:
                    districts_data = cached['data']['districts']
                    stats = cached['data']['statistics']
                else:
                    districts_data = cached['districts']
                    stats = cached['statistics']
            else:
                return error_response(
                    json_response,
                    "NO_PREDICTION_DATA",
                    "Chưa có dữ liệu dự đoán cho thời gian này",
                    {"suggestion": "Gọi /api/v2/predict/all trước để tạo dự đoán"},
                    404
                )

            sort_by = payload.get('sort_by', 'pm25')
            order = payload.get('order', 'desc')
            limit = int(payload.get('limit', 10))

            # Sort districts
            reverse = (order == 'desc')
            if sort_by == 'pm25':
                sorted_districts = sorted(districts_data, key=lambda x: x['pm25_prediction'], reverse=reverse)
            elif sort_by == 'population':
                sorted_districts = sorted(districts_data, key=lambda x: x['population'], reverse=reverse)
            else:
                return error_response(
                    json_response,
                    "INVALID_SORT",
                    f"Tham số sort_by không hợp lệ: {sort_by}",
                    {"valid_options": ["pm25", "population"]},
                    400
                )

            result_data = {
                "prediction_info": info,
                "sort_by": sort_by,
                "order": order,
                "limit": limit,
                "ranking": sorted_districts[:limit],
                "best_air_quality": sorted(districts_data, key=lambda x: x['pm25_prediction'])[:5],
                "worst_air_quality": sorted(districts_data, key=lambda x: x['pm25_prediction'], reverse=True)[:5],
                "statistics": stats
            }

            return success_response(json_response, result_data)

        except Exception as e:
            logger.error(f"❌ Error in ranking: {e}")
            return error_response(
                json_response,
                "INTERNAL_ERROR",
                "Lỗi hệ thống khi xếp hạng",
                {"error": str(e)},
                500
            )

    @app.route('/api/v2/map/geojson', methods=['POST'])
    def get_geojson():
        """
        Get GeoJSON format for map visualization.
        Reuses cached prediction result if available.
        """
        try:
            payload = request.get_json()

            year = int(payload['year'])
            month = int(payload['month'])
            day = int(payload['day'])
            hour = int(payload['hour'])
            minute = int(payload.get('minute', 0))

            # ✅ VALIDATE REQUEST
            is_valid, error_code, error_msg, info = validate_prediction_request(year, month, day, hour, minute)
            if not is_valid:
                return error_response(json_response, error_code, error_msg, info)

            # Reuse cached prediction
            cached = prediction_cache.get(year, month, day, hour, minute)
            if cached:
                logger.info("⚡ Reusing cached prediction for GeoJSON")
                # Handle both wrapped and unwrapped cache formats
                if 'data' in cached:
                    districts_data = cached['data']['districts']
                    stats = cached['data']['statistics']
                else:
                    districts_data = cached['districts']
                    stats = cached['statistics']
            else:
                return error_response(
                    json_response,
                    "NO_PREDICTION_DATA",
                    "Chưa có dữ liệu dự đoán cho thời gian này",
                    {"suggestion": "Gọi /api/v2/predict/all trước để tạo dự đoán"},
                    404
                )

            # Create GeoJSON
            features = []
            for district in districts_data:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "id": district['id'],
                        "name": district['name'],
                        "name_en": district['name_en'],
                        "pm25": district['pm25_prediction'],
                        "population": district['population'],
                        "area_km2": district['area_km2'],
                        "type": district['type']
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [district['lon'], district['lat']]
                    }
                }
                features.append(feature)

            result_data = {
                "type": "FeatureCollection",
                "prediction_info": info,
                "features": features,
                "statistics": stats
            }

            return success_response(json_response, result_data)

        except Exception as e:
            logger.error(f"❌ Error in GeoJSON: {e}")
            return error_response(
                json_response,
                "INTERNAL_ERROR",
                "Lỗi hệ thống khi tạo GeoJSON",
                {"error": str(e)},
                500
            )

    # Return the app
    return app