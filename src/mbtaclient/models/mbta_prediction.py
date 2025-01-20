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
            self.revenue_status: Optional[str] = attributes.get('revenue_status', None)
            self.direction_id: Optional[int] = attributes.get('direction_id', None)
            self.schedule_relationship: Optional[str] = attributes.get('schedule_relationship', None)
            self.departure_uncertainty: Optional[int] = attributes.get('departure_uncertainty', None)
            self.departure_time: Optional[str] = attributes.get('departure_time', None)
            self.arrival_uncertainty: Optional[int] = attributes.get('arrival_uncertainty', None)
            self.arrival_time: Optional[str] = attributes.get('arrival_time', None)
            
            # Relationships
            relationships: dict = prediction.get('relationships', {})
            # Ensure 'data' exists and is not None before accessing it
            self.vehicle_id: Optional[str] = (
                relationships.get('vehicle', {}).get('data', None).get('id', None) if (relationships.get('vehicle') and relationships.get('vehicle').get('data')) else None
            )
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
        return (f"MBTAPrediction(id={self.id}, route_id={self.route_id}, stop_id={self.stop_id})")
