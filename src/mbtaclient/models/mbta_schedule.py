import logging
from typing import Any, Optional

class MBTASchedule:
    """A schedule object to hold information about a schedule."""

    def __init__(self, schedule: dict[str, Any]) -> None:
        try:
            # ID
            self.id: Optional[str] = schedule.get('id', None)
            
            # Attributes
            attributes = schedule.get('attributes', {})
            self.arrival_time: Optional[str] = attributes.get('arrival_time', None)
            self.departure_time: Optional[str] = attributes.get('departure_time', None)
            self.direction_id: Optional[int] = attributes.get('direction_id', None)
            self.drop_off_type: Optional[str] = attributes.get('drop_off_type', None)
            self.pickup_type: Optional[str] = attributes.get('pickup_type', None)
            self.stop_headsign: Optional[str] = attributes.get('stop_headsign', None)
            self.stop_sequence: Optional[int] = attributes.get('stop_sequence', None)
            self.timepoint: Optional[bool] = attributes.get('timepoint', None)

            # Relationships
            relationships = schedule.get('relationships', {})
            # Ensure 'data' exists and is not None before accessing it
            self.trip_id: Optional[str] = (
                relationships.get('trip', {}).get('data', {}).get('id', None) if (relationships.get('trip') and relationships.get('trip').get('data')) else None
            )
            self.stop_id: Optional[str] = (
                relationships.get('stop', {}).get('data', {}).get('id', None) if (relationships.get('stop') and relationships.get('stop').get('data')) else None
            )
            self.route_id: Optional[str] = (
                relationships.get('route', {}).get('data', {}).get('id', None) if (relationships.get('route') and relationships.get('route').get('data')) else None
            )
        
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)
            # Re-raise the exception if needed or handle accordingly
            raise

    def __repr__(self) -> str:
        return (f"MBTASchedule(id={self.id}, route_id={self.route_id}, stop_id={self.stop_id})")


