from typing import Union, Optional
from datetime import datetime

from .journey_stop import JourneyStop
from .schedule import MBTASchedule
from .prediction import MBTAPrediction
from .stop import MBTAStop
from .route import MBTARoute
from .trip import MBTATrip
from .alert import MBTAAlert
from .utils import MBTAUtils

class Journey:
    """A class to manage a journey with multiple stops."""

    def __init__(self) -> None:
        """
        Initialize a Journey with optional route, trip, and alert information.
        Departure and arrival stops are also initialized as None.
        """
        self.duration = None
        self.route: Optional[MBTARoute] = None
        self.trip: Optional[MBTATrip] = None
        self.alerts: list[MBTAAlert] = []
        self.stops: dict[str, Optional[JourneyStop]] = {
            'departure': None,
            'arrival': None
        }

    def __repr__(self) -> str:
        return f"Journey(depart_from={self.stops['departure']}, arrive_at={self.stops['arrival']})"
    
    def add_stop(self, stop_type: str, scheduling_data: Union[MBTASchedule,MBTAPrediction], stop: MBTAStop, status) -> None:
        """Add or update a stop to the journey."""
        
        if self.stops[stop_type] is None: 
        
            # Create or update JourneyStop
            journey_stop = JourneyStop(
                stop,
                scheduling_data.arrival_time,
                scheduling_data.departure_time,
                scheduling_data.stop_sequence,
                status
            )

            self.stops[stop_type] = journey_stop
        
        else:
            
            self.stops[stop_type].update_stop(
                stop,
                scheduling_data.arrival_time,
                scheduling_data.departure_time,
                scheduling_data.stop_sequence,
                status
            )
            
        if self.stops['departure'] and self.stops['arrival']:
            self.duration = MBTAUtils.calculate_time_difference(self.stops['arrival'].get_time(),self.stops['departure'].get_time())
        
    def get_stop(self, stop_type: str) -> Optional[JourneyStop]:
        """Return the specified stop or None if not set."""
        if stop_type in self.stops:
            return self.stops[stop_type]

    def get_stop_id(self, stop_type: str) -> Optional[str]:
        """Return the stop ID for the specified stop type, or an empty string if None."""
        journey_stop = self.get_stop(stop_type)
        return journey_stop.stop.id if journey_stop and journey_stop.stop and journey_stop.stop.id else None

    def get_stops_ids(self) -> list[str]:
        """Return the IDs for both departure and arrival stops."""
        return [self.get_stop_id('departure'), self.get_stop_id('arrival')]
    
    def find_journey_stop_by_id(self, stop_id: str) -> Optional[JourneyStop]:
        """Return the JourneyStop with the given stop_id, or None if not found."""
        for stop in self.stops.values():
            if stop and stop.stop.id == stop_id:
                return stop
        return None

    def get_route_short_name(self) -> Optional[str]:
        return self.route.short_name if self.route else None
        
    def get_route_long_name(self) -> Optional[str]:
        return self.route.long_name if self.route else None

    def get_route_color(self) -> Optional[str]:
        return self.route.color if self.route else None

    def get_route_description(self) -> Optional[str]:
        return MBTAUtils.get_route_type_desc_by_type_id(self.route.type) if self.route else None

    def get_route_type(self) -> Optional[str]:
        return self.route.type if self.route else None
    
    def get_trip_headsign(self) -> Optional[str]:
        return self.trip.headsign if self.trip else None

    def get_trip_name(self) -> Optional[str]:
        return self.trip.name if self.trip else None

    def get_trip_destination(self) -> Optional[str]:
        if self.trip and self.route:
            trip_direction = self.trip.direction_id
            return self.route.direction_destinations[trip_direction]
        return None

    def get_trip_direction(self) -> Optional[str]:
        if self.trip and self.route:
            trip_direction = self.trip.direction_id
            return self.route.direction_names[trip_direction]
        return None
    
    def get_trip_duration(self) -> Optional[str]:
        if self.duration:
            return round(self.duration,0)
        return None

    def get_stop_name(self, stop_type: str) -> Optional[str]:
        """Return the stop name for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.stop.name if stop else None
    
    def get_platform_name(self, stop_type: str) -> Optional[str]:
        """Return the platform name for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.stop.platform_name if stop else None

    def get_stop_time(self, stop_type: str) -> Optional[datetime]:
        """Return the stop time for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.get_time() if stop else None

    def get_stop_delay(self, stop_type: str) -> Optional[float]:
        """Return the stop delay for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.get_delay() if stop else None

    def get_stop_status(self, stop_type: str) -> Optional[float]:
        """Return the stop delay for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.status if stop else None
    
    def get_stop_time_to(self, stop_type: str) -> Optional[float]:
        """Return the time to for the specified stop type."""
        stop = self.get_stop(stop_type)
        return stop.get_time_to() if stop else None
    
    def get_alert_header(self, alert_index: int) -> Optional[str]:
        alert = self.alerts[alert_index]
        return alert.header_text
