from datetime import datetime
from typing import Optional

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
