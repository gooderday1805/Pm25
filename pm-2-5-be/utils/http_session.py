"""
HTTP session with retry mechanism
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config.settings import MAX_RETRIES, BACKOFF_FACTOR, MAX_WORKERS

def create_session_with_retry() -> requests.Session:
    """Create HTTP session with retry mechanism and connection pooling."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=MAX_WORKERS * 2,
        pool_maxsize=MAX_WORKERS * 4
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Global HTTP session
http_session = create_session_with_retry()