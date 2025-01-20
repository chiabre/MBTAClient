from typing import Union, Optional
from datetime import datetime
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
        self.mbta_route: Optional[MBTARoute] = None
        self.mbta_trip: Optional[MBTATrip] = None
        self.mbta_vehicle: Optional[MBTAVehicle] = None
        self.mbta_alerts: list[MBTAAlert] = []
        self.stops: list[Optional[TripStop]] = []

    def __repr__(self) -> str:
        return (f"Trip({self.mbta_route}, {self.mbta_trip})"
        )
        
    def dump(self) -> str:
        """Generate a string representation of all properties, with each on a new line."""
        properties = {
            "headsign": self.headsign,
            "name": self.name,
            "destination": self.destination,
            "direction": self.direction,
            "duration": self.duration,
            "route_id": self.route_id,
            "route_short_name": self.route_short_name,
            "route_long_name": self.route_long_name,
            "route_color": self.route_color,
            "route_description": self.route_description,
            "route_type": self.route_type,
            "vehicle_current_status": self.vehicle_current_status,
            "vehicle_current_stop_sequence": self.vehicle_current_stop_sequence,
            "vehicle_longitude": self.vehicle_longitude,
            "vehicle_latitude": self.vehicle_latitude,
            "vehicle_occupancy_status": self.vehicle_occupancy_status,
            "vehicle_updated_at": self.vehicle_updated_at,
            "departure_stop_name": self.departure_stop_name,
            "departure_stop_description": self.departure_stop_description,
            "departure_platform_name": self.departure_platform_name,
            "departure_platform_code": self.departure_platform_code,
            "departure_time": self.departure_time,
            "departure_delay": self.departure_delay,
            "departure_time_to": self.departure_time_to,
            "departure_status": self.departure_status,
            "arrival_stop_name": self.arrival_stop_name,
            "arrival_stop_description": self.arrival_stop_description,
            "arrival_platform_name": self.arrival_platform_name,
            "arrival_platform_code": self.arrival_platform_code,
            "arrival_time": self.arrival_time,
            "arrival_delay": self.arrival_delay,
            "arrival_time_to": self.arrival_time_to,
            "arrival_status": self.arrival_status,
        }
        props_str = "\n".join(f"{name}: {value!r}" for name, value in properties.items())

        alert = [
            f"{alert.lifecycle}:{alert.effect}:{alert.severity}: {alert.short_header}" 
            for alert in self.mbta_alerts 
        ]
        alerts_str = "\n".join(f"({i + 1}):{alert}" for i, alert in enumerate(alert))

        return f"Trip:\n{props_str}\n{alerts_str}\n"


    @property
    def departure_stop(self) -> Optional[TripStop]:
        return self.get_stop_by_type(StopType.DEPARTURE) if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def arrival_stop(self) -> Optional[TripStop]:
        return self.get_stop_by_type(StopType.ARRIVAL) if self.get_stop_by_type(StopType.ARRIVAL) else None

    @property
    def route_name(self) -> Optional[str]:
        if self.mbta_route and self.mbta_route.type in [0,1,2,4]: #subway + train + ferry
            return self.route_long_name
        elif self.mbta_route and self.mbta_route.type == 3: #bus
            return self.route_short_name
    
    @property
    def route_id(self) -> Optional[str]:
        return self.mbta_route.id if self.mbta_route else None
    
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
        return (
            self.mbta_route.direction_destinations[self.mbta_trip.direction_id]
            if self.mbta_trip and self.mbta_route
            else None
        )

    @property
    def direction(self) -> Optional[str]:
        return (
            self.mbta_route.direction_names[self.mbta_trip.direction_id]
            if self.mbta_trip and self.mbta_route
            else None
        )

    @property
    def duration(self) -> Optional[int]:
        if self.departure_stop and self.arrival_stop:
            return TripStop.calculate_time_difference(
                self.arrival_stop.get_time(), self.departure_stop.get_time()
            )
        return None

    @property
    def vehicle_current_status(self) -> Optional[str]:
        return self.mbta_vehicle.current_status if self.mbta_vehicle else None
 
    @property
    def vehicle_current_stop_sequence(self) -> Optional[str]:
        return self.mbta_vehicle.current_stop_sequence if self.mbta_vehicle else None
       
    @property
    def vehicle_longitude(self) -> Optional[float]:
        return self.mbta_vehicle.longitude if self.mbta_vehicle else None

    @property
    def vehicle_latitude(self) -> Optional[float]:
        return self.mbta_vehicle.latitude if self.mbta_vehicle else None

    @property
    def vehicle_occupancy_status(self) -> Optional[str]:
        return self.mbta_vehicle.occupancy_status if self.mbta_vehicle else None

    @property
    def vehicle_last_update_datetime(self) -> Optional[datetime]:
        return TripStop.parse_datetime(self.mbta_vehicle.updated_at) if self.mbta_vehicle else None
    
    @property
    def vehicle_last_update(self) -> Optional[int]:
        now = datetime.now().astimezone()
        if self.mbta_vehicle:
            return TripStop.time_to(now, TripStop.parse_datetime(self.mbta_vehicle.updated_at))
        else: 
            return None
 
    @property
    def departure_stop_name(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.DEPARTURE).mbta_stop.name if self.get_stop_by_type(StopType.DEPARTURE).mbta_stop else None

    @property
    def arrival_stop_name(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.ARRIVAL).mbta_stop.name if self.get_stop_by_type(StopType.ARRIVAL).mbta_stop else None

    @property
    def departure_stop_description(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.DEPARTURE).mbta_stop.description if self.get_stop_by_type(StopType.DEPARTURE).mbta_stop else None

    @property
    def arrival_stop_description(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.ARRIVAL).mbta_stop.description if self.get_stop_by_type(StopType.ARRIVAL).mbta_stop else None
    @property
    def departure_platform_name(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.DEPARTURE).mbta_stop.platform_name if self.get_stop_by_type(StopType.DEPARTURE).mbta_stop else None

    @property
    def arrival_platform_name(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.ARRIVAL).mbta_stop.platform_name if self.get_stop_by_type(StopType.ARRIVAL).mbta_stop else None

    @property
    def departure_platform_code(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.DEPARTURE).mbta_stop.platform_code if self.get_stop_by_type(StopType.DEPARTURE).mbta_stop else None

    @property
    def arrival_platform_code(self) -> Optional[str]:
        return self.get_stop_by_type(StopType.ARRIVAL).mbta_stop.platform_code if self.get_stop_by_type(StopType.ARRIVAL).mbta_stop else None
    
    @property
    def departure_time(self) -> Optional[str]:
       return self.departure_datetime.isoformat() if self.departure_datetime else None

    @property
    def arrival_time(self) -> Optional[str]:
        return self.arrival_datetime.isoformat() if self.arrival_datetime else None

    @property
    def departure_datetime(self) -> Optional[datetime]:
       return self.get_stop_by_type(StopType.DEPARTURE).get_time() if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def arrival_datetime(self) -> Optional[datetime]:
        return self.get_stop_by_type(StopType.ARRIVAL).get_time() if self.get_stop_by_type(StopType.ARRIVAL) else None
    
    @property
    def departure_delay(self) -> Optional[int]:
        return self.get_stop_by_type(StopType.DEPARTURE).get_delay() if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def arrival_delay(self) -> Optional[int]:
        return self.get_stop_by_type(StopType.ARRIVAL).get_delay() if self.get_stop_by_type(StopType.ARRIVAL) else None

    @property
    def departure_time_to(self) -> Optional[int]:
        return self.get_stop_by_type(StopType.DEPARTURE).get_time_to() if self.get_stop_by_type(StopType.DEPARTURE) else None
    
    @property
    def arrival_time_to(self) -> Optional[int]:
        return self.get_stop_by_type(StopType.ARRIVAL).get_time_to() if self.get_stop_by_type(StopType.ARRIVAL) else None
    
    @property
    def departure_status(self) -> Optional[str]:
        return self.stop_countdown(StopType.DEPARTURE) if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def arrival_status(self) -> Optional[str]:
        return self.stop_countdown(StopType.ARRIVAL) if self.get_stop_by_type(StopType.ARRIVAL) else None


    def add_stop(self, stop_type: str, scheduling_data: Union[MBTASchedule, MBTAPrediction], mbta_stop: MBTAStop) -> None:
        """Add or update a stop in the journey."""
        stop = self.get_stop_by_type(stop_type)

        if stop is None:
            # Create a new TripStop
            stop = TripStop(
                stop_type=stop_type,
                mbta_stop=mbta_stop,
                arrival_time=scheduling_data.arrival_time,
                departure_time=scheduling_data.departure_time,
                stop_sequence=scheduling_data.stop_sequence,
            )
            self.stops.append(stop)
        else:
            # Update existing TripStop
            stop.update_stop(
                mbta_stop=mbta_stop,
                arrival_time=scheduling_data.arrival_time,
                departure_time=scheduling_data.departure_time,
                stop_sequence=scheduling_data.stop_sequence,
            )
        
    def reset_stops(self):
        self.stops = []    
        
    def get_stop_by_type(self, stop_type: str) -> Optional[TripStop]:
        return next((stop for stop in self.stops if stop and stop.stop_type == stop_type), None)

    def get_mbta_stop_ids(self) -> list[str]:
        """Return IDs of departure and arrival stops, excluding None."""
        stop_ids = [
            self.get_mbta_stop_ids_by_type(StopType.DEPARTURE),
            self.get_mbta_stop_ids_by_type(StopType.ARRIVAL),
        ]
        return [stop_id for stop_id in stop_ids if stop_id is not None]
    
    def get_mbta_stop_ids_by_type(self, stop_type: str) -> list[str]:
        """Return IDs of the stop of the given type."""
        stop: TripStop = self.get_stop_by_type(stop_type)
        return stop.mbta_stop.id if stop and stop.mbta_stop else None
       
    def alert_header(self, alert_index: int) -> Optional[str]:
        if 0 <= alert_index < len(self.mbta_alerts):
            return self.mbta_alerts[alert_index].header
        return None

    def stop_countdown(self, stop_type: StopType) -> Optional[str]:
        """Determine the countdown or status of a stop based on vehicle and time."""
        stop = self.get_stop_by_type(stop_type)
        if not stop or not self.mbta_vehicle:
            return None

        target_time = self.get_stop_by_type(stop_type).get_time()
        if not target_time:
            return None

        now = datetime.now().astimezone()
        minutes = int((target_time - now).total_seconds() // 60)

        if self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
            status = self.mbta_vehicle.current_status
            if status == "STOPPED_AT":
                return "BOARDING"
            if status == "INCOMING_AT":
                return "ARRIVING NOW"
            if status == "IN_TRANSIT_TO":
                if minutes >= 0:
                    return f"ARRIVING < {minutes + 1} min"
                else:
                    return "ARRIVING"

        return "DEPARTED" if self.mbta_vehicle.current_stop_sequence > stop.stop_sequence else "EN ROUTE"

