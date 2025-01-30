import logging
from typing import Any, Optional

class MBTARoute:
    """A route object to hold information about a route."""

    ROUTE_TYPES= {
        0: 'Light Rail',   
        1: 'Heavy Rail',  
        2: 'Commuter Rail',
        3: 'Bus',
        4: 'Ferry'
    }
    
    def __init__(self, route: dict[ str, Any]) -> None:
        try:
            # ID
            self.id:  Optional[str] = route.get('id', None)
            
            # Attributes
            attributes = route.get('attributes', {})
            self.type: Optional[str] = attributes.get('type', None)
            self.text_color: Optional[str] = attributes.get('text_color', None)
            self.sort_order: Optional[int] = attributes.get('sort_order', None)
            self.short_name: Optional[str] = attributes.get('short_name', None)
            self.long_name: Optional[str] = attributes.get('long_name', None)
            self.fare_class: Optional[str] = attributes.get('fare_class', None)
            self.direction_names: list[Optional[str]] = attributes.get('direction_names', [])
            self.direction_destinations: list[Optional[str]] = attributes.get('direction_destinations', [])
            self.description: Optional[str] = attributes.get('description', None)
            self.color: Optional[str] = attributes.get('color', None)
       
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)
        
    def __repr__(self) ->  Optional[str]:
        return (f"MBTAroute:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the route ID."""
        if isinstance(other, MBTARoute):
            return self.id == other.id
        return False
    
    @staticmethod
    def get_route_type_desc_by_type_id(route_type: int) ->  Optional[str]:
        """Get a description of the route type."""
        return MBTARoute.ROUTE_TYPES.get(route_type, 'Unknown')
    

