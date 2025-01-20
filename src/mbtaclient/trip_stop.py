from enum import Enum
from typing import Optional
from datetime import datetime

from .models.mbta_stop import MBTAStop

class StopType(Enum):
    DEPARTURE = 'departure'
    ARRIVAL = 'arrival'
    
class TripStop:
    """A trip stop object to hold and manage arrival and departure details."""

    def __init__(self, stop_type: StopType, mbta_stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int, ) -> None:
        
        self.stop_type = stop_type
        self.mbta_stop: MBTAStop = mbta_stop

        self.arrival_time = TripStop.parse_datetime(arrival_time)
        self.real_arrival_time = None
        self.arrival_delay = None

        self.departure_time = TripStop.parse_datetime(departure_time)
        self.real_departure_time = None
        self.departure_delay = None

        self.stop_sequence = stop_sequence

    def __repr__(self) -> str:
        return f"TripStop({self.mbta_stop.name})"
    
    def update_stop(self, mbta_stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: str, ) -> None:
        """Update the stop details, including real arrival and departure times, uncertainties, and delays."""
        self.mbta_stop = mbta_stop
        self.stop_sequence = stop_sequence

        if arrival_time is None and departure_time is None:
            self.arrival_time = None
            self.real_arrival_time = None
            self.arrival_delay = None
            self.departure_time = None
            self.real_departure_time = None
            self.departure_delay = None
        else:
            if arrival_time is not None:
                self.real_arrival_time = TripStop.parse_datetime(arrival_time)
                if self.arrival_time is not None:
                    self.arrival_delay = TripStop.calculate_time_difference(
                        self.real_arrival_time, self.arrival_time
                    )
            if departure_time is not None:
                self.real_departure_time = TripStop.parse_datetime(departure_time)
                if self.departure_time is not None:
                    self.departure_delay = TripStop.calculate_time_difference(
                        self.real_departure_time, self.departure_time
                    )

    def get_time(self) -> Optional[datetime]:
        """Return the most relevant time for the stop."""
        if self.real_arrival_time is not None:
            return self.real_arrival_time
        if self.real_departure_time is not None:
            return self.real_departure_time
        if self.arrival_time is not None:
            return self.arrival_time
        if self.departure_time is not None:
            return self.departure_time
        return None

    def get_delay(self) -> Optional[int]:
        """Return the most relevant delay for the stop."""
        if self.arrival_delay is not None:
            return int(round(self.arrival_delay, 0))
        if self.departure_delay is not None:
            return int(round(self.departure_delay, 0))
        return None

    def get_time_to(self) -> Optional[int]:
        """Return the most relevant time to for the stop."""
        now = datetime.now().astimezone()
        if self.real_arrival_time is not None:
            return TripStop.time_to(self.real_arrival_time, now)
        if self.real_departure_time is not None:
            return TripStop.time_to(self.real_departure_time, now)
        if self.arrival_time is not None:
            return TripStop.time_to(self.arrival_time, now)
        if self.departure_time is not None:
            return TripStop.time_to(self.departure_time, now)

    @staticmethod
    def parse_datetime(time_str: str) -> Optional[datetime]:
        """Parse a string in ISO 8601 format to a datetime object."""
        if not isinstance(time_str, str):
            return None
        try:
            return datetime.fromisoformat(time_str)
        except ValueError as e:
            return None

    @staticmethod
    def calculate_time_difference(time1: Optional[datetime], time2: Optional[datetime]) -> Optional[int]:
        if time1 is None or time2 is None:
            return None
        return int(round((time1 - time2).total_seconds(), 0))

    @staticmethod
    def time_to(time: Optional[datetime], now: datetime) -> Optional[int]:
        if time is None:
            return None
        # Ensure both datetime objects have timezone info
        if time.tzinfo != now.tzinfo:
            if time.tzinfo is None:
                time = time.replace(tzinfo=now.tzinfo)
            elif now.tzinfo is None:
                now = now.replace(tzinfo=None)
        return int(round((time - now).total_seconds(), 0))
