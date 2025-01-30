from datetime import datetime
import logging
from typing import Any, Optional
from enum import Enum

class MBTAAlert:
    """An alert object to hold information about an MBTA alert."""

    def __init__(self, alert: dict[str, Any]) -> None:
        try:
            # ID
            self.id: Optional[str] = alert.get('id', None)

            # Attributes
            attributes = alert.get('attributes', {})
            self.url: Optional[str] = attributes.get('url', None)
            self.updated_at: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('updated_at'))
                if attributes.get('updated_at') is not None
                else None
            )
            self.timeframe: Optional[str] = attributes.get('timeframe', None)
            self.short_header: Optional[str] = attributes.get('short_header', None)
            self.severity: Optional[str] = attributes.get('severity', None)
            self.service_effect: Optional[str] = attributes.get('service_effect', None)
            self.lifecycle: Optional[str] = attributes.get('lifecycle', None)

            # Informed Entities
            self.informed_entities: list[MBTAAlertsInformedEntity] = [
                MBTAAlertsInformedEntity(
                    trip_id=entity.get('trip'),
                    stop_id=entity.get('stop'),
                    route_type=entity.get('route_type'),
                    route_id=entity.get('route'),
                    facility_id=entity.get('facility'),
                    direction_id=entity.get('direction_id'),
                    activities=entity.get('activities')
                )
                for entity in attributes.get('informed_entity', [])
            ]
            
            self.image_alternative_text: Optional[str] = attributes.get('image_alternative_text', None)
            self.image: Optional[str] = attributes.get('image', None)
            self.header: Optional[str] = attributes.get('header', None)
            self.effect_name: Optional[str] = attributes.get('effect_name', None)
            self.effect: Optional[str] = attributes.get("effect", None)
            self.duration_certainty: Optional[str] = attributes.get('duration_certainty', None)
            self.description: Optional[str] = attributes.get('description', None)
            self.created_at: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('created_at'))
                if attributes.get('created_at') is not None
                else None
            )
            self.cause: Optional[str] = attributes.get('cause', None)            
            self.banner: Optional[str] = attributes.get('banner', None)           
            # Active period
            self.active_period_start: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('active_period', [{}])[0].get('start'))
                if attributes.get('active_period', [{}])[0].get('start') is not None
                else None
            )
            self.active_period_end: Optional[datetime] = (
                datetime.fromisoformat(attributes.get('active_period', [{}])[0].get('end'))
                if attributes.get('active_period', [{}])[0].get('end') is not None
                else None
            )
        
        except Exception as e:
            # Log the exception with traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error initializing {self.__class__.__name__}: {e}", exc_info=True)
        
    def __repr__(self) -> str:
        return (f"MBTAAlert:{self.id}")

    def __eq__(self, other: object) -> bool:
        """Defines equality based on the alert ID."""
        if isinstance(other, MBTAAlert):
            return self.id == other.id
        return False
    
class MBTAAlertsInformedEntity:
    def __init__(
        self,
        trip_id: Optional[str] = None,
        stop_id: Optional[str] = None,
        route_type: Optional[int] = None,
        route_id: Optional[str] = None,
        facility_id: Optional[str] = None,
        direction_id: Optional[int] = None,
        activities: Optional[list[str]] = None
    ):
        self.trip_id = trip_id
        self.stop_id = stop_id
        self.route_type = route_type
        self.route_id = route_id
        self.facility_id = facility_id
        self.direction_id = direction_id
        self.activities = activities

from enum import Enum

class MBTAAlertPassengerActivity(Enum):
    BOARD = "BOARD"  # Boarding a vehicle. Any passenger trip includes boarding a vehicle and exiting from a vehicle.
    BRINGING_BIKE = "BRINGING_BIKE"  # Bringing a bicycle while boarding or exiting.
    EXIT = "EXIT"  # Exiting from a vehicle (disembarking). Any passenger trip includes boarding a vehicle and exiting a vehicle.
    PARK_CAR = "PARK_CAR"  # Parking a car at a garage or lot in a station.
    RIDE = "RIDE"  # Riding through a stop without boarding or exiting. Not every passenger trip will include this – a passenger may board at one stop and exit at the next stop.
    STORE_BIKE = "STORE_BIKE"  # Storing a bicycle at a station.
    USING_ESCALATOR = "USING_ESCALATOR"  # Using an escalator while boarding or exiting (should only be used for customers who specifically want to avoid stairs.)
    USING_WHEELCHAIR = "USING_WHEELCHAIR"  # Using a wheelchair while boarding or exiting. Note that this applies to something that specifically affects customers who use a wheelchair to board or exit; a delay should not include this as an affected activity unless it specifically affects customers using wheelchairs.
