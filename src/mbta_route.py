from typing import Any

class MBTARoute:
    """A route object to hold information about a route."""

    def __init__(self, route: dict[str, Any]) -> None:
        attributes = route.get('attributes', {})

        self.id: str = route.get('id', '')
        self.color: str = attributes.get('color', '')
        self.description: str = attributes.get('description', '')
        self.direction_destinations: list[str] = attributes.get('direction_destinations', [])
        self.direction_names: list[str] = attributes.get('direction_names', [])
        self.fare_class: str = attributes.get('fare_class', '')
        self.long_name: str = attributes.get('long_name', '')
        self.short_name: str = attributes.get('short_name', '')
        self.sort_order: int = attributes.get('sort_order', 0)
        self.text_color: str = attributes.get('text_color', '')
        self.type: str = attributes.get('type', '')

    def __repr__(self) -> str:
        return (f"MBTAroute(id={self.id})")

