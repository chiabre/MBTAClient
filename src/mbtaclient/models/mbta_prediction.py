from datetime import datetime
from enum import Enum
import logging
from typing import Any, Optional

class MBTAPrediction:
    """A prediction object to hold information about a prediction."""
    
    def __init__(self, prediction: dict[str, Any]) -> None:
        try:
            # ID
            self.id: Optional[str] = prediction.get('id', None)
            
            # Attributes
            attributes = prediction.get('attributes', {})
            self.update_type: Optional[str] = attributes.get('update_type', None)
            self.stop_sequence: Optional[int] = attributes.get('stop_sequence', None)
            self.status: Optional[str] = attributes.get('status', None)
            self.schedule_relationship: Optional[str] = attributes.get('schedule_relationship', None)
            self.revenue_status: Optional[str] = attributes.get('revenue_status', None)
            self.direction_id: Optional[int] = attributes.get('direction_id', None)        
            self.departure_uncertainty: Optional[int] = attributes.get('departure_uncertainty', None)
            self.departure_time: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('departure_time'))
                if attributes.get('departure_time') is not None
                else None
            )
            self.arrival_uncertainty: Optional[int] = attributes.get('arrival_uncertainty', None)
            self.arrival_time: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('arrival_time'))
                if attributes.get('arrival_time') is not None
                else None
            )
            
            # Relationships
            relationships: dict = prediction.get('relationships', {})
            self.vehicle_id: Optional[str] = relationships.get('vehicle', {}).get('data', {}).get('id', None) if relationships.get('vehicle', {}).get('data') is not None else None
            self.stop_id: Optional[str] = relationships.get('stop', {}).get('data', {}).get('id', None) if relationships.get('stop', {}).get('data') is not None else None
            self.trip_id: Optional[str] = relationships.get('trip', {}).get('data', {}).get('id', None) if relationships.get('trip', {}).get('data') is not None else None
            self.schedule_id: Optional[str] = relationships.get('schedule', {}).get('data', {}).get('id', None) if relationships.get('schedule', {}).get('data') is not None else None
            self.route_id: Optional[str] = relationships.get('route', {}).get('data', {}).get('id', None) if relationships.get('route', {}).get('data') is not None else None
            # Extract a list of alert IDs
            self.alerts_id: Optional[list[Optional[str]]] = [
                alert.get('id') for alert in relationships.get('alerts', {}).get('data', []) if alert.get('id') is not None
            ]
            
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)

    def __repr__(self) -> str:
        return (f"MBTAPrediction:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the prediction ID."""
        if isinstance(other, MBTAPrediction):
            return self.id == other.id
        return False

class MBTAScheduleRelationship(Enum):
    ADDED = "ADDED"  # An extra trip added in addition to a running schedule.
    CANCELLED = "CANCELLED"  # A trip that existed in the schedule but was removed.
    NO_DATA = "NO_DATA"  # No data given for this stop; no realtime info available.
    SKIPPED = "SKIPPED"  # A stop that was originally scheduled but was skipped.
    UNSCHEDULED = "UNSCHEDULED"  # A trip running with no schedule associated.
