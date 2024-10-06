from typing import Any

class MBTAStop:
    """A stop object to hold information about a stop."""

    def __init__(self, stop: dict[str, Any]) -> None:
        attributes = stop.get('attributes', {})

        self.id: str = stop.get('id', '')
        self.address: str = attributes.get('address', '')
        self.at_street: str = attributes.get('at_street', '')
        self.description: str = attributes.get('description', '')
        self.latitude: float = attributes.get('latitude', 0.0)
        self.location_type: int = attributes.get('location_type', 0)
        self.longitude: float = attributes.get('longitude', 0.0)
        self.municipality: str = attributes.get('municipality', '')
        self.name: str = attributes.get('name', '')
        self.on_street: str = attributes.get('on_street', '')
        self.platform_code: str = attributes.get('platform_code', '')
        self.platform_name: str = attributes.get('platform_name', '')
        self.vehicle_type: int = attributes.get('vehicle_type', 0)
        self.wheelchair_boarding: int = attributes.get('wheelchair_boarding', 0)

    def __repr__(self) -> str:
        return (f"MBTAstop(id={self.id})")

