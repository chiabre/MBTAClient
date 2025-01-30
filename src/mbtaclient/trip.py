from dataclasses import dataclass, field
from typing import Union, Optional
from datetime import datetime, timedelta

from .mbta_object_store import MBTAAlertObjStore, MBTARouteObjStore, MBTATripObjStore, MBTAVehicleObjStore

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
    mbta_route_id: Optional[str] = None
    mbta_trip_id: Optional[str] = None
    mbta_vehicle_id: Optional[str] = None
    mbta_alerts_ids: set[Optional[str]] = field(default_factory=set)
    stops: list[Optional['Stop']] = field(default_factory=list)

    # registry 
    @property
    def mbta_route(self) -> Optional[MBTARoute]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_route = MBTARouteObjStore.get_by_id(self.mbta_route_id)
        if mbta_route:
            return mbta_route
        #self.mbta_route_id = None
        return None
    
    @mbta_route.setter
    def mbta_route(self, mbta_route: MBTARoute) -> None:
        if mbta_route:
            self.mbta_route_id = mbta_route.id
            MBTARouteObjStore.store(mbta_route)
        
    @property
    def mbta_trip(self) -> Optional[MBTATrip]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_trip = MBTATripObjStore.get_by_id(self.mbta_trip_id)
        if mbta_trip:
            return mbta_trip
        #self.mbta_trip = None
        return None
    
    @mbta_trip.setter
    def mbta_trip(self, mbta_trip: MBTATrip) -> None:
        if mbta_trip:
            self.mbta_trip_id = mbta_trip.id
            MBTATripObjStore.store(mbta_trip)

    @property
    def mbta_vehicle(self) -> Optional[MBTAVehicle]:
        """Retrieve the MBTARoute object for this Trip."""
        return MBTAVehicleObjStore.get_by_id(self.mbta_vehicle_id)
    
    @mbta_vehicle.setter
    def mbta_vehicle(self, mbta_vehicle: MBTAVehicle) -> None:
        if mbta_vehicle:
            self.mbta_vehicle_id = mbta_vehicle.id
            MBTAVehicleObjStore.store(mbta_vehicle)
            
    @property
    def mbta_alerts(self) -> Optional[list[MBTAAlert]]:
        """Retrieve the MBTARoute object for this Trip."""
        mbta_alerts = []
        for mbta_alert_id in self.mbta_alerts_ids:
            mbta_alerts.append(MBTAAlertObjStore.get_by_id(mbta_alert_id))
        return mbta_alerts
    
    @mbta_alerts.setter
    def mbta_alerts(self, mbta_alerts: list[MBTAAlert]) -> None:
        if mbta_alerts:
            for mbta_alert in mbta_alerts:
                self.mbta_alerts_ids.add(mbta_alert.id)
                MBTAAlertObjStore.store(mbta_alert)
 
    # trip
    @property
    def headsign(self) -> Optional[str]:
        return self.mbta_trip.headsign if self.mbta_trip and self.mbta_trip.headsign else None

    @property
    def name(self) -> Optional[str]:
        return self.mbta_trip.name if self.mbta_trip and self.mbta_trip.name else None

    @property
    def direction_destination(self) -> Optional[str]:
        return (
            self.mbta_route.direction_destinations[self.mbta_trip.direction_id]
            if self.mbta_trip and self.mbta_trip.direction_id and self.mbta_route and self.mbta_route.direction_destinations
            else None
        )

    @property
    def direction_name(self) -> Optional[str]:
        return (
            self.mbta_route.direction_names[self.mbta_trip.direction_id]
            if self.mbta_trip and self.mbta_trip.direction_id and self.mbta_route and self.mbta_route.direction_names
            else None
        )

    @property
    def duration(self) -> Optional[timedelta]:
        if self.departure_stop and self.arrival_stop:
            return self.arrival_stop.time -  self.departure_stop.time
        return None

    # route
    @property
    def route_name(self) -> Optional[str]:
        if self.mbta_route and self.mbta_route.type in [0,1,2,4]: #subway + train + ferry
            return self.route_long_name
        elif self.mbta_route and self.mbta_route.type == 3: #bus
            return self.route_short_name
    
    @property
    def route_id(self) -> Optional[str]:
        return self.mbta_route.id if self.mbta_route and self.mbta_route.id else None
    
    @property
    def route_short_name(self) -> Optional[str]:
        return self.mbta_route.short_name if self.mbta_route and self.mbta_route.short_name else None

    @property
    def route_long_name(self) -> Optional[str]:
        return self.mbta_route.long_name if self.mbta_route and self.mbta_route.long_name else None

    @property
    def route_color(self) -> Optional[str]:
        return self.mbta_route.color if self.mbta_route and self.mbta_route.color else None

    @property
    def route_description(self) -> Optional[str]:
        return MBTARoute.get_route_type_desc_by_type_id(self.mbta_route.type) if self.mbta_route and self.mbta_route.type is not None else None

    @property
    def route_type(self) -> Optional[str]:
        return self.mbta_route.type if self.mbta_route and self.mbta_route.type is not None else None

    # vehicle
    @property
    def vehicle_current_status(self) -> Optional[str]:
        return self.mbta_vehicle.current_status if self.mbta_vehicle and self.mbta_vehicle.current_status else None
 
    @property
    def vehicle_current_stop_sequence(self) -> Optional[str]:
        return self.mbta_vehicle.current_stop_sequence if self.mbta_vehicle and self.mbta_vehicle.current_stop_sequence else None
       
    @property
    def vehicle_longitude(self) -> Optional[float]:
        return self.mbta_vehicle.longitude if self.mbta_vehicle and self.mbta_vehicle.longitude else None

    @property
    def vehicle_latitude(self) -> Optional[float]:
        return self.mbta_vehicle.latitude if self.mbta_vehicle and self.mbta_vehicle.latitude else None

    @property
    def vehicle_occupancy_status(self) -> Optional[str]:
        return self.mbta_vehicle.occupancy_status if self.mbta_vehicle and self.mbta_vehicle.occupancy_status else None

    @property
    def vehicle_updated_at(self) -> Optional[datetime]:
        return self.mbta_vehicle.updated_at if self.mbta_vehicle and self.mbta_vehicle.updated_at else None
    
    #departure stop
    @property
    def departure_stop(self) -> Optional[Stop]:
        return self.get_stop_by_type(StopType.DEPARTURE) if self.get_stop_by_type(StopType.DEPARTURE) else None

    @property
    def departure_stop_name(self) -> Optional[str]:
        return self.departure_stop.mbta_stop.name if self.departure_stop and self.departure_stop.mbta_stop else None

    @property
    def departure_platform_name(self) -> Optional[str]:
        return self.departure_stop.mbta_stop.platform_name if self.departure_stop and self.departure_stop.mbta_stop else None

    @property
    def departure_time(self) -> Optional[datetime]:
       return self.departure_stop.time if self.departure_stop and self.departure_stop.time else None

    @property
    def departure_deltatime(self) -> Optional[int]:
        return self.departure_stop.deltatime if self.departure_stop and self.departure_stop.deltatime else None

    @property
    def departure_time_to(self) -> Optional[timedelta]:
        return self.departure_stop.time_to if self.departure_stop and self.departure_stop.time_to else None
   
    @property
    def departure_status(self) -> Optional[str]:
        return self._get_stop_countdown(StopType.DEPARTURE) if self.departure_stop else None

    #arrival stop
    @property
    def arrival_stop(self) -> Optional[Stop]:
        return self.get_stop_by_type(StopType.ARRIVAL) if self.get_stop_by_type(StopType.ARRIVAL) else None

    @property
    def arrival_stop_name(self) -> Optional[str]:
        return self.arrival_stop.mbta_stop.name if self.arrival_stop and self.arrival_stop.mbta_stop else None

    @property
    def arrival_platform_name(self) -> Optional[str]:
        return self.arrival_stop.mbta_stop.platform_name if self.arrival_stop and self.arrival_stop.mbta_stop else None

    @property
    def arrival_time(self) -> Optional[datetime]:
       return self.arrival_stop.time if self.arrival_stop and self.arrival_stop.time else None

    @property
    def arrival_deltatime(self) -> Optional[timedelta]:
        return self.arrival_stop.deltatime if self.arrival_stop and self.arrival_stop.deltatime else None

    @property
    def arrival_time_to(self) -> Optional[timedelta]:
        return self.arrival_stop.time_to if self.arrival_stop and self.arrival_stop.time_to else None
   
    @property
    def arrival_status(self) -> Optional[str]:
        return self._get_stop_countdown(StopType.ARRIVAL) if self.arrival_stop else None
    
    def get_stop_by_type(self, stop_type: str) -> Optional[Stop]:
        return next((stop for stop in self.stops if stop and stop.stop_type == stop_type), None) 
    
    def add_stop(self, stop_type: str, scheduling: Union[MBTASchedule, MBTAPrediction], mbta_stop_id: str) -> None:
        """Add or update a stop in the journey."""
        stop = self.get_stop_by_type(stop_type)
        

        if stop is None:
            # Create a new Stop
            stop = Stop(
                stop_type=stop_type,
                mbta_stop_id=mbta_stop_id,
                stop_sequence=scheduling.stop_sequence,
                arrival_time=scheduling.arrival_time,
                departure_time=scheduling.departure_time,
            )
            self.stops.append(stop)
        else:
            # Update existing Stop
            stop.update_stop(
                mbta_stop_id=mbta_stop_id,
                stop_sequence=scheduling.stop_sequence,
                arrival_time=scheduling.arrival_time,
                departure_time=scheduling.departure_time,
                
            )
    
    def remove_stop_by_id(self, mbta_stop_id: str) -> None:
        self.stops = [stop for stop in self.stops if stop.mbta_stop.id != mbta_stop_id]

    def reset_stops(self):
        self.stops = []    
            
    def get_stop_id_by_stop_type(self, stop_type: StopType) -> Optional[str]:
        """Return the stop ID of the stop of the given type."""
        if stop_type == StopType.DEPARTURE and self.departure_stop and self.departure_stop.mbta_stop:
            return self.departure_stop.mbta_stop.id
        if stop_type == StopType.ARRIVAL and self.arrival_stop and self.arrival_stop.mbta_stop:
            return self.arrival_stop.mbta_stop.id
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
        """Determine the countdown or status of a stop based on vehicle and time."""
        stop = self.get_stop_by_type(stop_type)
        
        if not stop or not stop.time or not self.mbta_vehicle:
            return None

        now = datetime.now().astimezone()
        minutes = int((stop.time - now).total_seconds() // 60)

        if self.mbta_vehicle.current_stop_sequence == stop.stop_sequence:
            status = self.mbta_vehicle.current_status
            if status == "STOPPED_AT":
                if stop_type == StopType.DEPARTURE:
                    if minutes >= 5:
                        return f"DEPARTING < {minutes + 1} min"
                    return "BOARDING"
                else:
                    return "ARRIVED"
            if status == "INCOMING_AT":
                return "DUE"
            if status == "IN_TRANSIT_TO":
                if minutes >= 0:
                    return f"ARRIVING < {minutes + 1} min"
                else:
                    return "ARRIVING"

        if self.mbta_vehicle.current_stop_sequence and self.mbta_vehicle.current_stop_sequence > stop.stop_sequence:
            return "DEPARTED" 
        else: 
            return "EN ROUTE"