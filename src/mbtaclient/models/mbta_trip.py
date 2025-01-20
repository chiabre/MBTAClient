import logging
from typing import Any, Optional

class MBTATrip:
    """A trip object to hold information about a trip."""
    
    def __init__(self, trip: dict[str, Any]) -> None:
        try:
            # ID
            self.id: str = trip.get('id', '')
            
            # Attributes
            attributes = trip.get('attributes', {})
            self.name: Optional[str] = attributes.get('name', None)
            self.headsign: Optional[str] = attributes.get('headsign', None)
            self.direction_id: Optional[int] = attributes.get('direction_id', None)
            self.block_id: Optional[str] = attributes.get('block_id', None)
            self.shape_id: Optional[str] = attributes.get('shape_id', None)
            self.wheelchair_accessible: Optional[bool] = attributes.get('wheelchair_accessible', None)
            self.bikes_allowed: Optional[bool] = attributes.get('bikes_allowed', None)
            self.schedule_relationship: Optional[str] = attributes.get('schedule_relationship', None)

            # Relationships
            relationships = trip.get('relationships', {})
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
        return (f"MBTATrip(id={self.id}, headsign={self.headsign})")
    
class MBTATripError(Exception):
    pass
