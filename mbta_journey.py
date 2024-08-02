import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

class MBTAjourneyStop:
    """A journey stop object to hold and manage arrival and departure details."""

    def __init__(self, stop_id: str, arrival_time: str, departure_time: str, stop_sequence: int) -> None:
        now = datetime.now().astimezone()
        
        self.stop_id = stop_id
        self.arrival_time = self.__parse_datetime(arrival_time)
        self.real_arrival_time = None
        self.arrival_uncertainty = None
        self.arrival_delay = None
        self.time_to_arrival = self.__time_to(self.arrival_time, now)
        
        self.departure_time = self.__parse_datetime(departure_time)
        self.real_departure_time = None
        self.departure_uncertainty = None
        self.departure_delay = None
        self.time_to_departure = self.__time_to(self.departure_time, now)
        
        self.stop_sequence = stop_sequence

    def __repr__(self) -> str:
        return (f"MBTAjourneyStop(stop_id={self.stop_id}, arrival_time={self.arrival_time}, real_arrival_time={self.real_arrival_time}, "
                f"arrival_uncertainty={self.arrival_uncertainty}, departure_time={self.departure_time}, "
                f"real_departure_time={self.real_departure_time}, departure_uncertainty={self.departure_uncertainty}, "
                f"stop_sequence={self.stop_sequence}, arrival_delay={self.arrival_delay}, "
                f"departure_delay={self.departure_delay}, time_to_departure={self.time_to_departure}, "
                f"time_to_arrival={self.time_to_arrival})")

    def update_stop(self, stop_id: str, arrival_time: Optional[str], arrival_uncertainty: Optional[str],
                      real_departure_time: Optional[str], departure_uncertainty: Optional[str]) -> None:
        """Internal method to update stop details."""
        self.stop_id = stop_id
        if arrival_time is not None:
            self.real_arrival_time = self.__parse_datetime(arrival_time)
            if self.arrival_time is not None:
                self.arrival_delay = self.__compute_delay(self.real_arrival_time, self.arrival_time)
                self.time_to_arrival = self.__time_to(self.real_arrival_time, datetime.now().astimezone())
        if real_departure_time is not None:
            self.real_departure_time = self.__parse_datetime(real_departure_time)
            if self.departure_time is not None:
                self.departure_delay = self.__compute_delay(self.real_departure_time, self.departure_time)
                self.time_to_departure = self.__time_to(self.real_departure_time, datetime.now().astimezone())
        if arrival_uncertainty is not None:
            self.arrival_uncertainty = arrival_uncertainty
        if departure_uncertainty is not None:
            self.departure_uncertainty = departure_uncertainty
            
    def get_time(self) -> datetime:
        """Add a stop to the journey."""
        if self.real_arrival_time is not None:
            return self.real_arrival_time
        if self.arrival_time is not None:
            return self.arrival_time
        if self.real_departure_time is not None:
            return self.departure_time
        if self.departure_time is not None:
            return self.departure_time
        return datetime.max

    @staticmethod
    def __time_to(time: Optional[datetime], now: datetime) -> Optional[float]:
        if time is None:
            return None
        return (time - now).total_seconds()

    @staticmethod
    def __compute_delay(real_time: Optional[datetime], time: Optional[datetime]) -> Optional[float]:
        if real_time is None or time is None:
            return None
        return (real_time - time).total_seconds()
        
    @staticmethod
    def __parse_datetime(time_str: Optional[str]) -> Optional[datetime]:
        """Parse a string in ISO 8601 format to a datetime object."""
        if time_str is None:
            return None
        try:
            return datetime.fromisoformat(time_str)
        except ValueError as e:
            logging.error(f"Error parsing datetime: {e}")
            return None

class MBTAjourney:
    """A class to manage a journey with multiple stops."""

    def __init__(self, direction_name: str, direction_destination: str, headsign: Optional[str]) -> None:
        self.direction_name = direction_name
        self.direction_destination = direction_destination
        self.headsign = headsign
        self.stops = {}

    def add_stop(self, stop_name: str, stop: MBTAjourneyStop) -> None:
        """Add a stop to the journey."""
        self.stops[stop_name] = stop
        
    def get_stop_by_name(self, stop_name: str) -> Optional[MBTAjourneyStop]:
        """Return the stop with the given stop_name, or None if not found."""
        return self.stops.get(stop_name, None)

    def get_stops_ids(self) -> List[str]:
        """Return all stop IDs in the journey as a list, preserving the order."""
        return [stop.stop_id for stop in self.stops.values()]
    
    def get_stops_list(self) -> List[MBTAjourneyStop]:
        """Return all stops in the journey as a list, preserving the order."""
        return list(self.stops.values())

    def get_stops_names(self) -> List[str]:
        """Return all stops name in the journey as a list, preserving the order."""
        return list(self.stops.keys())

    def has_stop(self, stop_name: str) -> bool:
        """Check if a stop with the given stop_name is present in the journey."""
        return stop_name in self.stops

    def count_stops(self) -> int:
        """Count the stops in the journey."""
        return len(self.stops)

    def __repr__(self) -> str:
        stops_repr = ', '.join([f"'{stop_name}': {repr(stop)}" for stop_name, stop in self.stops.items()])
        return (f"MBTAjourney(direction_name={self.direction_name}, "
                f"direction_destination={self.direction_destination}, headsign={self.headsign}, stops={{ {stops_repr} }})")
