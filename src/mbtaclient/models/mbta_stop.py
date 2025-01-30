import logging
from typing import Any, Optional

class MBTAStop:
    """A stop object to hold information about a stop."""

    def __init__(self, stop: dict[str, Any]) -> None:
        try:
            # ID
            self.id: str = stop.get('id', '')
            
            # Attributes
            attributes = stop.get('attributes', {})
            self.address: Optional[str] = attributes.get('address', None)
            self.at_street: Optional[str] = attributes.get('at_street', None)
            self.description: Optional[str] = attributes.get('description', None)
            self.latitude: Optional[float] = attributes.get('latitude', None)
            self.location_type: Optional[int] = attributes.get('location_type', None)
            self.longitude: Optional[float] = attributes.get('longitude', None)
            self.municipality: Optional[str] = attributes.get('municipality', None)
            self.name: Optional[str] = attributes.get('name', None)
            self.on_street: Optional[str] = attributes.get('on_street', None)
            self.platform_code: Optional[str] = attributes.get('platform_code', None)
            self.platform_name: Optional[str] = attributes.get('platform_name', None)
            self.vehicle_type: Optional[int] = attributes.get('vehicle_type', None)
            self.wheelchair_boarding: Optional[int] = attributes.get('wheelchair_boarding', None)

        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)
        
    def __repr__(self) -> str:
        return (f"MBTAStop:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the stop ID."""
        if isinstance(other, MBTAStop):
            return self.id == other.id
        return False
