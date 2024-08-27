from datetime import datetime, timedelta

from typing import Optional
from collections.abc import Hashable
import logging

# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


class MBTAUtils:
        
    ROUTE_TYPES= {
        # 0: 'Light Rail',   # Example: Green Line
        # 1: 'Heavy Rail',   # Example: Red Line
        0: 'Subway',   
        1: 'Subway',  
        2: 'Commuter Rail',
        3: 'Bus',
        4: 'Ferry'
    }

    UNCERTAINTY = {
        '60': 'Trip that has already started',
        '120': 'Trip not started and a vehicle is awaiting departure at the origin',
        '300': 'Vehicle has not yet been assigned to the trip',
        '301': 'Vehicle appears to be stalled or significantly delayed',
        '360': 'Trip not started and a vehicle is completing a previous trip'
    }
           
    @staticmethod
    def get_route_type_desc_by_type_id(route_type: int) -> str:
        """Get a description of the route type."""
        return MBTAUtils.ROUTE_TYPES.get(route_type, 'Unknown')
    
    @staticmethod
    def get_uncertainty_description(key: str) -> str:
        return MBTAUtils.UNCERTAINTY.get(key, 'None')
    
    @staticmethod
    def time_to(time: Optional[datetime], now: datetime) -> Optional[float]:
        if time is None:
            return None
        return (time - now).total_seconds()

    @staticmethod
    def calculate_time_difference(real_time: Optional[datetime], time: Optional[datetime]) -> Optional[float]:
        if real_time is None or time is None:
            return None
        return (real_time - time).total_seconds()

    @staticmethod
    def parse_datetime(time_str: str) -> Optional[datetime]:
        """Parse a string in ISO 8601 format to a datetime object."""
        if not isinstance(time_str, str):
            return None
        return datetime.fromisoformat(time_str)
    


from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def memoize_async(expire_at_end_of_day=False):
    def decorator(func):
        cache = {}

        def make_hashable(item):
            if isinstance(item, dict):
                # Exclude the 'filter[min_time]' key from the dictionary
                item = {k: v for k, v in item.items() if k != 'filter[min_time]'}
                return frozenset((make_hashable(k), make_hashable(v)) for k, v in item.items())
            return str(item)  # Convert non-dict items to string

        async def wrapper(*args):
            current_time = datetime.now()
            cache_key = tuple(make_hashable(arg) for arg in args)

            if cache_key in cache:
                cached_result, timestamp = cache[cache_key]

                if expire_at_end_of_day:
                    if timestamp.date() == current_time.date():
                        _LOGGER.debug(f"Cache hit for {func.__name__} with arguments {cache_key} at {current_time}")
                        return cached_result
                else:  # Expiration based on 30 days
                    if current_time - timestamp < timedelta(days=30):
                        _LOGGER.debug(f"Cache hit for {func.__name__} with arguments {cache_key} at {current_time}")
                        return cached_result

            _LOGGER.debug(f"Cache miss for {func.__name__} with arguments {cache_key} at {current_time}")
            result = await func(*args)
            cache[cache_key] = (result, current_time)
            _LOGGER.debug(f"Cache updated for key: {cache_key} at {current_time}")
            return result

        return wrapper
    return decorator
