import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import hashlib
import json
from functools import wraps

_LOGGER = logging.getLogger(__name__)

DEFAULT_MAX_CACHE_SIZE = 256

class MBTACacheManager:
    """
    Manages caching with distinct expiration policies for server-side and client-side caches.
    """

    def __init__(
        self,  
        max_cache_size: Optional[int] = DEFAULT_MAX_CACHE_SIZE, 
        logger: Optional[logging.Logger] = None
    ):
        self._max_cache_size = max_cache_size
        self._server_cache = {}
        self._client_cache = {}
        self._logger = logger or logging.getLogger(__name__)
        ###
        self._client_cache_hit = 0
        self._client_cache_miss = 0
        self._client_cache_eviction = 0
        self.server_cache_hit = 0
        self.server_cache_miss = 0
        self._server_cache_eviction = 0
        ###
        self._logger.debug("MBTACacheManager initialized")

    @staticmethod
    def generate_cache_key(path: str, params: Optional[Dict[str, Any]]) -> str:
        """Generate a unique cache key based on the path and parameters."""
        key_data = {"path": path, "params": params or {}}
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _enforce_cache_size(self, cache: dict) -> None:
        """Ensure the cache does not exceed the maximum size."""
        while len(cache) > self._max_cache_size:
            oldest_key = min(cache, key=lambda k: cache[k]["timestamp"])
            del cache[oldest_key]
            if cache is self._server_cache:
                self._server_cache_eviction += 1
            self._client_cache_eviction += 1

                
    def _is_client_cache_entry_valid(self, entry: dict) -> bool:
        """Check if a client cache entry is valid based on expiration time."""
        now = datetime.now()
        expiration_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=3)
        if now >= expiration_time:
            expiration_time += timedelta(days=1)
        return entry["timestamp"] < expiration_time.timestamp()

    def get_cached_server_data(self, path: str, params: Optional[Dict[str, Any]]) -> Tuple[Optional[Any],Optional[float]]:
        """Retrieve cached data from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._server_cache.get(key)
        if cached_entry:
            return cached_entry["data"], cached_entry["timestamp"]
        return None, None

    def update_server_cache(self, path: str, params: Optional[Dict[str, Any]], data: Any, last_modified: Optional[str] = None) -> float:
        """Update the server-side cache with data."""
        key = self.generate_cache_key(path, params)
        timestamp = time.time()
        self._server_cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "last_modified": last_modified
        }
        self._enforce_cache_size(self._server_cache)
        return timestamp

    def get_last_modified(self, path: str, params: Optional[Dict[str, Any]]) -> Optional[str]:
        """Retrieve the 'Last-Modified' header from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._server_cache.get(key)
        if cached_entry and "last_modified" in cached_entry:
            return cached_entry["last_modified"]
        return None

    def get_cached_client_data(self, key) -> Tuple[Optional[Any],Optional[float]]:
        """Retrieve cached data from the client-side cache."""
        cached_entry = self._client_cache.get(key)
        if cached_entry:
            if self._is_client_cache_entry_valid(cached_entry):
                self._client_cache_hit += 1
                return cached_entry["data"], cached_entry["timestamp"] 
            del self._client_cache[key]
        self._client_cache_miss += 1
        return None, None

    def update_client_cache(self, key, data: Any, timestamp: float) -> None:
        """Update the client-side cache with data."""
        self._client_cache[key] = {
            "data": data, 
            "timestamp": timestamp
            }
        
    def print_stats(self):
        self._logger.info("MBTACaches stats:")
        client_cache_access = self._client_cache_hit + self._client_cache_miss
        if client_cache_access > 0:
            client_cache_hit_rate = int(round((self._client_cache_hit/client_cache_access)*100,0))
            self._logger.info(f"Client cache: {client_cache_access} acccess, {client_cache_hit_rate}% hit rate, {self._client_cache_eviction} evictions ")
        server_cache_access = self.server_cache_hit + self.server_cache_miss
        if server_cache_access > 0:
            server_cache_hit_rate = int(round((self.server_cache_hit/server_cache_access)*100,0))
            self._logger.info(f"Server cache: {server_cache_access} acccess, {server_cache_hit_rate}% hit rate, {self._server_cache_eviction} evictions ")  
        total_cache_access = client_cache_access + server_cache_access
        if total_cache_access > 0:
            total_cache_hit = self._client_cache_hit + self.server_cache_hit
            total_cache_hit_rate = int(round((total_cache_hit/total_cache_access)*100,0))
            tota_cache_evictions = self._client_cache_eviction + self._server_cache_eviction
            self._logger.info(f"Cache: {total_cache_access} total acccess, {total_cache_hit_rate}% hit rate, {tota_cache_evictions} total evictions ")  

    
    def cleanup(self):
        """Clear all cached data."""
        self._logger.debug("Cleaning up MBTACacheManager resources")
        self.print_stats()
        self._server_cache.clear()
        self._client_cache.clear()
        if self._logger:
            self._logger.debug("All cache entries have been cleared.")

def memoize_async_mbta_client_cache():
    """
    Asynchronous memoization decorator for methods with optional expiration policies.

    Assumes the decorated method belongs to a class with an attribute '_cache_manager'.

    Returns:
        A decorator function.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Tuple[Any,float]:
            if not hasattr(self, '_cache_manager'):
                raise AttributeError(f"{self.__class__.__name__} does not have an attribute '_cache_manager'")
            
            cache_manager = self._cache_manager
            key = cache_manager.generate_cache_key(func.__name__, {"args": args, "kwargs": kwargs})

            # Attempt to retrieve cached data
            cached_data, timestamp = cache_manager.get_cached_client_data(key)
            # if cached data, return the data and its timestamp
            if cached_data:
                return cached_data, timestamp
            # if not, fetch the data (new data may be either fresh or from server cache)
            data, timestamp = await func(self, *args, **kwargs)

            # Update the cached data and its timestamp
            cache_manager.update_client_cache(key, data, timestamp)

            return data, timestamp

        return wrapper
    return decorator
