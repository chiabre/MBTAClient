from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

from .registries.mbta_strops import MBTAStopsRegistry
from .models.mbta_stop import MBTAStop

class StopType(Enum):
    DEPARTURE = "departure"
    ARRIVAL = "arrival"

@dataclass
class TripStopTime:
    """
    Represents a time with optional original and updated values.
    """
    original_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
        
    def __init__(self, original_time: Optional[datetime] = None):
        self.original_time = original_time
        self.updated_time: Optional[datetime] = None

    @property
    def delta(self) -> Optional[timedelta]:
        if self.original_time and self.updated_time:
            return self.original_time - self.updated_time
        return None

@dataclass
class TripStop:
    """
    Represents a stop on a trip.
    """
    stop_type: StopType
    mbta_stop_id: str
    stop_sequence: int 
    arrival_time: Optional[TripStopTime] = None 
    departure_time: Optional[TripStopTime] = None

    def __init__(self, stop_type: StopType, mbta_stop_id: str, stop_sequence: int, arrival_time: Optional[datetime] = None, departure_time: Optional[datetime] = None, ):
        """
        Inits the stop.

        Args:
            stop_type: the stop type (DEPARTURE|ARRIVAL)
            mbta_stop_id: The MBTA stop ID.
            stop_sequence: The stop sequence.
            arrival_time: The arrival time.
            departure_time: The departure time.
        """
        self.stop_type = stop_type
        self.mbta_stop_id = mbta_stop_id
        self.stop_sequence = stop_sequence
        self.arrival_time = TripStopTime(arrival_time) if arrival_time else None 
        self.departure_time = TripStopTime(departure_time) if departure_time else None

    def update_stop(self, mbta_stop_id: str ,stop_sequence: int,arrival_time: Optional[datetime] = None, departure_time: Optional[datetime] = None, ) -> None:
        """
        Updates the stop with new information.

        Args:
            mbta_stop_id: The new MBTA stop ID.
            stop_sequence: The new stop sequence.
            arrival_time: The new arrival time.
            departure_time: The new departure time.
        """
        self.mbta_stop_id = mbta_stop_id
        self.stop_sequence = stop_sequence
        
        if arrival_time:
            if not self.arrival_time:
                self.arrival_time = TripStopTime(arrival_time)
            else:
                self.arrival_time.updated_time = arrival_time
        if departure_time:
            if not self.departure_time:
                self.departure_time = TripStopTime(departure_time)
            else:
                self.departure_time.updated_time = departure_time
            
    @property
    def mbta_stop(self) -> Optional[MBTAStop]:
        """Retrieve the MBTAStop object for this TripStop."""
        return MBTAStopsRegistry.get_mbta_stop(self.mbta_stop_id)

    @mbta_stop.setter
    def mbta_stop(self, mbta_stop: "MBTAStop") -> None:
        """Set the MBTAStop and add it to the registry."""
        self.mbta_stop_id = mbta_stop.id  # Update the stop ID
        MBTAStopsRegistry.register_mbta_stop(mbta_stop.id, mbta_stop)  # Add to registry

    @property
    def time(self) -> Optional[datetime]:
        """Returns the most recent time for this stop (updated or original)."""
        if self.arrival_time and self.arrival_time.updated_time:
            return self.arrival_time.updated_time
        elif self.departure_time and self.departure_time.updated_time:
            return self.departure_time.updated_time
        elif self.arrival_time and self.arrival_time.original_time:
            return self.arrival_time.original_time
        elif self.departure_time and self.departure_time.original_time:
            return self.departure_time.original_time
        else:
            return None

    @property
    def deltatime(self) -> Optional[timedelta]:
        if self.arrival and self.arrival_time.delta:
            return self.arrival_time.delta
        if self.departure_time and self.departure_time.delta:
            return self.departure_time.delta
        return None

    @property
    def time_to(self) -> Optional[timedelta]:
        if self.time:
            return self.time - datetime.now()
        return None