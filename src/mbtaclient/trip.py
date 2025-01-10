from typing import Any, Optional

class MBTATrip:
    """A trip object to hold information about a trip."""
    
    def __init__(self, trip: dict[str, Any]) -> None:
        attributes = trip.get('attributes', {})
        
        self.id: str = trip.get('id', '')
        self.name: str = attributes.get('name', '')
        self.headsign: str = attributes.get('headsign', '')
        self.direction_id: int = attributes.get('direction_id', 0)
        self.block_id: str = attributes.get('block_id', '')
        self.shape_id: str = attributes.get('shape_id', '')
        self.wheelchair_accessible: Optional[bool] = attributes.get('wheelchair_accessible')
        self.bikes_allowed: Optional[bool] = attributes.get('bikes_allowed')
        self.schedule_relationship: str = attributes.get('schedule_relationship', '')

        self.route_id: str = trip.get('relationships', {}).get('route', {}).get('data', {}).get('id', '')
        
        service_data = trip.get('relationships', {}).get('service', {}).get('data', {})
        self.service_id: str = service_data.get('id', '') if service_data else ''

    
    def __repr__(self) -> str:
        return (f"MBTAtrip(id={self.id})")
 


