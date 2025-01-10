from typing import Optional
from datetime import datetime

from .stop import MBTAStop
from .utils import MBTAUtils


class JourneyStop:
    
    """A journey stop object to hold and manage arrival and departure details."""

    def __init__(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int,  status: str) -> None:

        self.stop: MBTAStop = stop
        
        self.arrival_time = MBTAUtils.parse_datetime(arrival_time)
        self.real_arrival_time = None
        self.arrival_delay = None

        self.departure_time = MBTAUtils.parse_datetime(departure_time)
        self.real_departure_time = None
        self.departure_delay = None
        
        self.status = status
        self.stop_sequence = stop_sequence

    def __repr__(self) -> str:
        return (f"JourneyStop(stop={self.stop.name})")
    
    def update_stop(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: str, status: str) -> None:
        """Update the stop details, including real arrival and departure times, uncertainties, and delays."""
        
        self.stop = stop
        self.stop_sequence = stop_sequence
        self.status = status
        
        if arrival_time is None and departure_time is None:
            self.arrival_time = None
            self.real_arrival_time = None
            self.arrival_delay = None
            self.departure_time = None
            self.real_departure_time = None
            self.departure_delay = None
        else:
            if arrival_time is not None:
                self.real_arrival_time = MBTAUtils.parse_datetime(arrival_time)
                if self.arrival_time is not None:
                    self.arrival_delay = MBTAUtils.calculate_time_difference(self.real_arrival_time, self.arrival_time)
            if departure_time is not None:
                self.real_departure_time = MBTAUtils.parse_datetime(departure_time)
                if self.departure_time is not None:
                    self.departure_delay = MBTAUtils.calculate_time_difference(self.real_departure_time, self.departure_time)
            
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
            return int(round(self.arrival_delay,0))
        if self.departure_delay is not None:
            return int(round(self.departure_delay,0))
        return None
        
    def get_time_to(self) -> float:
        """Return the most relevant time to for the stop."""
        now = datetime.now().astimezone()
        if self.real_arrival_time is not None:
            return MBTAUtils.time_to(self.real_arrival_time, now) 
        if self.real_departure_time is not None:
            return MBTAUtils.time_to(self.real_departure_time, now) 
        if self.arrival_time is not None:
            return MBTAUtils.time_to(self.arrival_time, now) 
        if self.departure_time is not None:
            return MBTAUtils.time_to(self.departure_time, now)      