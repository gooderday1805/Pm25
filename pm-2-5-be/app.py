"""
PM2.5 Prediction API - Main Application
Modular architecture with detailed PM2.5 logging (NO AQI)
"""
from flask import Flask, Response
from flask_cors import CORS
import joblib
import os

# Import utilities
from utils.logger import main_logger as logger
from utils.cache_manager import CacheManager
from config.settings import (
    MODEL_PATH, SCALER_PATH, JSON_PATH, DISTRICTS_PATH,
    MAX_CACHE_SIZE
)

# Import routes
from api.routes import register_routes

# ==================== JSON RESPONSE UTILITY ====================
try:
    import orjson
    USE_ORJSON = True

    def json_response(data, status=200):
        """Fast JSON response using orjson."""
        return Response(
            orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY),
            status=status,
            mimetype='application/json'
        )
except ImportError:
    USE_ORJSON = False
    from flask import jsonify
    print("⚠️  orjson not available, using standard json")
    json_response = lambda data, status=200: (jsonify(data), status)

# ==================== LOAD STATIC DATA ====================
def load_json_once(filepath: str, description: str = "data"):
    """Load JSON file once at startup."""
    try:
        if USE_ORJSON:
            with open(filepath, 'rb') as f:
                data = orjson.loads(f.read())
        else:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

        logger.info(f"✅ Loaded {description} from {filepath}")
        return data
    except Exception as e:
        logger.error(f"❌ Failed to load {description}: {e}")
        raise

# ==================== INITIALIZE FLASK APP ====================
def create_app():
    """Create and configure Flask application."""
    
    print("\n" + "=" * 70)
    print("🔧 INITIALIZING PM2.5 API - MODULAR (NO AQI)")
    print("=" * 70)

    # Create Flask app
    app = Flask(__name__)
    CORS(app)

    # Flask config
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    # Load model and data
    logger.info(f"📦 Loading model from: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    logger.info("   ✅ Model loaded")

    logger.info(f"📦 Loading scaler from: {SCALER_PATH}")
    scaler = joblib.load(SCALER_PATH)
    logger.info("   ✅ Scaler loaded")

    logger.info(f"📦 Loading model info from: {JSON_PATH}")
    model_info = load_json_once(JSON_PATH, "model info")
    feature_columns = model_info.get('feature_columns')
    logger.info(f"   ✅ Loaded {len(feature_columns)} features")

    logger.info(f"📦 Loading districts from: {DISTRICTS_PATH}")
    districts_data = load_json_once(DISTRICTS_PATH, "districts")
    districts = districts_data['districts']
    logger.info(f"   ✅ Loaded {len(districts)} districts")

    # Initialize cache
    cache_manager = CacheManager(max_size=MAX_CACHE_SIZE)

    # Register routes
    register_routes(app, model, scaler, feature_columns, districts, 
                   model_info, cache_manager, json_response)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return json_response({
            "error": "Endpoint not found",
            "status": 404
        }, 404)

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal error: {error}")
        return json_response({
            "error": "Internal server error",
            "status": 500
        }, 500)

    print("=" * 70)
    print("✅ PM2.5 API READY (NO AQI)")
    print(f"   orjson: {'✅ Enabled' if USE_ORJSON else '❌ Disabled'}")
    print(f"   Cache: ✅ Enabled (max {MAX_CACHE_SIZE} entries)")
    print(f"   PM2.5 Logging: ✅ Enabled (logs/pm25_values.log)")
    print(f"   Architecture: ✅ Modular")
    print("=" * 70 + "\n")

    return app


# ==================== MAIN ====================
if __name__ == '__main__':
    app = create_app()
    
    port = int(os.getenv('PORT', 5001))

    logger.info(f"\n{'='*70}")
    logger.info(f"🚀 Starting PM2.5 API (NO AQI)")
    logger.info(f"   URL: http://0.0.0.0:{port}")
    logger.info(f"   PM2.5 Logs: logs/pm25_values.log")
    logger.info(f"{'='*70}\n")

    # For development only
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)