import logging
from typing import Any, Dict, Optional

class MBTAAlert:
    """An alert object to hold information about an MBTA alert."""

    def __init__(self, alert: dict[str, Any]) -> None:
        try:
            # ID
            self.id: Optional[str] = alert.get('id', None)

            # Attributes
            attributes = alert.get('attributes', {})
            
            self.url: Optional[str] = attributes.get('url', None)
            self.updated_at: Optional[str] = attributes.get('updated_at', None)
            self.timeframe: Optional[str] = attributes.get('timeframe', None)
            self.short_header: Optional[str] = attributes.get('short_header', None)
            self.severity: Optional[str] = attributes.get('severity', None)
            self.service_effect: Optional[str] = attributes.get('service_effect', None)
            self.lifecycle: Optional[str] = attributes.get('lifecycle', None)

            # Informed Entities
            self.informed_entities: list[Dict[str, Optional[Any]]] = [
                {
                    "trip_id": entity.get('trip', None),
                    "stop_id": entity.get('stop', None),
                    "route_type": entity.get('route_type', None),
                    "route_id": entity.get('route', None),
                    "facility_id": entity.get('facility', None),
                    "direction_id": entity.get('direction_id', None),
                    "activities": entity.get('activities', None)
                }
                for entity in attributes.get('informed_entity', [])
            ]
            
            self.image_alternative_text: Optional[str] = attributes.get('image_alternative_text', None)
            self.image: Optional[str] = attributes.get('image', None)
            self.header: Optional[str] = attributes.get('header', None)
            self.effect_name: Optional[str] = attributes.get('effect_name', None)
            self.effect: Optional[str] = attributes.get('effect', None)
            self.duration_certainty: Optional[str] = attributes.get('duration_certainty', None)
            self.description: Optional[str] = attributes.get('description', None)
            self.cause: Optional[str] = attributes.get('cause', None)
            self.banner: Optional[str] = attributes.get('banner', None)
            
            # Active period
            self.active_period_start: Optional[str] = attributes.get('active_period', [{}])[0].get('start', None)
            self.active_period_end: Optional[str] = attributes.get('active_period', [{}])[0].get('end', None)
        
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)
            # Re-raise the exception if needed or handle accordingly
            raise
        
    def __repr__(self) -> str:
        return (f"MBTAAlert(id={self.id}, route_id={self.route_id}, stop_id={self.stop_id})")

    def get_informed_stops_ids(self) -> list[Optional[str]]:
        """Retrieve a list of unique stop IDs from informed entities."""
        return list({entity['stop_id'] for entity in self.informed_entities if entity.get('stop_id')})

    def get_informed_trips_ids(self) -> list[Optional[str]]:
        """Retrieve a list of unique trip IDs from informed entities."""
        return list({entity['trip_id'] for entity in self.informed_entities if entity.get('trip_id')})

    def get_informed_routes_ids(self) -> list[Optional[str]]:
        """Retrieve a list of unique route IDs from informed entities."""
        return list({entity['route_id'] for entity in self.informed_entities if entity.get('route_id')})
