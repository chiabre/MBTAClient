import typing
from typing import Any, Dict, Optional, List

class MBTAStop:
    """A stop object to hold information about a stop."""

    def __init__(self, stop: Dict[str, Any]) -> None:
        attributes = stop.get('attributes', {})

        self.id: str = stop.get('id', '')
        self.address: str = attributes.get('address', '')
        self.at_street: str = attributes.get('at_street', '')
        self.description: str = attributes.get('description', '')
        self.latitude: float = attributes.get('latitude', 0.0)
        self.location_type: int = attributes.get('location_type', 0)
        self.longitude: float = attributes.get('longitude', 0.0)
        self.municipality: str = attributes.get('municipality', '')
        self.name: str = attributes.get('name', '')
        self.on_street: str = attributes.get('on_street', '')
        self.platform_code: str = attributes.get('platform_code', '')
        self.platform_name: str = attributes.get('platform_name', '')
        self.vehicle_type: int = attributes.get('vehicle_type', 0)
        self.wheelchair_boarding: int = attributes.get('wheelchair_boarding', 0)

    def __repr__(self) -> str:
        return (f"MBTAstop(id={self.id}, name={self.name})")

    @classmethod
    def get_stop_ids_by_name(cls, stops: List['MBTAStop'], stop_name: str) -> List[str]:
        """Given a list of MBTAstop objects and a stop name, return a list of stop ids that match the stop name."""
        matching_stop_ids = [stop.id for stop in stops if stop.name.lower() == stop_name.lower()]
        return matching_stop_ids
    
    @classmethod
    def get_stops_by_name(cls, stops: List['MBTAStop'], stop_name: str) -> List['MBTAStop']:
        """Given a list of MBTAstop objects and a stop name, return a list of MBTAstop objects that match the stop name."""
        matching_stops = [stop for stop in stops if stop.name.lower() == stop_name.lower()]
        return matching_stops