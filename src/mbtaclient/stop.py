from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

from .mbta_object_store import MBTAStopObjStore
from .models.mbta_stop import MBTAStop

class StopType(Enum):
    DEPARTURE = "departure"
    ARRIVAL = "arrival"

@dataclass
class Time:
    """
    Represents a time with optional original and updated values.
    """
    scheduled_time: Optional[datetime] = None
    predicted_time: Optional[datetime] = None

    def __init__(self, scheduled_time: Optional[datetime] = None):
        self.scheduled_time = scheduled_time
        self.predicted_time: Optional[datetime] = None

    @property
    def deltatime(self) -> Optional[timedelta]:
        if self.scheduled_time and self.predicted_time:
            return self.predicted_time - self.scheduled_time
        if self.scheduled_time:
            return timedelta(seconds=0)
        return None

    @property
    def time(self) -> Optional[datetime]:
        return self.predicted_time or self.scheduled_time

@dataclass
class Stop:
    """
    Represents a stop on a trip.
    """
    stop_type: StopType
    mbta_stop_id: str
    stop_sequence: int
    arrival: Optional[Time] = None
    departure: Optional[Time] = None
    status: Optional[str] = None

    def __init__(
        self,
        stop_type: StopType,
        mbta_stop_id: str,
        stop_sequence: int,
        arrival_time: Optional[datetime] = None,
        departure_time: Optional[datetime] = None,
        status: Optional[str] = None):
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
        self.arrival = Time(scheduled_time=arrival_time) if arrival_time else None
        self.departure = Time(scheduled_time=departure_time) if departure_time else None
        self.status = status

    @property
    def mbta_stop(self) -> Optional[MBTAStop]:
        """Retrieve the MBTAStop object for this TripStop."""
        mbta_stop = MBTAStopObjStore.get_by_id(self.mbta_stop_id)
        if mbta_stop:
            return mbta_stop
        return None

    @mbta_stop.setter
    def mbta_stop(self, mbta_stop: "MBTAStop") -> None:
        """Set the MBTAStop and add it to the registry."""
        self.mbta_stop_id = mbta_stop.id  # Update the stop ID
        MBTAStopObjStore.store(mbta_stop)  # Add to store

    @property
    def arrival_time(self) -> Optional[datetime]:
        if self.arrival and self.arrival.time:
            return self.arrival.time
        return None

    @property
    def departure_time(self) -> Optional[datetime]:
        if self.departure and self.departure.time:
            return self.departure.time
        return None

    @property
    def time(self) -> Optional[datetime]:
        """Returns the most recent time for this stop (updated or original)."""
        if self.arrival:
            return self.arrival.time
        elif self.departure:
            return self.departure.time
        else:
            return None

    @property
    def deltatime(self) -> Optional[timedelta]:
        if self.arrival and self.arrival.deltatime:
            return self.arrival.deltatime
        if self.departure and self.departure.deltatime:
            return self.departure.deltatime
        return None

    @property
    def time_to(self) -> Optional[timedelta]:
        if self.time:
            return self.time.astimezone() - datetime.now().astimezone()
        return None
    
    @property
    def time_to_departure(self) -> Optional[timedelta]:
        if self.departure_time:
            return self.departure_time.astimezone() - datetime.now().astimezone()
        return None
    
    @property
    def time_to_arrival(self) -> Optional[timedelta]:
        if self.arrival_time:
            return self.arrival_time.astimezone() - datetime.now().astimezone()
        return None

    def __repr__(self) -> str:
        return (f"TripStop({self.stop_type.value}): {self.mbta_stop_id} @ {self.time.replace(tzinfo=None)}"
        )

    def update_stop(
        self,
        mbta_stop_id: str,
        stop_sequence: int,
        arrival_time: Optional[datetime] = None,
        departure_time: Optional[datetime] = None,
        status: Optional[str] = None) -> None:
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
        self.status = status

        if arrival_time:
            if not self.arrival:
                self.arrival = Time(scheduled_time=arrival_time)
            else:
                self.arrival.predicted_time = arrival_time
        if departure_time:
            if not self.departure:
                self.departure = Time(scheduled_time=departure_time)
            else:
                self.departure.predicted_time = departure_time
