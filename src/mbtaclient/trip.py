from dataclasses import dataclass, field
from typing import Union, Optional
from datetime import datetime

from .mbta_object_store import MBTAAlertObjStore, MBTARouteObjStore, MBTAStopObjStore, MBTATripObjStore, MBTAVehicleObjStore

from .stop import Stop, StopType

from .models.mbta_schedule import MBTASchedule
from .models.mbta_prediction import MBTAPrediction
from .models.mbta_route import MBTARoute
from .models.mbta_trip import MBTATrip
from .models.mbta_vehicle import MBTAVehicle
from .models.mbta_alert import MBTAAlert


@dataclass
class Trip:
    """A class to manage a Trip with multiple stops."""
    _mbta_route_id: Optional[str] = None
    _mbta_trip_id: Optional[str] = None
    _mbta_vehicle_id: Optional[str] = None
    _mbta_alerts_ids: set[Optional[str]] = field(default_factory=set)
    stops: list[Optional['Stop']] = field(default_factory=list)

    VEHICLE_DATA_FRESHNESS_THRESHOLD = 90  # seconds

    # registry
    @property
    def mbta_route(self) -> Optional[MBTARoute]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_route = MBTARouteObjStore.get_by_id(self._mbta_route_id)
        if mbta_route:
            return mbta_route
        #self._mbta_route_id = None
        return None

    @mbta_route.setter
    def mbta_route(self, mbta_route: MBTARoute) -> None:
        if mbta_route:
            self._mbta_route_id = mbta_route.id
            MBTARouteObjStore.store(mbta_route)

    @property
    def mbta_trip(self) -> Optional[MBTATrip]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_trip = MBTATripObjStore.get_by_id(self._mbta_trip_id)
        if mbta_trip:
            return mbta_trip
        return None

    @mbta_trip.setter
    def mbta_trip(self, mbta_trip: MBTATrip) -> None:
        if mbta_trip:
            self._mbta_trip_id = mbta_trip.id
            MBTATripObjStore.store(mbta_trip)

    @property
    def mbta_vehicle(self) -> Optional[MBTAVehicle]:
        """Retrieve the MBTARoute object for this Trip."""
        return MBTAVehicleObjStore.get_by_id(self._mbta_vehicle_id)

    @mbta_vehicle.setter
    def _mbta_vehicle(self, mbta_vehicle: MBTAVehicle) -> None:
        if mbta_vehicle:
            self._mbta_vehicle_id = mbta_vehicle.id
            MBTAVehicleObjStore.store(mbta_vehicle)

    @property
    def mbta_alerts(self) -> Optional[list[MBTAAlert]]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_alerts = []
        for mbta_alert_id in self._mbta_alerts_ids:
            mbta_alerts.append(MBTAAlertObjStore.get_by_id(mbta_alert_id))
        return mbta_alerts

    @mbta_alerts.setter
    def _mbta_alerts(self, mbta_alerts: list[MBTAAlert]) -> None:
        if mbta_alerts:
            for mbta_alert in mbta_alerts:
                self._mbta_alerts_ids.add(mbta_alert.id)
                MBTAAlertObjStore.store(mbta_alert)

    # trip
    @property
    def headsign(self) -> Optional[str]:
        return self.mbta_trip.headsign if self.mbta_trip and self.mbta_trip.headsign else None

    @property
    def name(self) -> Optional[str]:
        return self.mbta_trip.name if self.mbta_trip and self.mbta_trip.name else None

    @property
    def destination(self) -> Optional[str]:
        return (
            self.mbta_route.direction_destinations[self.mbta_trip.direction_id]
            if self.mbta_trip
            and self.mbta_trip.direction_id
            and self.mbta_route
            and self.mbta_route.direction_destinations
            else None
        )

    @property
    def direction(self) -> Optional[str]:
        return (
            self.mbta_route.direction_names[self.mbta_trip.direction_id]
            if self.mbta_trip
            and self.mbta_trip.direction_id
            and self.mbta_route
            and self.mbta_route.direction_names
            else None
        )

    @property
    def duration(self) -> Optional[int]:
        if self._departure_stop and self._arrival_stop:
            return int((self._arrival_stop.time -  self._departure_stop.time).total_seconds())
        return None

    # route
    @property
    def route_name(self) -> Optional[str]:
        if self.mbta_route and self.mbta_route.type in [0,1,2,4]: #subway + train + ferry
            return self.mbta_route.long_name if self.mbta_route and self.mbta_route.long_name else None
        elif self.mbta_route and self.mbta_route.type == 3: #bus
            return self.mbta_route.short_name if self.mbta_route and self.mbta_route.short_name else None

    @property
    def route_color(self) -> Optional[str]:
        return f"#{self.mbta_route.color}" if self.mbta_route and self.mbta_route.color else None

    @property
    def route_description(self) -> Optional[str]:
        return MBTARoute.get_route_type_desc_by_type_id(self.mbta_route.type) if self.mbta_route and self.mbta_route.type is not None else None

    # vehicle
    @property
    def vehicle_status(self) -> Optional[str]:
        if self.mbta_vehicle and self.mbta_vehicle.current_status and self.vehicle_stop_name:
            title_case_with_spaces = " ".join([word.capitalize() for word in self.mbta_vehicle.current_status.split("_")])
            return title_case_with_spaces + " " + self.vehicle_stop_name
        return None

    @property
    def vehicle_stop_name(self) -> Optional[str]:
        return MBTAStopObjStore.get_by_child_stop_id(self.mbta_vehicle.stop_id).name if self.mbta_vehicle and self.mbta_vehicle.stop_id and MBTAStopObjStore.get_by_child_stop_id(self.mbta_vehicle.stop_id) else None

    @property
    def vehicle_longitude(self) -> Optional[float]:
        return self.mbta_vehicle.longitude if self.mbta_vehicle and self.mbta_vehicle.longitude else None

    @property
    def vehicle_latitude(self) -> Optional[float]:
        return self.mbta_vehicle.latitude if self.mbta_vehicle and self.mbta_vehicle.latitude else None

    @property
    def vehicle_occupancy(self) -> Optional[str]:
        return self.mbta_vehicle.occupancy_status if self.mbta_vehicle and self.mbta_vehicle.occupancy_status else None

    @property
    def vehicle_speed(self) -> Optional[str]:
        return self.mbta_vehicle.speed if self.mbta_vehicle and self.mbta_vehicle.speed else None

    @property
    def vehicle_updated_at(self) -> Optional[datetime]:
        return self.mbta_vehicle.updated_at.replace(tzinfo=None) if self.mbta_vehicle and self.mbta_vehicle.updated_at else None

    @property
    def is_vehicle_data_fresh(self) -> bool:
        if self.mbta_vehicle and self.mbta_vehicle.updated_at:
            now =  datetime.now().astimezone() # Ensure consistent timezone handling
            delta = (now - self.mbta_vehicle.updated_at).total_seconds()
            return delta <= self.VEHICLE_DATA_FRESHNESS_THRESHOLD
        return False

    #departure stop
    @property
    def _departure_stop(self) -> Optional[Stop]:
        return self.get_stop_by_type(StopType.DEPARTURE) if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def departure_stop_name(self) -> Optional[str]:
        return self._departure_stop.mbta_stop.name if self._departure_stop and self._departure_stop.mbta_stop else None

    @property
    def departure_platform(self) -> Optional[str]:
        return self._departure_stop.mbta_stop.platform_name if self._departure_stop and self._departure_stop.mbta_stop else None

    @property
    def departure_time(self) -> Optional[datetime]:
        return self._departure_stop.time.replace(tzinfo=None) if self._departure_stop and self._departure_stop.time else None

    @property
    def departure_delay(self) -> Optional[int]:
        return int(self._departure_stop.deltatime.total_seconds()) if self._departure_stop and self._departure_stop.deltatime else None

    @property
    def departure_time_to(self) -> Optional[int]:
        return int(self._departure_stop.time_to.total_seconds()) if self._departure_stop and self._departure_stop.time_to else None

    @property
    def departure_mbta_countdown(self) -> Optional[str]:
        return self._get_stop_mbta_countdown(StopType.DEPARTURE) if self._departure_stop else None

    @property
    def departure_countdown(self) -> Optional[str]:
        return self._get_stop_countdown(StopType.DEPARTURE) if self._departure_stop else None

    @property
    def has_departed(self) -> bool:
        stop = self._departure_stop
        if not stop:  # No departure stop available
            return False

        now = datetime.now().astimezone()
        seconds = (stop.departure_time.astimezone() - now).total_seconds() if stop.departure_time else stop.time
        current_stop = self.mbta_vehicle.current_stop_sequence if self.mbta_vehicle else None

        if current_stop is not None and current_stop > stop.stop_sequence:
            return True
        if seconds < -30:
            return True

        return False


    #arrival stop
    @property
    def _arrival_stop(self) -> Optional[Stop]:
        return self.get_stop_by_type(StopType.ARRIVAL) if self.get_stop_by_type(StopType.ARRIVAL) else None

    @property
    def arrival_stop_name(self) -> Optional[str]:
        return self._arrival_stop.mbta_stop.name if self._arrival_stop and self._arrival_stop.mbta_stop else None

    @property
    def arrival_platform(self) -> Optional[str]:
        return self._arrival_stop.mbta_stop.platform_name if self._arrival_stop and self._arrival_stop.mbta_stop else None

    @property
    def arrival_time(self) -> Optional[datetime]:
        return self._arrival_stop.time.replace(tzinfo=None) if self._arrival_stop and self._arrival_stop.time else None

    @property
    def arrival_delay(self) -> Optional[int]:
        return int(self._arrival_stop.deltatime.total_seconds()) if self._arrival_stop and self._arrival_stop.deltatime else None

    @property
    def arrival_time_to(self) -> Optional[int]:
        return int(self._arrival_stop.time_to.total_seconds()) if self._arrival_stop and self._arrival_stop.time_to else None

    @property
    def arrival_mbta_countdown(self) -> Optional[str]:
        return self._get_stop_mbta_countdown(StopType.ARRIVAL) if self._arrival_stop else None

    @property
    def arrival_countdown(self) -> Optional[str]:
        return self._get_stop_countdown(StopType.ARRIVAL) if self._arrival_stop else None

    @property
    def has_arrived(self) -> bool:
        stop = self._arrival_stop
        if not stop:  # No departure stop available
            return False

        now = datetime.now().astimezone()
        seconds = (stop.arrival_time.astimezone() - now).total_seconds() if stop.arrival_time else stop.time

        current_stop = self.mbta_vehicle.current_stop_sequence if self.mbta_vehicle else None

        if current_stop is not None and current_stop > stop.stop_sequence:
            return True
        if seconds < -30:
            return True

        return False

    #alerts
    @property
    def alerts(self) -> Optional[set[str]]:
        alerts_details = set()
        if self.mbta_alerts:
            for mbta_alert in self.mbta_alerts:
                effect = " ".join(mbta_alert.effect.split("_"))
                lifecycle = mbta_alert.lifecycle
                short_header = mbta_alert.short_header
                alerts_details.add(effect + "[" + lifecycle + "]: " + short_header)
            return alerts_details
        return None

    def get_stop_by_type(self, stop_type: str) -> Optional[Stop]:
        return next((stop for stop in self.stops if stop and stop.stop_type == stop_type), None)

    def add_stop(self, stop_type: str, scheduling: Union[MBTASchedule, MBTAPrediction], mbta_stop_id: str) -> None:
        """Add or update a stop in the journey."""
        stop = self.get_stop_by_type(stop_type)

        ##Status from prediction
        status = None
        if isinstance(scheduling, MBTAPrediction) and scheduling.status:
            status = scheduling.status

        if stop is None:
            # Create a new Stop
            stop = Stop(
                stop_type=stop_type,
                mbta_stop_id=mbta_stop_id,
                stop_sequence=scheduling.stop_sequence,
                arrival_time=scheduling.arrival_time,
                departure_time=scheduling.departure_time,
                status=status
            )
            self.stops.append(stop)
        else:
            # Update existing Stop
            stop.update_stop(
                mbta_stop_id=mbta_stop_id,
                stop_sequence=scheduling.stop_sequence,
                arrival_time=scheduling.arrival_time,
                departure_time=scheduling.departure_time,
                status=status
            )

    def remove_stop_by_id(self, mbta_stop_id: str) -> None:
        self.stops = [stop for stop in self.stops if stop.mbta_stop.id != mbta_stop_id]

    def reset_stops(self):
        self.stops = []

    def get_stop_id_by_stop_type(self, stop_type: StopType) -> Optional[str]:
        """Return the stop ID of the stop of the given type."""
        if stop_type == StopType.DEPARTURE and self._departure_stop and self._departure_stop.mbta_stop:
            return self._departure_stop.mbta_stop.id
        if stop_type == StopType.ARRIVAL and self._arrival_stop and self._arrival_stop.mbta_stop:
            return self._arrival_stop.mbta_stop.id
        return None

    def get_stops_ids(self) -> list[str]:
        """Return IDs of departure and arrival stops, excluding None."""
        return [
            stop_id for stop_id in [
                self.get_stop_id_by_stop_type(StopType.DEPARTURE),
                self.get_stop_id_by_stop_type(StopType.ARRIVAL)
            ] if stop_id is not None
        ]

    def get_alert_header(self, alert_index: int) -> Optional[str]:
        if 0 <= alert_index < len(self.mbta_alerts):
            return self.mbta_alerts[alert_index].header
        return None

    def _get_stop_countdown(self, stop_type: StopType) -> Optional[str]:
        """Determine the countdown or status of a stop."""

        stop: Stop = self.get_stop_by_type(stop_type)
        if not stop:
            return None

        if stop.status:
            return stop.status

        if not stop.time:
            return None

        now = datetime.now().astimezone()

        # Calculate time deltas
        arrival_time = stop.arrival_time or stop.time
        departure_time = stop.departure_time or stop.time

        arrival_delta = arrival_time.astimezone() - now
        departure_delta = departure_time.astimezone() - now

        seconds_arrival = int(arrival_delta.total_seconds())
        seconds_departure = int(departure_delta.total_seconds())

        # Vehicle data overrides
        if self.mbta_vehicle and self.is_vehicle_data_fresh:

            vehicle_stop = self.mbta_vehicle.current_stop_sequence
            vehicle_status = self.mbta_vehicle.current_status

            if vehicle_stop > stop.stop_sequence:
                if stop_type == StopType.DEPARTURE:
                    return "Departed"
                if stop_type == StopType.ARRIVAL:
                    return "Arrived"

            if vehicle_stop == stop.stop_sequence:
                if stop_type == StopType.DEPARTURE and vehicle_status == "STOPPED_AT" and 0 <= seconds_departure <= 90:
                    return "Boarding"
                if vehicle_status == "INCOMING_AT" and 0 <= seconds_arrival <= 90:
                    return "Arriving"

        # Handle status messages
        if stop_type == StopType.DEPARTURE and seconds_departure < 0:
            return "Departed"
        if stop_type == StopType.ARRIVAL and seconds_arrival < 0:
            return "Arrived"

        # Prioritize boarding over arriving
        if stop_type == StopType.DEPARTURE and 0 <= seconds_departure < 30:
            return "Boarding"
        if 0 <= seconds_arrival < 30 and seconds_departure > 0:
            return "Arriving"

        # Default to formatted time countdown
        return self._format_time(seconds_arrival) if seconds_arrival >= 30 else None

    def _get_stop_mbta_countdown(self, stop_type: StopType) -> Optional[str]:
        """Determine the countdown to a stop based on vehicle and time following
        https://www.mbta.com/developers/v3-api/best-practices """

        stop = self.get_stop_by_type(stop_type)

        if stop:

            if stop.status:
                return stop.status

            if not stop.time:
                return None

            seconds = (stop.time.astimezone() - datetime.now().astimezone()).total_seconds()

            if seconds < 0:
                return None

            if seconds <= 90 and self.mbta_vehicle and self.mbta_vehicle.current_status == "STOPPED_AT" and self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
                return "BRD"

            if seconds <= 30:
                return "ARR"

            if seconds <= 60:
                return "1 min"

            minutes = int(seconds/60)

            if minutes > 20:
                return "20+ min"

            return f"{minutes} min"

        return None

   # Convert time to human-readable format
    def _format_time(self, seconds: int) -> Optional[str]:
        if seconds < 0:
            return None
        minutes = (seconds // 60) % 60
        hours = (seconds // 3600) % 24
        days = seconds // 86400

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        if hours > 0:
            return f"{hours}h {minutes}m"
        if minutes > 1:
            return f"{minutes} min"
        return "1 min"
