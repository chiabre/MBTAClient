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
        requests_per_stats_report: Optional[int] = 0,
        logger: Optional[logging.Logger] = None
    ):
        self._max_cache_size = max_cache_size
        self._cache = OrderedDict()  # Use OrderedDict for LRU behavior
        self._logger = logger or logging.getLogger(__name__)
        self.cache_stats = None
        if requests_per_stats_report > 0:
            self.cache_stats = MBTACacheManagerStats(
                max_cache_size=max_cache_size,
                requests_per_stats_report=requests_per_stats_report,
                logger=logger
            )

        self._logger.debug("MBTACacheManager initialized with max_cache_size=%d", self._max_cache_size)

    @staticmethod
    def generate_cache_key(path: str, params: Optional[Dict[str, Any]]) -> str:
        """Generate a unique cache key based on the path and parameters."""
        try:
            key_data = {"path": path, "params": params or {}}
            return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        except Exception as e:
            _LOGGER.error("Failed to generate cache key: %s", e, exc_info=True)
            return ""

    def _enforce_cache_size(self) -> None:
        """Ensure the cache does not exceed the maximum size."""
        try:
            while len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)  # Remove the oldest item (FIFO)
                if self.cache_stats:
                    self.cache_stats.increase_counter(CacheEvent.EVICTION)
        except Exception as e:
            self._logger.error("Error enforcing cache size: %s", e, exc_info=True)

    def cleanup(self):
        """Clear all cached data."""
        self._logger.debug("Cleaning up MBTACacheManager resources")
        try:
            if self.cache_stats:
                self.cache_stats.print_stats()
            self._cache.clear()
        except Exception as e:
            self._logger.error("Error during cache cleanup: %s", e, exc_info=True)

    def get_cached_data(
        self, path: str, 
        params: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[Any], Optional[float], Optional[str]]:
        """Retrieve cached data from the server-side cache."""
        try:
            key = self.generate_cache_key(path, params)
            cached_entry = self._cache.get(key)
            if cached_entry:
                self._cache.move_to_end(key, last=True)  # Move accessed item to the end (LRU)
                return cached_entry["data"], cached_entry["timestamp"], cached_entry["last_modified"]
        except Exception as e:
            self._logger.error("Error retrieving cached data: %s", e, exc_info=True)
        return None, None, None

    def update_cache(
        self,
        path: str,
        params: Optional[Dict[str, Any]],
        data: Any,
        last_modified: Optional[str] = None
    ) -> float:
        """Update the server-side cache with data."""
        try:
            key = self.generate_cache_key(path, params)
            timestamp = int(time.time())
            self._cache[key] = {
                "data": data,
                "timestamp": timestamp,
                "last_modified": last_modified
            }
            self._enforce_cache_size()
            if self.cache_stats:
                self.cache_stats.increase_counter(CacheEvent.UPDATE, cache_size=len(self._cache))
            return timestamp
        
        except Exception as e:
            self._logger.error("Error updating cache: %s", e, exc_info=True)
            return 0.0

class MBTACacheManagerStats:

    DEFAULT_REQUESTS_PER_STATS_REPORT = 1000

    def __init__(
        self,
        max_cache_size: int,
        requests_per_stats_report: Optional[int] = DEFAULT_REQUESTS_PER_STATS_REPORT,
        logger: Optional[logging.Logger] = None,
    ):
        self.requests_per_stats_report = requests_per_stats_report
        self.max_cache_size = max_cache_size
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._entries = 0
        self._logger = logger or logging.getLogger(__name__)

    @property
    def _requests(self) -> Optional[int]:
        return self._hits + self._misses

    def increase_counter(self, cache_event: CacheEvent, cache_size: Optional[int] = None):
        """Increase cache event counters and log stats periodically."""
        try:
            if cache_event == CacheEvent.HIT:
                self._hits += 1
            elif cache_event == CacheEvent.MISS:
                self._misses += 1
            elif cache_event == CacheEvent.UPDATE:
                self._entries = cache_size
            elif cache_event == CacheEvent.EVICTION:
                self._evictions += 1
                self._entries = max(0, self._entries - 1)

            if cache_event in [CacheEvent.HIT, CacheEvent.MISS] and self._requests > 0 and self._requests % self.requests_per_stats_report == 0:
                self.print_stats()
        except Exception as e:
            self._logger.error("Error increasing counter for event %s: %s", cache_event, e, exc_info=True)

    def print_stats(self):
        """Print cache statistics."""
        try:
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
            self._logger.info("%s %d%% hit rate (%d/%d)", self._generate_bar(hit_rate), hit_rate, self._hits, self._requests)
            self._logger.info("%s %d%% usage (%d/%d)", self._generate_bar(usage), usage, self._entries, self.max_cache_size)
            if self._evictions > 0:
                self._logger.info("%d evictions", self._evictions)
        except Exception as e:
            self._logger.error("Error printing cache stats: %s", e, exc_info=True)

    def _generate_bar(self, percentage: int) -> str:
        """Generate a visual bar representation of a percentage."""
        try:
            bar_length = 10
            filled_length = max(0, min(bar_length, int((percentage / 100) * bar_length)))
            bar_content = "█" * filled_length + "░" * (bar_length - filled_length)
            return f"|{bar_content}|"
        except Exception as e:
            self._logger.error("Error generating bar: %s", e, exc_info=True)
            return "|░░░░░░░░░░|"
