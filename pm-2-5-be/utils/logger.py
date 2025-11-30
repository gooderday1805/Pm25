"""
Logging utilities for PM2.5 API
"""
import logging
from datetime import datetime
from config.settings import LOG_FILE_MAIN, LOG_FILE_PM25, LOG_LEVEL, LOG_FORMAT, TZ_VN

# ==================== MAIN LOGGER ====================
def setup_main_logger():
    """Setup main application logger."""
    logger = logging.getLogger('pm25_api')
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE_MAIN, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ==================== PM2.5 VALUES LOGGER ====================
class PM25Logger:
    """Special logger for tracking PM2.5 values through the prediction pipeline."""
    
    def __init__(self):
        self.logger = logging.getLogger('pm25_values')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()
        
        # Dedicated file for PM2.5 values
        handler = logging.FileHandler(LOG_FILE_PM25, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(message)s'
        ))
        self.logger.addHandler(handler)
        
        # Also log to console for debugging
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('🔍 %(message)s'))
        self.logger.addHandler(console)
    
    def log_request(self, district_id: int, district_name: str, year: int, month: int, 
                   day: int, hour: int, minute: int):
        """Log prediction request."""
        timestamp = datetime.now(TZ_VN).strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info(
            f"REQUEST | District: {district_name} (ID: {district_id}) | "
            f"Target: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} | "
            f"Time: {timestamp}"
        )
    
    def log_raw_pm25(self, district_name: str, timestamp: str, 
                     pm25_t2: float, pm25_t1: float, pm25_t0: float):
        """Log raw PM2.5 values from API (t-2, t-1, t-0)."""
        self.logger.info(
            f"PM25_RAW | {district_name} | {timestamp} | "
            f"t-2: {pm25_t2:.2f} | t-1: {pm25_t1:.2f} | t-0: {pm25_t0:.2f}"
        )
    
    def log_features(self, district_name: str, features_dict: dict):
        """Log key engineered features."""
        pm25_lag1 = features_dict.get('pm2_5_lag_1', 'N/A')
        pm25_lag2 = features_dict.get('pm2_5_lag_2', 'N/A')
        pm25_roll_avg = features_dict.get('pm2_5_roll_avg_3hr', 'N/A')
        pm25_diff = features_dict.get('pm2_5_diff_1hr', 'N/A')
        
        self.logger.info(
            f"PM25_FEATURES | {district_name} | "
            f"lag1: {pm25_lag1:.2f} | lag2: {pm25_lag2:.2f} | "
            f"roll_avg_3hr: {pm25_roll_avg:.2f} | diff_1hr: {pm25_diff:.2f}"
        )
    
    def log_prediction(self, district_name: str, predicted_pm25: float, 
                      actual_pm25_t0: float):
        """Log final prediction vs actual current PM2.5."""
        diff = predicted_pm25 - actual_pm25_t0
        diff_percent = (diff / actual_pm25_t0 * 100) if actual_pm25_t0 > 0 else 0
        
        self.logger.info(
            f"PM25_PREDICTION | {district_name} | "
            f"Predicted: {predicted_pm25:.2f} | Actual(t-0): {actual_pm25_t0:.2f} | "
            f"Diff: {diff:+.2f} ({diff_percent:+.1f}%)"
        )
    
    def log_error(self, district_name: str, error: str):
        """Log prediction error."""
        self.logger.error(
            f"PM25_ERROR | {district_name} | {error}"
        )
    
    def log_summary(self, total: int, success: int, failed: int, 
                   avg_pm25: float, execution_time: float):
        """Log batch prediction summary."""
        self.logger.info(
            f"PM25_SUMMARY | Total: {total} | Success: {success} | Failed: {failed} | "
            f"Avg PM2.5: {avg_pm25:.2f} | Time: {execution_time:.2f}s"
        )

# Create global loggers
main_logger = setup_main_logger()
pm25_logger = PM25Logger()