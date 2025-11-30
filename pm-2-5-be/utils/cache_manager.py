"""
Cache management system
"""
import time
import hashlib
from typing import Optional
from utils.logger import main_logger as logger

class CacheManager:
    """Advanced cache manager with TTL and LRU eviction."""

    def __init__(self, max_size: int = 2000):
        self.cache = {}
        self.timestamps = {}
        self.access_count = {}
        self.max_size = max_size

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str, ttl: int) -> Optional[any]:
        """Get cached value if exists and not expired."""
        if key in self.cache:
            timestamp = self.timestamps.get(key, 0)
            if time.time() - timestamp < ttl:
                self.access_count[key] = self.access_count.get(key, 0) + 1
                logger.debug(f"✅ Cache HIT: {key[:20]}...")
                return self.cache[key]
            else:
                # Expired
                self._remove(key)
                logger.debug(f"⏰ Cache EXPIRED: {key[:20]}...")

        logger.debug(f"❌ Cache MISS: {key[:20]}...")
        return None

    def set(self, key: str, value: any):
        """Set cache value."""
        # Clean if too large
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.access_count[key] = 0

    def _remove(self, key: str):
        """Remove a cache entry."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.access_count.pop(key, None)

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find least accessed and oldest
        lru_key = min(self.timestamps.items(), 
                     key=lambda x: (self.access_count.get(x[0], 0), x[1]))[0]
        logger.debug(f"🗑️  Cache EVICT: {lru_key[:20]}...")
        self._remove(lru_key)

    def clear(self):
        """Clear all cache."""
        count = len(self.cache)
        self.cache.clear()
        self.timestamps.clear()
        self.access_count.clear()
        logger.info(f"🗑️  Cache cleared: {count} entries removed")

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": "N/A"
        }


class PredictionCache:
    """Cache for prediction results to reuse across endpoints."""

    def __init__(self, ttl: int = 1800):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl

    def _generate_key(self, year: int, month: int, day: int, 
                     hour: int, minute: int = 0) -> str:
        """Generate prediction cache key."""
        return f"pred_{year}_{month}_{day}_{hour}_{minute}"

    def get(self, year: int, month: int, day: int, 
           hour: int, minute: int = 0) -> Optional[dict]:
        """Get cached prediction result."""
        key = self._generate_key(year, month, day, hour, minute)

        if key in self.cache:
            timestamp = self.timestamps.get(key, 0)
            if time.time() - timestamp < self.ttl:
                logger.info(f"🎯 PREDICTION CACHE HIT for {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.timestamps[key]

        logger.info(f"❌ PREDICTION CACHE MISS for {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
        return None

    def set(self, year: int, month: int, day: int, 
           hour: int, minute: int, result: dict):
        """Set prediction result cache."""
        key = self._generate_key(year, month, day, hour, minute)
        self.cache[key] = result
        self.timestamps[key] = time.time()
        logger.info(f"💾 PREDICTION CACHED for {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")

    def clear(self):
        """Clear prediction cache."""
        count = len(self.cache)
        self.cache.clear()
        self.timestamps.clear()
        logger.info(f"🗑️  Prediction cache cleared: {count} entries removed")

    def stats(self) -> dict:
        """Get cache stats."""
        return {
            "size": len(self.cache),
            "ttl": self.ttl,
            "keys": list(self.cache.keys())
        }