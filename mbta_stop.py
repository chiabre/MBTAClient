import typing
from typing import Any, Dict, Optional

class MBTAstop:
    """A stop object to hold information about a stop."""

    def __init__(self, stop: Dict[str, Any]) -> None:
        attributes = stop.get('attributes', {})
        
        self.stop_id: Optional[str] = stop.get('id')
        self.stop_address: Optional[str] = attributes.get('address')
        self.stop_at_street: Optional[str] = attributes.get('at_street')
        self.stop_description: Optional[str] = attributes.get('description')
        self.stop_latitude: Optional[float] = attributes.get('latitude')
        self.stop_location_type: Optional[int] = attributes.get('location_type')
        self.stop_longitude: Optional[float] = attributes.get('longitude')
        self.stop_municipality: Optional[str] = attributes.get('municipality')
        self.stop_name: Optional[str] = attributes.get('name')
        self.stop_on_street: Optional[str] = attributes.get('on_street')
        self.stop_platform_code: Optional[str] = attributes.get('platform_code')
        self.stop_platform_name: Optional[str] = attributes.get('platform_name')
        self.stop_vehicle_type: Optional[int] = attributes.get('vehicle_type')
        self.stop_wheelchair_boarding: Optional[int] = attributes.get('wheelchair_boarding')

    def __repr__(self) -> str:
        return (f"MBTAstop(id={self.stop_id}, address={self.stop_address}, at_street={self.stop_at_street}, "
                f"description={self.stop_description}, latitude={self.stop_latitude}, location_type={self.stop_location_type}, "
                f"longitude={self.stop_longitude}, municipality={self.stop_municipality}, name={self.stop_name}, "
                f"on_street={self.stop_on_street}, platform_code={self.stop_platform_code}, platform_name={self.stop_platform_name}, "
                f"vehicle_type={self.stop_vehicle_type}, wheelchair_boarding={self.stop_wheelchair_boarding})")
    
    def __str__(self) -> str:
        return f"Stop {self.stop_name or self.stop_id} in {self.stop_municipality}"
