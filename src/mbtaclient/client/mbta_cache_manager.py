from enum import Enum
import logging
import time
from typing import Optional, Dict, Any, Tuple
import hashlib
import json
from collections import OrderedDict

_LOGGER = logging.getLogger(__name__)

class CacheEvent(Enum):
    HIT = "hit"
    MISS = "miss"
    EVICTION = "eviction"
    UPDATE = "update"

class MBTACacheManager:
    """
    Manages caching with expiration policies for server-side cache.
    """

    DEFAULT_MAX_CACHE_SIZE = 512

    def __init__(
        self,
        max_cache_size: Optional[int] = DEFAULT_MAX_CACHE_SIZE,
        stats: Optional[bool] = True,
        stats_interval: Optional[int] = None,
        logger: Optional[logging.Logger] = None
    ):
        self._max_cache_size = max_cache_size
        self._cache = OrderedDict()  # Use OrderedDict for LRU behavior
        self._logger = logger or logging.getLogger(__name__)
        self.stats = stats
        if stats:
            self.cache_stats = MBTACacheManagerStats(
                max_cache_size=max_cache_size, 
                stats_interval=stats_interval or None,
                logger=logger )
        self._logger.debug("MBTACacheManager initialized")

    @staticmethod
    def generate_cache_key(path: str, params: Optional[Dict[str, Any]]) -> str:
        """Generate a unique cache key based on the path and parameters."""
        key_data = {"path": path, "params": params or {}}
        return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _enforce_cache_size(self) -> None:
        """Ensure the cache does not exceed the maximum size."""
        while len(self._cache) > self._max_cache_size:
            self._cache.popitem(last=False)  # Remove the oldest item (FIFO)
            if self.stats:
                self.cache_stats.increase_counter(CacheEvent.EVICTION)

    def cleanup(self):
        """Clear all cached data."""
        self._logger.debug("Cleaning up MBTACacheManager resources")
        self.cache_stats.print_stats()
        self._cache.clear()

    def get_cached_data(
        self, path: str, 
        params: Optional[Dict[str, Any]]) -> Tuple[Optional[Any],Optional[float],Optional[str]]:
        """Retrieve cached data from the server-side cache."""
        key = self.generate_cache_key(path, params)
        cached_entry = self._cache.get(key)
        if cached_entry:
            if self._is_cache_entry_valid(cached_entry):
                self._cache.move_to_end(key, last=True)  # Move accessed item to the end (LRU)
                return cached_entry["data"], cached_entry["timestamp"], cached_entry["last_modified"]
            else:
                del self._cache[key]
                if self.stats:
                    self.cache_stats.increase_counter(CacheEvent.EVICTION)
        return None, None, None

    def update_cache(
        self,
        path: str,
        params: Optional[Dict[str, Any]],
        data: Any, 
        last_modified: Optional[str] = None) -> float:
        """Update the server-side cache with data."""
        key = self.generate_cache_key(path, params)
        timestamp = time.time()
        self._cache[key] = {
            "data": data,
            "timestamp": timestamp,
            "last_modified": last_modified
        }
        self._enforce_cache_size()
        if self.stats:
            self.cache_stats.increase_counter(CacheEvent.UPDATE,cache_size=len(self._cache))
        return timestamp

    def _is_cache_entry_valid(self, cached_entry: Dict) -> bool:
        """Check if the cache entry is valid."""
        # You can add custom logic here, e.g., check for expiration time
        return True

class MBTACacheManagerStats:

    DEFAULT_STAS_INTERVAL = 1000

    def __init__(
        self,
        max_cache_size: int,
        stats_interval: Optional[int] = DEFAULT_STAS_INTERVAL,
        logger: Optional[logging.Logger] = None,
    ):
        self.stats_interval = stats_interval or self.DEFAULT_STAS_INTERVAL
        self.max_cache_size = max_cache_size
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._entries  = 0
        self._logger = logger or logging.getLogger(__name__)

    @property
    def _requests(self) -> Optional[int]:
        return self._hits + self._misses

    def increase_counter(self, cache_event: CacheEvent, cache_size: Optional[int]= None):

        if cache_event == CacheEvent.HIT:
            self._hits += 1
        elif cache_event == CacheEvent.MISS:
            self._misses += 1
        elif cache_event == CacheEvent.UPDATE:
            self._entries = cache_size
        elif cache_event == CacheEvent.EVICTION:
            self._evictions += 1
            self._entries = max(0, self._entries - 1)

        if self.stats_interval != 0 and cache_event in [CacheEvent.HIT,CacheEvent.MISS] and self._requests > 0 and self._requests % self.stats_interval == 0:
            self.print_stats()

    def print_stats(self):

        hit_rate = (
            int((self._hits / self._requests) * 100)
            if self._requests > 0
            else 0
        )
        usage = (
            int((self._entries / self.max_cache_size) * 100)
            if self.max_cache_size > 0
            else 0
        )
        self._logger.info("MBTA Cache Stats:")
        self._logger.info(f"{self._generate_bar(hit_rate)} {hit_rate}% hit rate ({self._hits}/{self._requests})")        
        self._logger.info(f"{self._generate_bar(usage)} {usage}% usage ({self._entries}/{self.max_cache_size})")
        if self._evictions >0:
            self._logger.info(f"{self._evictions} evictions")

    def _generate_bar(self, percentage):
        bar_length = 10
        filled_length = max(0, min(bar_length, int((percentage / 100) * bar_length)))
        bar_content = "█" * filled_length + "░" * (bar_length - filled_length)
        return f"|{bar_content}|"
