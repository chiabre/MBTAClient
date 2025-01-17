from typing import Union, Optional
from datetime import datetime, timedelta

from .trip_stop import TripStop, StopType

from .models.mbta_schedule import MBTASchedule
from .models.mbta_prediction import MBTAPrediction
from .models.mbta_stop import MBTAStop
from .models.mbta_route import MBTARoute
from .models.mbta_alert import MBTAAlert
from .models.mbta_trip import MBTATrip
from .models.mbta_vehicle import MBTAVehicle

class Trip:
    """A class to manage a Trip with multiple stops."""

    def __init__(self) -> None:
        """
        Initialize the Trip with optional MBTARoute, MBTATrip, and MBTAAlert information.
        """
        self.duration:  Optional[int] = None
        self.mbta_route: Optional[MBTARoute] = None
        self.mbta_trip: Optional[MBTATrip] = None
        self.mbta_vehicle: Optional[MBTAVehicle] = None
        self.mbta_alerts: list[MBTAAlert] = []
        self.stops: list[Optional[TripStop]] =[]

    def __repr__(self) -> str:
        return (f"Trip(depart_from={self._departure_stop}, arrive_at={self._arrival_stop})" if self._departure_stop and self._arrival_stop else "Trip not fully defined")
    
    @property
    def _departure_stop(self) -> Optional[TripStop]:
        return next((stop for stop in self.stops if stop.stop_type == StopType.DEPARTURE), None)

    @property
    def _arrival_stop(self) -> Optional[TripStop]:
        """Return the arrival stop if it exists, otherwise None."""
        return next((stop for stop in self.stops if stop.stop_type == StopType.ARRIVAL), None)

    @property
    def route_short_name(self) -> Optional[str]:
        return self.mbta_route.short_name if self.mbta_route else None

    @property
    def route_long_name(self) -> Optional[str]:
        return self.mbta_route.long_name if self.mbta_route else None

    @property
    def route_color(self) -> Optional[str]:
        return self.mbta_route.color if self.mbta_route else None

    @property
    def route_description(self) -> Optional[str]:
        return MBTARoute.get_route_type_desc_by_type_id(self.mbta_route.type) if self.mbta_route else None

    @property
    def route_type(self) -> Optional[str]:
        return self.mbta_route.type if self.mbta_route else None

    @property
    def headsign(self) -> Optional[str]:
        return self.mbta_trip.headsign if self.mbta_trip else None

    @property
    def name(self) -> Optional[str]:
        return self.mbta_trip.name if self.mbta_trip else None

    @property
    def destination(self) -> Optional[str]:
        if self.mbta_trip and self.mbta_route:
            return self.mbta_route.direction_destinations[self.mbta_trip.direction_id]
        return None
    
    @property
    def direction(self) -> Optional[str]:
        if self.mbta_trip and self.mbta_route:
            return self.mbta_route.direction_names[self.mbta_trip.direction_id]
        return None

    @property
    def departure_stop_name(self) -> Optional[str]:
        """Get the departure stop name."""
        return self.stop_name(StopType.DEPARTURE)

    @property
    def arrival_stop_name(self) -> Optional[str]:
        """Get the arrival stop name."""
        return self.stop_name(StopType.ARRIVAL)

    @property
    def departure_platform_name(self) -> Optional[str]:
        """Get the departure platform name."""
        return self.platform_name(StopType.DEPARTURE)

    @property
    def arrival_platform_name(self) -> Optional[str]:
        """Get the arrival platform name."""
        return self.platform_name(StopType.ARRIVAL)

    @property
    def departure_time(self) -> Optional[datetime]:
        """Get the departure stop time."""
        return self.stop_time(StopType.DEPARTURE)

    @property
    def arrival_time(self) -> Optional[datetime]:
        """Get the arrival stop time."""
        return self.stop_time(StopType.ARRIVAL)

    @property
    def departure_delay(self) -> Optional[int]:
        """Get the departure stop delay."""
        return self.stop_delay(StopType.DEPARTURE)

    @property
    def arrival_delay(self) -> Optional[int]:
        """Get the arrival stop delay."""
        return self.stop_delay(StopType.ARRIVAL)

    @property
    def departure_status(self) -> Optional[str]:
        """Get the departure stop status."""
        return self.stop_countdown(StopType.DEPARTURE)

    @property
    def arrival_status(self) -> Optional[str]:
        """Get the arrival stop status."""
        return self.stop_countdown(StopType.ARRIVAL)

    @property
    def departure_time_to(self) -> Optional[int]:
        """Get the time to the departure stop."""
        return self.time_to_stop(StopType.DEPARTURE)

    @property
    def arrival_time_to(self) -> Optional[int]:
        """Get the time to the arrival stop."""
        return self.time_to_stop(StopType.ARRIVAL)

    def add_stop(
        self, 
        stop_type: str, 
        scheduling_data: Union[MBTASchedule, MBTAPrediction], 
        mbta_stop: MBTAStop, 
        status: str = '',
    ) -> None:
        """Add or update a stop in the journey."""

        # Check if stop type is valid
        if stop_type not in StopType:
            raise ValueError(f"Invalid stop_type: {stop_type}. Must be one of {StopType}.")

        arrival_time = scheduling_data.arrival_time if scheduling_data.arrival_time else None
        departure_time = scheduling_data.departure_time if scheduling_data.departure_time else None
        stop_sequence = scheduling_data.stop_sequence
    
        # Find existing stop by type or create a new one
        existing_stop: Optional[TripStop] = next((stop for stop in self.stops if stop and stop.stop_type == stop_type), None)

        if existing_stop is None:
            # Create a new TripStop
            trip_stop = TripStop(
                stop_type=stop_type,
                mbta_stop=mbta_stop,
                arrival_time=arrival_time,
                departure_time=departure_time,
                stop_sequence=stop_sequence,
                status=status,
            )
            self.stops.append(trip_stop)
        else:
            # Update existing TripStop
            existing_stop.update_stop(
                mbta_stop=mbta_stop,
                arrival_time=arrival_time,
                departure_time=departure_time,
                stop_sequence=stop_sequence,
                status=status,
            )
            
        # Check if both departure and arrival stops are set to calculate the duration
        if self._departure_stop and self._arrival_stop:
            self.duration: Optional[int] = TripStop.calculate_time_difference(
                self._arrival_stop.get_time(),
                self._departure_stop.get_time(),
            )

        
    def reset_stops(self):
        self.stops = []    
        
    def stop_ids(self) -> list[str]:
        """Return IDs of departure and arrival stops."""
        return [self._stop_id(StopType.DEPARTURE), self._stop_id(StopType.ARRIVAL)]

    def stop(self, stop_type: str) -> Optional[TripStop]:
        """Return the stop of the given type."""
        if stop_type not in StopType:
            raise ValueError(f"Invalid stop_type: {stop_type}. Must be one of {StopType}.")
        return next((stop for stop in self.stops if stop.stop_type == stop_type), None)

    def _stop_id(self, stop_type: str) -> Optional[str]:
        """Return the ID of the stop of the given type."""
        stop = self.stop(stop_type)
        return stop.mbta_stop.id if stop and stop.mbta_stop else None

    def _find_stop(self, stop_id: str) -> Optional[TripStop]:
        """Find a stop by its ID."""
        return next((stop for stop in self.stops if stop and stop.mbta_stop.id == stop_id), None)

    def stop_name(self, stop_type: str) -> Optional[str]:
        stop = self.stop(stop_type)
        return stop.mbta_stop.name if stop else None

    def platform_name(self, stop_type: str) -> Optional[str]:
        stop = self.stop(stop_type)
        return stop.mbta_stop.platform_name if stop else None

    def stop_time(self, stop_type: str) -> Optional[datetime]:
        stop = self.stop(stop_type)
        return stop.time if stop else None

    def stop_delay(self, stop_type: str) -> Optional[int]:
        stop = self.stop(stop_type)
        return stop.get_delay() if stop else None

    def stop_status(self, stop_type: str) -> Optional[str]:
        stop = self.stop(stop_type)
        return stop.status if stop else None

    def time_to_stop(self, stop_type: str) -> Optional[int]:
        stop = self.stop(stop_type)
        return stop.get_time_to() if stop else None

    def alert_header(self, alert_index: int) -> Optional[str]:
        if 0 <= alert_index < len(self.mbta_alerts):
            return self.mbta_alerts[alert_index].header_text
        return None

    def stop_countdown(self, stop_type: StopType) -> Optional[str]:
            stop = self.stop(stop_type)
            if not stop:
                return None

            target_time = self.stop_time(stop_type)
                           
            if not target_time:
                return None
            
            now = datetime.now().astimezone()
            
            if target_time.date() >= (now + timedelta(days=1)).date():
                days = (target_time.date() - now.date()).days
                return f"+{days} day{'s' if days > 1 else ''}"

            minutes = int((target_time - now).total_seconds() // 60)
            

            if self.mbta_vehicle:
                if stop.stop_sequence == 0:  # Check for originating station
                    if minutes < 2 and self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
                        return "BOARDING"
                    elif minutes < 5 and self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
                        return f"DEPARTING {minutes} min"
                else: # Check for other stations
                    if self.mbta_vehicle.current_status == "STOPPED_AT" and minutes <= 1 and self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
                        return "BOARDING"
                    elif self.mbta_vehicle.current_status == "IN_TRANSIT_TO" and minutes <= 2 and self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
                        return f"ARRIVING {minutes} min" if minutes > 0 else "ARRIVING"
                
                if minutes < 0:
                    if  self.mbta_vehicle.current_stop_sequence > stop.stop_sequence:
                        return "DEPARTED"
                    else:
                        return "DEPARTING"
            else:
                if minutes < 0:
                    "DELAYED"        


            if minutes >= 60:
                hours = int(minutes // 60)
                remaining_minutes = int(minutes % 60)
                return f"{hours} hr {remaining_minutes} min" if remaining_minutes > 0 else f"{hours} hr"

            return f"{minutes} min"
