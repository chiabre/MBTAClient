import typing
from typing import Any, Dict, List

class MBTARoute:
    """A route object to hold information about a route."""

    ROUTE_TYPES= {
        0: 'Light Rail',   # Example: Green Line
        1: 'Heavy Rail',   # Example: Red Line
        2: 'Commuter Rail',
        3: 'Bus',
        4: 'Ferry'
    }

    def __init__(self, route: Dict[str, Any]) -> None:
        attributes = route.get('attributes', {})

        self.route_id: str = route.get('id', '')
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
        return (f"MBTAroute(id={self.route_id}, color={self.route_color}, description={self.route_description}, "
                f"direction_destinations={self.route_direction_destinations}, direction_names={self.route_direction_names}, "
                f"fare_class={self.route_fare_class}, long_name={self.route_long_name}, short_name={self.route_short_name}, "
                f"sort_order={self.route_sort_order}, text_color={self.route_text_color}, type={self.route_type})")

    def __str__(self) -> str:
        return f"Route {self.route_short_name or self.route_id}: {self.route_long_name}"

