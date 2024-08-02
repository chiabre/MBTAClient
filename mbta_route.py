import typing
from typing import Any, Dict, List, Optional

class MBTAroute:
    """A route object to hold information about a route."""

    def __init__(self, route: Dict[str, Any]) -> None:
        attributes = route.get('attributes', {})
        
        self.route_id: Optional[str] = route.get('id')
        self.route_color: Optional[str] = attributes.get('color')
        self.route_description: Optional[str] = attributes.get('description')
        self.route_direction_destinations: List[str] = attributes.get('direction_destinations', [])
        self.route_direction_names: List[str] = attributes.get('direction_names', [])
        self.route_fare_class: Optional[str] = attributes.get('fare_class')
        self.route_long_name: Optional[str] = attributes.get('long_name')
        self.route_short_name: Optional[str] = attributes.get('short_name')
        self.route_sort_order: Optional[int] = attributes.get('sort_order')
        self.route_text_color: Optional[str] = attributes.get('text_color')
        self.route_type: Optional[int] = attributes.get('type')
        
    def __repr__(self) -> str:
        return (f"MBTAroute(id={self.route_id}, color={self.route_color}, description={self.route_description}, "
                f"direction_destinations={self.route_direction_destinations}, direction_names={self.route_direction_names}, "
                f"fare_class={self.route_fare_class}, long_name={self.route_long_name}, short_name={self.route_short_name}, "
                f"sort_order={self.route_sort_order}, text_color={self.route_text_color}, type={self.route_type})")
    
    def __str__(self) -> str:
        return f"Route {self.route_short_name or self.route_id}: {self.route_long_name}"
