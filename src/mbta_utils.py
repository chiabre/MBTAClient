from datetime import datetime
import logging
from typing import Optional

from mbta_stop import MBTAStop

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
    def get_stop_by_id(stops: list[MBTAStop], stop_id: str) -> Optional[MBTAStop]:
        """Retrieve a MBTAstop from the list of MBTAstop objects based on the stop ID."""
        for stop in stops:
            if stop.id == stop_id:
                return stop
        return None
    
    @staticmethod
    def get_stops_by_name(stops: list['MBTAStop'], stop_name: str) -> list['MBTAStop']:
        """Retrieve a list of MBTAstops from the list of MBTAstops based on the stop name."""
        matching_stops = [stop for stop in stops if stop.name.lower() == stop_name.lower()]
        return matching_stops

    @staticmethod
    def get_stop_ids_from_stops(stops: list[MBTAStop]) -> list[str]:
        """Extract all stop IDs from a list of MBTAstop objects."""
        stop_ids = [stop.id for stop in stops]
        return stop_ids
    
    @staticmethod
    def get_stop_ids_by_name(stops: list['MBTAStop'], stop_name: str) -> list[str]:
        """Retrieve a list of stop IDs from the list of MBTAstops based on the stop name."""
        stop_ids = [stop.id for stop in stops if stop.name.lower() == stop_name.lower()]
        return stop_ids
           
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
    def compute_delay(real_time: Optional[datetime], time: Optional[datetime]) -> Optional[float]:
        if real_time is None or time is None:
            return None
        return (real_time - time).total_seconds()

    @staticmethod
    def parse_datetime(time_str: str) -> Optional[datetime]:
        """Parse a string in ISO 8601 format to a datetime object."""
        if time_str is None:
            return None
        try:
            return datetime.fromisoformat(time_str)
        except ValueError as e:
            logging.error(f"Error parsing datetime: {e}")
            return None
