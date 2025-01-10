from typing import Any, Optional

class MBTAAlert:
    """An alert object to hold information about an MBTA alert."""

    def __init__(self, alert: dict[str, Any]) -> None:
        attributes = alert.get('attributes', {})
        
        # Basic attributes
        self.id: str = alert.get('id', '')
        self.active_period_start: Optional[str] = attributes.get('active_period', [{}])[0].get('start', None)
        self.active_period_end: Optional[str] = attributes.get('active_period', [{}])[0].get('end', None)
        self.cause: str = attributes.get('cause', '')
        self.effect: str = attributes.get('effect', '')
        self.header_text: str = attributes.get('header', '')
        self.description_text: Optional[str] = attributes.get('description', None)
        self.severity: int = attributes.get('severity', 0)
        self.created_at: str = attributes.get('created_at', '')
        self.updated_at: str = attributes.get('updated_at', '')
        
        # Informed entities
        self.informed_entities: list[dict[str, Any]] = [
            {
                "activities": entity.get('activities', []),
                "route": entity.get('route', ''),
                "route_type": entity.get('route_type', 0),
                "stop": entity.get('stop', ''),
                "trip": entity.get('trip', ''),
                "facility": entity.get('facility', '')
            }
            for entity in attributes.get('informed_entity', [])
        ]

    def __repr__(self) -> str:
        return (f"MBTAalert(id={self.alert_id})")

    def get_informed_stops(self) -> list[str]:
        """Retrieve a list of unique stops from informed entities."""
        return list({entity['stop'] for entity in self.informed_entities if entity.get('stop')})

    def get_informed_trips(self) -> list[str]:
        """Retrieve a list of unique trips from informed entities."""
        return list({entity['trip'] for entity in self.informed_entities if entity.get('trip')})

    def get_informed_routes(self) -> list[str]:
        """Retrieve a list of unique routes from informed entities."""
        return list({entity['route'] for entity in self.informed_entities if entity.get('route')})