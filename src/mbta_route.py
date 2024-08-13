import typing
from typing import Any, Dict, List

class MBTARoute:
    """A route object to hold information about a route."""

    ROUTE_TYPES= {
        # 0: 'Light Rail',   # Example: Green Line
        # 1: 'Heavy Rail',   # Example: Red Line
        0: 'Subway',   
        1: 'Subway',  
        2: 'Commuter Rail',
        3: 'Bus',
        4: 'Ferry'
    }

    def __init__(self, route: Dict[str, Any]) -> None:
        attributes = route.get('attributes', {})

        self.id: str = route.get('id', '')
        self.color: str = attributes.get('color', '')
        self.description: str = attributes.get('description', '')
        self.direction_destinations: List[str] = attributes.get('direction_destinations', [])
        self.direction_names: List[str] = attributes.get('direction_names', [])
        self.fare_class: str = attributes.get('fare_class', '')
        self.long_name: str = attributes.get('long_name', '')
        self.short_name: str = attributes.get('short_name', '')
        self.sort_order: int = attributes.get('sort_order', 0)
        self.text_color: str = attributes.get('text_color', '')
        self.type: str = attributes.get('type', '')

    def __repr__(self) -> str:
        return (f"MBTAroute(id={self.id}, short_name={self.short_name})")

    @staticmethod
    def get_route_type_desc_by_type_id(route_type: int) -> str:
        """Get a description of the route type."""
        return MBTARoute.ROUTE_TYPES.get(route_type, 'Unknown')