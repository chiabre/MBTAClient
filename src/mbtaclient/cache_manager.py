import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json
from functools import wraps

_LOGGER = logging.getLogger(__name__)

DEFAULT_SERVER_CACHE_TTL = 86400  # 24 hours
DEFAULT_CLIENT_CACHE_EXPIRATION_HOUR = 3  # 3 AM

class CacheManager:
    """
    Manages caching with distinct expiration policies for server-side and client-side caches.
    """

    def __init__(
        self, 
        server_cache_ttl=DEFAULT_SERVER_CACHE_TTL, 
        client_cache_hour=DEFAULT_CLIENT_CACHE_EXPIRATION_HOUR,
        logger: logging.Logger = None
    ):
        self.server_cache_ttl = server_cache_ttl
        self.client_cache_hour = client_cache_hour
        self._server_cache = {}
        self._client_cache = {}
        self._logger = logger or logging.getLogger(__name__)
        _LOGGER.debug("CacheManager initialized with server_cache_ttl=%s, client_cache_hour=%s", 
                     server_cache_ttl, client_cache_hour)

    @staticmethod
    def generate_cache_key(path: str, params: Optional[Dict[str, Any]]) -> str:
        """Generate a unique cache key based on the path and parameters."""
        key_data = {"path": path, "params": params or {}}
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _is_server_cache_entry_valid(self, entry: dict) -> bool:
        """Check if a server cache entry is still valid based on TTL."""
        if "last_modified" in entry:
            return (time.time() - entry["timestamp"]) < self.server_cache_ttl
        return False

    def _is_client_cache_entry_valid(self, entry: dict) -> bool:
        """Check if a client cache entry is valid based on expiration time."""
        now = datetime.now()
        expiration_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=self.client_cache_hour)
        if now >= expiration_time:
            expiration_time += timedelta(days=1)
        return entry["timestamp"] < expiration_time.timestamp()

    def get_cached_server_data(self, path: str, params: Optional[Dict[str, Any]]) -> Optional[Any]:
        """Retrieve cached data from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._server_cache.get(key)
        if cached_entry:
            if self._is_server_cache_entry_valid(cached_entry):
                _LOGGER.debug("Server cache hit")
                return cached_entry["data"]
            del self._server_cache[key]
            _LOGGER.debug("Evicted expired server cache entry")
        else:
            _LOGGER.debug("Server cache miss")
        return None

    def update_server_cache(self, path: str, params: Optional[Dict[str, Any]], data: Any, last_modified: Optional[str] = None):
        """Update the server-side cache with data."""
        key = self.generate_cache_key(path, params)
        self._server_cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "last_modified": last_modified
        }

    def get_last_modified(self, path: str, params: Optional[Dict[str, Any]]):
        """Retrieve the 'Last-Modified' header from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._server_cache.get(key)
        if cached_entry and "last_modified" in cached_entry:
            return cached_entry["last_modified"]
        return None

    def get_cached_client_data(self, key) -> Optional[Any]:
        """Retrieve cached data from the client-side cache."""
        cached_entry = self._client_cache.get(key)
        if cached_entry:
            if self._is_client_cache_entry_valid(cached_entry):
                _LOGGER.debug("Client cache hit")
                return cached_entry["data"]
            del self._client_cache[key]
            _LOGGER.debug("Evicted expired client cache")
        else:
            _LOGGER.debug("Client cache miss")
        return None

    def update_client_cache(self, key, data: Any):
        """Update the client-side cache with data."""
        self._client_cache[key] = {"data": data, "timestamp": time.time()}
        

def memoize_async():
    """
    Asynchronous memoization decorator for methods with optional expiration policies.

    Assumes the decorated method belongs to a class with an attribute '_cache_manager'.

    Returns:
        A decorator function.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache_manager'):
                raise AttributeError(f"{self.__class__.__name__} does not have an attribute '_cache_manager'")
            
            cache_manager = self._cache_manager
            key = cache_manager.generate_cache_key(func.__name__, {"args": args, "kwargs": kwargs})

            # Attempt to retrieve cached data
            cached_data = cache_manager.get_cached_client_data(key)
            if cached_data:
                return cached_data
            
            result = await func(self, *args, **kwargs)

            # Update the cache with the result
            cache_manager.update_client_cache(key, result)

            return result

        return wrapper
    return decorator
