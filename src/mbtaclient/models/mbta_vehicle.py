from typing import Any, Optional

class MBTAVehicle:
    """A vehicle object to hold information about an MBTA vehicle."""

    def __init__(self, vehicle: dict[str, Any]) -> None:
        # ID
        self.id: str = vehicle.get('id', '')
        
        # Attributes
        attributes = vehicle.get('attributes', {})
        self.current_status: Optional[str] = attributes.get('current_status', None)
        self.current_stop_sequence: Optional[str] = attributes.get('current_stop_sequence', None)
        self.direction_id: Optional[str] = attributes.get('direction_id', None)
        self.label: Optional[str] = attributes.get('label', None) 
        self.occupancy_status: Optional[str] = attributes.get('occupancy_status', None)
        self.revenue: Optional[int] = attributes.get('revenue', None)
        self.speed: Optional[str] = attributes.get('speed', None)
        self.updated_at: Optional[str] = attributes.get('updated_at', None)
        self.latitude: Optional[str] = attributes.get('latitude', None)
        self.longitude: Optional[str] = attributes.get('longitude', None)

        # Relationships
        relationships = vehicle.get('relationships', {})
        self.route_id: Optional[str] = relationships.get('route', {}).get('data', {}).get('id', None)
        self.stop_id: Optional[str] = relationships.get('stop', {}).get('data', {}).get('id', None)
        self.trip_id: Optional[str] = relationships.get('trip', {}).get('data', {}).get('id', None)

    def __repr__(self) -> str:
        return (f"MBTAVehicles(id={self.id}), label={self.label} ")
