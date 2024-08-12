import typing
from typing import Any, Dict, Optional, List

class MBTAStop:
    """A stop object to hold information about a stop."""

    def __init__(self, stop: Dict[str, Any]) -> None:
        attributes = stop.get('attributes', {})

        self.stop_id: str = stop.get('id', '')
        self.stop_address: str = attributes.get('address', '')
        self.stop_at_street: str = attributes.get('at_street', '')
        self.stop_description: str = attributes.get('description', '')
        self.stop_latitude: float = attributes.get('latitude', 0.0)
        self.stop_location_type: int = attributes.get('location_type', 0)
        self.stop_longitude: float = attributes.get('longitude', 0.0)
        self.stop_municipality: str = attributes.get('municipality', '')
        self.stop_name: str = attributes.get('name', '')
        self.stop_on_street: str = attributes.get('on_street', '')
        self.stop_platform_code: str = attributes.get('platform_code', '')
        self.stop_platform_name: str = attributes.get('platform_name', '')
        self.stop_vehicle_type: int = attributes.get('vehicle_type', 0)
        self.stop_wheelchair_boarding: int = attributes.get('wheelchair_boarding', 0)

    def __repr__(self) -> str:
        return (f"MBTAstop(id={self.stop_id}, address={self.stop_address}, at_street={self.stop_at_street}, "
                f"description={self.stop_description}, latitude={self.stop_latitude}, location_type={self.stop_location_type}, "
                f"longitude={self.stop_longitude}, municipality={self.stop_municipality}, name={self.stop_name}, "
                f"on_street={self.stop_on_street}, platform_code={self.stop_platform_code}, platform_name={self.stop_platform_name}, "
                f"vehicle_type={self.stop_vehicle_type}, wheelchair_boarding={self.stop_wheelchair_boarding})")
    
    def __str__(self) -> str:
        return f"Stop {self.stop_name or self.stop_id} ({self.stop_latitude}, {self.stop_longitude}) in {self.stop_municipality}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MBTAStop):
            return self.stop_id == other.stop_id
        return False

    def __hash__(self) -> int:
        return hash(self.stop_id)

    @classmethod
    def get_stop_ids_by_name(cls, stops: List['MBTAStop'], stop_name: str) -> List[str]:
        """
        Given a list of MBTAstop objects and a stop name, return a list of stop_ids for the matching stops.
        
        :param stops: List of MBTAstop objects
        :param stop_name: Name of the stop to search for
        :return: List of stop_ids of the matching stops
        """
        matching_stop_ids = [stop.stop_id for stop in stops if stop.stop_name.lower() == stop_name.lower()]
        return matching_stop_ids
    
    @classmethod
    def get_stops_by_name(cls, stops: List['MBTAStop'], stop_name: str) -> List['MBTAStop']:
        """
        Given a list of MBTAstop objects and a stop name, return a list of MBTAstop objects that match the stop name.

        :param stops: List of MBTAstop objects
        :param stop_name: Name of the stop to search for
        :return: List of MBTAstop objects that match the stop name
        """
        matching_stops = [stop for stop in stops if stop.stop_name.lower() == stop_name.lower()]
        return matching_stops