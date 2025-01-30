from datetime import datetime
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
            self.timepoint: Optional[bool] = attributes.get('timepoint', None)
            self.stop_sequence: Optional[int] = attributes.get('stop_sequence', None)
            self.stop_headsign: Optional[str] = attributes.get('stop_headsign', None)
            self.pickup_type: Optional[int] = attributes.get('pickup_type', None)
            self.drop_off_type: Optional[int] = attributes.get('drop_off_type', None)
            self.direction_id: Optional[int] = attributes.get('direction_id', None)
            self.departure_time: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('departure_time'))
                if attributes.get('departure_time') is not None
                else None
            )
            self.arrival_time: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('arrival_time'))
                if attributes.get('arrival_time') is not None
                else None
            )

            # Relationships
            relationships = schedule.get('relationships', {})
            self.trip_id: Optional[str] = relationships.get('trip', {}).get('data', {}).get('id', None) if relationships.get('trip', {}).get('data') is not None else None
            self.stop_id: Optional[str] = relationships.get('stop', {}).get('data', {}).get('id', None) if relationships.get('stop', {}).get('data') is not None else None
            self.route_id: Optional[str] = relationships.get('route', {}).get('data', {}).get('id', None) if relationships.get('route', {}).get('data') is not None else None
            self.prediction_id: Optional[str] = relationships.get('prediction', {}).get('data', {}).get('id', None) if relationships.get('prediction', {}).get('data') is not None else None

        
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)

    def __repr__(self) -> str:
        return (f"MBTASchedule:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the schedule ID."""
        if isinstance(other, MBTASchedule):
            return self.id == other.id
        return False
