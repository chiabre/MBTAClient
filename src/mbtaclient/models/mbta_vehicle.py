from datetime import datetime
import logging
from typing import Any, Optional

class MBTAVehicle:
    """A vehicle object to hold information about an MBTA vehicle."""

    def __init__(self, vehicle: dict[str, Any]) -> None:
        try:
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
            self.updated_at: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('updated_at'))
                if attributes.get('updated_at') is not None
                else None
            )
            self.latitude: Optional[str] = attributes.get('latitude', None)
            self.longitude: Optional[str] = attributes.get('longitude', None)

            # Relationships
            relationships = vehicle.get('relationships', {})
            self.trip_id: Optional[str] = relationships.get('trip', {}).get('data', {}).get('id', None) if relationships.get('trip').get('data') else None
            self.stop_id: Optional[str] = relationships.get('stop', {}).get('data', {}).get('id', None) if relationships.get('stop').get('data') else None
            self.route_id: Optional[str] = relationships.get('route', {}).get('data', {}).get('id', None) if relationships.get('route').get('data') else None
            
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)

    def __repr__(self) -> str:
        return (f"MBTAVehicles:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the vehicle ID."""
        if isinstance(other, MBTAVehicle):
            return self.id == other.id
        return False

