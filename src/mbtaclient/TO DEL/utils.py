from datetime import datetime, timedelta
from typing import Optional
import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MBTAUtils:
        
    ROUTE_TYPES= {
        # 0: 'Light Rail',   # Example: Green Line
        # 1: 'Heavy Rail',   # Example: Red Line
        0: 'Subway (Light Rail)',   
        1: 'Subway (Heavy Rail)',  
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
    def time_to(time: Optional[datetime], now: datetime) -> Optional[int]:
        if time is None:
            logger.warning("time_to: Provided 'time' is None.")
            return None
        # Check if both datetime objects have timezone info
        if time.tzinfo != now.tzinfo:
            # Make both datetimes the same type: either both naive or both aware
            if time.tzinfo is None and now.tzinfo is not None:
                # Convert time to aware by using the timezone of `now`
                time = time.replace(tzinfo=now.tzinfo)
            elif time.tzinfo is not None and now.tzinfo is None:
                # Convert now to naive by stripping timezone info
                now = now.replace(tzinfo=None)
        # Now perform the calculation
        return int(round((time - now).total_seconds(),0))

    @staticmethod
    def calculate_time_difference(real_time: Optional[datetime], time: Optional[datetime]) -> Optional[int]:
        if real_time is None or time is None:
            return None
        return int(round((real_time - time).total_seconds(),0))

    @staticmethod
    def parse_datetime(time_str: str) -> Optional[datetime]:
        """Parse a string in ISO 8601 format to a datetime object."""
        if not isinstance(time_str, str):
            return None
        try:
            return datetime.fromisoformat(time_str)
        except ValueError as e:
            logger.error(f"Error parsing datetime string: {e}")
            return None


from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)