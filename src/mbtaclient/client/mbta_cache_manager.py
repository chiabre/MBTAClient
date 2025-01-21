from enum import Enum
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import hashlib
import json
from functools import wraps

_LOGGER = logging.getLogger(__name__)

DEFAULT_MAX_CACHE_SIZE = 128
DEFAULT_STAS_INTERVAL = 100

class CacheType(Enum):
    CLIENT = "client"
    SERVER = "server"
    
class CacheEvent(Enum):
    HIT = "client"
    MISS = "server" 
    EVICTION = "eviction"
    UPDATE = "update"   

class MBTACacheManager:
    """
    Manages caching with distinct expiration policies for server-side and client-side caches.
    """

    def __init__(
        self,  
        max_cache_size: Optional[int] = DEFAULT_MAX_CACHE_SIZE, 
        stats: Optional[bool] = True,
        stats_interval: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ):
        self._max_cache_size = max_cache_size
        self._server_cache = {}
        self._client_cache = {}
        self._logger = logger or logging.getLogger(__name__)
        self.stats = stats
        if stats:
            self.cache_stats = MBTACacheManagerStats(max_cache_size=max_cache_size, stats_interval=stats_interval or DEFAULT_STAS_INTERVAL,logger=logger )

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
            if self.stats:
                if cache is self._server_cache:
                    self.cache_stats.increase_counter(CacheType.SERVER,CacheEvent.EVICTION)
                elif cache is self._client_cache:
                    self.cache_stats.increase_counter(CacheType.CLIENT,CacheEvent.EVICTION)

    def cleanup(self):
        """Clear all cached data."""
        self._logger.debug("Cleaning up MBTACacheManager resources")
        self.cache_stats.print_stats()
        self._server_cache.clear()
        self._client_cache.clear()
        if self._logger:
            self._logger.debug("All cache entries have been cleared.")
            
    ## CLIENT            
    def _is_client_cache_entry_valid(self, entry: dict) -> bool:
        """Check if a client cache entry is valid based on expiration time."""
        now = datetime.now()
        expiration_time = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=3)
        if now >= expiration_time:
            expiration_time += timedelta(days=1)
        return entry["timestamp"] < expiration_time.timestamp()
    
    
    def get_client_cache_data(self, key) -> Tuple[Optional[Any],Optional[float]]:
        """Retrieve cached data from the client-side cache."""
        cached_entry = self._client_cache.get(key)
        if cached_entry:
            if self._is_client_cache_entry_valid(cached_entry):
                if self.stats:
                    self.cache_stats.increase_counter(CacheType.CLIENT,CacheEvent.HIT)
                return cached_entry["data"], cached_entry["timestamp"] 
            else: 
                del self._client_cache[key]
                if self.stats:
                    self.cache_stats.increase_counter(CacheType.CLIENT,CacheEvent.EVICTION)
        if self.stats:
            self.cache_stats.increase_counter(CacheType.CLIENT,CacheEvent.MISS)
        return None, None
    
    def update_client_cache(self, key, data: Any, timestamp: float) -> None:
        """Update the client-side cache with data."""
        self._enforce_cache_size(self._client_cache)
        self._client_cache[key] = {
            "data": data, 
            "timestamp": timestamp
            }
        if self.stats:
            self.cache_stats.increase_counter(CacheType.CLIENT,CacheEvent.UPDATE,cache_size=len(self._client_cache))
        

    ## SERVER
    def get_server_cache_data(self, path: str, params: Optional[Dict[str, Any]]) -> Tuple[Optional[Any],Optional[float],Optional[str]]:
        """Retrieve cached data from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._server_cache.get(key)
        if cached_entry:
            return cached_entry["data"], cached_entry["timestamp"], cached_entry ["last_modified"]
        return None, None, None

    def update_server_cache(self, path: str, params: Optional[Dict[str, Any]], data: Any, last_modified: Optional[str] = None) -> float:
        """Update the server-side cache with data."""
        key = self.generate_cache_key(path, params)
        timestamp = time.time()
        self._enforce_cache_size(self._server_cache)
        self._server_cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "last_modified": last_modified
        }
        if self.stats:
            self.cache_stats.increase_counter(CacheType.SERVER,CacheEvent.UPDATE,cache_size=len(self._server_cache))
        return timestamp

    # def get_last_modified(self, path: str, params: Optional[Dict[str, Any]]) -> Optional[str]:
    #     """Retrieve the 'Last-Modified' header from the server-side cache."""
    #     key = self.generate_cache_key(path, params)
    #     cached_entry = self._server_cache.get(key)
    #     if cached_entry and "last_modified" in cached_entry:
    #         return cached_entry["last_modified"]
    #     return None

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
            cached_data, timestamp = cache_manager.get_client_cache_data(key)
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


class MBTACacheManagerStats:
    def __init__(
        self,
        max_cache_size: int,
        stats_interval: Optional[int] = DEFAULT_STAS_INTERVAL,
        logger: Optional[logging.Logger] = None,
    ):
        self._stats_interval = stats_interval or DEFAULT_STAS_INTERVAL
        self._max_cache_size = max_cache_size
        self._client_cache_hit = 0
        self._client_cache_miss = 0
        self._client_cache_eviction = 0
        self._client_cache_entry = 0
        self._server_cache_hit = 0
        self._server_cache_miss = 0
        self._server_cache_eviction = 0
        self._server_cache_entry  = 0
        self._logger = logger or logging.getLogger(__name__)

    def increase_counter(self, cache_type: CacheType, cache_event: CacheEvent, cache_size: Optional[int]= None):
        if cache_type == CacheType.CLIENT:
            if cache_event == CacheEvent.HIT:
                self._client_cache_hit += 1
            elif cache_event == CacheEvent.MISS:
                self._client_cache_miss += 1
            elif cache_event == CacheEvent.UPDATE:  
                self._client_cache_entry = cache_size
            elif cache_event == CacheEvent.EVICTION:
                self._client_cache_eviction += 1
                self._client_cache_entry = max(0, self._client_cache_entry - 1)
        elif cache_type == CacheType.SERVER:
            if cache_event == CacheEvent.HIT:
                self._server_cache_hit += 1
            elif cache_event == CacheEvent.MISS:
                self._server_cache_miss += 1
            elif cache_event == CacheEvent.UPDATE:
                self._server_cache_entry = cache_size
            elif cache_event == CacheEvent.EVICTION:
                self._server_cache_eviction += 1
                self._server_cache_entry = max(0, self._server_cache_entry - 1)

        total_cache_access = (
            self._client_cache_hit + self._server_cache_hit + self._server_cache_miss
        )
        if total_cache_access > 0 and total_cache_access % self._stats_interval == 0:
            self.print_stats()

    def print_stats(self):
        total_cache_access = (
            self._client_cache_hit + self._server_cache_hit + self._server_cache_miss
        )
        if total_cache_access > 0:
            client_cache_hit_rate = (
                int((self._client_cache_hit / total_cache_access) * 100)
                if total_cache_access > 0
                else 0
            )
            server_cache_hit_rate = (
                int((self._server_cache_hit / total_cache_access) * 100)
                if total_cache_access > 0
                else 0
            )
            total_cache_hit_rate = (
                int(((self._client_cache_hit + self._server_cache_hit) / total_cache_access) * 100)
                if total_cache_access > 0
                else 0
            )
            total_cache_entry = self._client_cache_entry + self._server_cache_entry
            client_cache_usage = (
                int((self._client_cache_entry / self._max_cache_size) * 100)
                if self._max_cache_size > 0
                else 0
            )
            server_cache_usage = (
                int((self._server_cache_entry / self._max_cache_size) * 100)
                if self._max_cache_size > 0
                else 0
            )
            total_cache_usage = (
                int((total_cache_entry / (self._max_cache_size * 2)) * 100)
                if self._max_cache_size > 0
                else 0
            )
            total_cache_evictions = (
                self._client_cache_eviction + self._server_cache_eviction
            )

            self._logger.info(f"MBTA Cache Stats @{total_cache_access} accesses:")
            self._logger.info(
                f"{self._generate_bar(total_cache_hit_rate)} {total_cache_hit_rate}% total cache hit rate"
            )
            self._logger.info(
                f"{self._generate_bar(client_cache_hit_rate)} {client_cache_hit_rate}% client cache hit rate"
            )
            self._logger.info(
                f"{self._generate_bar(server_cache_hit_rate)} {server_cache_hit_rate}% server cache hit rate"
            )
            self._logger.info(f"{total_cache_entry} total cache entries ({self._client_cache_entry} client + {self._server_cache_entry} server) ")
            self._logger.info(
                f"{self._generate_bar(total_cache_usage)} {total_cache_usage}% total cache usage ({total_cache_evictions} total evictions)"
            )
            self._logger.info(
                f"{self._generate_bar(client_cache_usage)} {client_cache_usage}% client cache usage ({self._client_cache_eviction} evictions)"
            )
            self._logger.info(
                f"{self._generate_bar(server_cache_usage)} {server_cache_usage}% server cache usage ({self._server_cache_eviction} evictions)"
            )

    def _generate_bar(self, percentage):
        bar_length = 10
        filled_length = max(0, min(bar_length, int((percentage / 100) * bar_length)))
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        return f"|{bar}|"
