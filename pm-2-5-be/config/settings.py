"""
Configuration settings for PM2.5 Prediction API
"""
import os
import pytz

# ==================== TIMEZONE ====================
TZ_VN = pytz.timezone('Asia/Ho_Chi_Minh')

# ==================== PATHS ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best_pm25_model_20251025_214649.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'models', 'pm25_scaler_20251025_214649.pkl')
JSON_PATH = os.path.join(BASE_DIR, 'models', 'pm25_model_summary_20251025_214649.json')
DISTRICTS_PATH = os.path.join(BASE_DIR, 'config', 'districts.json')

# ==================== API SETTINGS ====================
DEFAULT_API_KEY = "0da082531276d74b1118047941f103c3"
MAX_WORKERS = 10

# ==================== CACHE SETTINGS ====================
CACHE_TTL_WEATHER = 3600       # 1 hour for weather data
CACHE_TTL_AIR = 1800            # 30 minutes for air quality
CACHE_TTL_PREDICTION = 1800     # 30 minutes for prediction results
MAX_CACHE_SIZE = 2000

# ==================== HTTP SETTINGS ====================
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
TIMEOUT = 30

# ==================== LOGGING ====================
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_MAIN = os.path.join(LOG_DIR, 'pm25_api.log')
LOG_FILE_PM25 = os.path.join(LOG_DIR, 'pm25_values.log')
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'