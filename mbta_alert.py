import typing
from typing import Any, Dict, List, Optional

class MBTAAlert:
    """An alert object to hold information about an MBTA alert."""

    def __init__(self, alert: Dict[str, Any]) -> None:
        attributes = alert.get('attributes', {})
        
        # Basic attributes
        self.alert_id: str = alert.get('id', '')
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
        self.informed_entities: List[Dict[str, Any]] = [
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
        return (f"MBTAalert(id={self.alert_id}, active_period_start={self.alert_active_period_start}, active_period_end={self.alert_active_period_end}, "
                f"cause={self.alert_cause}, effect={self.alert_effect}, header_text={self.alert_header_text}, description_text={self.alert_description_text}, "
                f"severity={self.alert_severity}, created_at={self.alert_created_at}, updated_at={self.alert_updated_at}, "
                f"informed_entities={self.informed_entities})")

    def __str__(self) -> str:
        return f"Alert {self.alert_id}: {self.alert_header_text}"

    def get_informed_stops(self) -> List[str]:
        """Retrieve a list of unique stops from informed entities."""
        return list({entity['stop'] for entity in self.informed_entities if entity.get('stop')})

    def get_informed_trips(self) -> List[str]:
        """Retrieve a list of unique trips from informed entities."""
        return list({entity['trip'] for entity in self.informed_entities if entity.get('trip')})

    def get_informed_routes(self) -> List[str]:
        """Retrieve a list of unique routes from informed entities."""
        return list({entity['route'] for entity in self.informed_entities if entity.get('route')})