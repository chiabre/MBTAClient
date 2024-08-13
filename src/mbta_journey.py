from typing import Optional, List
from datetime import datetime
from mbta_stop import MBTAStop
from mbta_route import MBTARoute
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert
from mbta_prediction import MBTAPrediction
import logging

class MBTAJourney:
    """A class to manage a journey with multiple stops."""

    def __init__(self) -> None:
        
        self.route: Optional[MBTARoute] = None
        self.trip: Optional[MBTATrip] = None
        self.alerts: List[MBTAAlert] = []
        self.journey_stops: List[MBTAJourneyStop] = []
        

    def __repr__(self) -> str:
        stops_repr = ', '.join([repr(stop) for stop in self.journey_stops])
        return f"MBTAjourney(route={self.route}, trip={self.trip}, stops=[{stops_repr}])"
    
    def add_stop(self, stop: 'MBTAJourneyStop') -> None:
        """Add a stop to the journey."""
        self.journey_stops.append(stop) 
    
    def get_stop_ids(self) -> List[str]:
        """Return a list of stop IDs for all stops in the journey."""
        return [journey_stop.stop.id for journey_stop in self.journey_stops]
    
    def find_jounrey_stop_by_id(self, stop_id: str) -> Optional['MBTAJourneyStop']:
        """Return the MBTAjourneyStop with the given stop_id, or None if not found."""
        for journey_stop in self.journey_stops:
            if journey_stop.stop.id == stop_id:
                return journey_stop
        return None
    
    def update_journey_stop(self, stop_index: int, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None):
    
        if (stop_index == 0 and len(self.journey_stops ) == 0) or (stop_index == 1 and len(self.journey_stops ) == 1):
            journey_stop = MBTAJourneyStop(stop, arrival_time, departure_time, stop_sequence, arrival_uncertainty, departure_uncertainty)
            self.journey_stops.append(journey_stop)
        else:
            self.journey_stops[stop_index].update_stop(stop, arrival_time, departure_time, stop_sequence, arrival_uncertainty, departure_uncertainty)
            
class MBTAJourneyStop:
    """A journey stop object to hold and manage arrival and departure details."""

    def __init__(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None) -> None:
        now = datetime.now().astimezone()

        self.stop = stop
        self.arrival_time = self.__parse_datetime(arrival_time)
        self.real_arrival_time = None
        self.arrival_uncertainty = MBTAPrediction.get_uncertainty_description(arrival_uncertainty)
        self.arrival_delay = None
        self.time_to_arrival = self.__time_to(self.arrival_time, now)

        self.departure_time = self.__parse_datetime(departure_time)
        self.real_departure_time = None
        self.departure_uncertainty = MBTAPrediction.get_uncertainty_description(departure_uncertainty)
        self.departure_delay = None
        self.time_to_departure = self.__time_to(self.departure_time, now)

        self.stop_sequence = stop_sequence

    def __repr__(self) -> str:
        return (f"MBTAjourneyStop(stop={repr(self.stop)}")

    def update_stop(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None) -> None:
        """Update the stop details, including real arrival and departure times, uncertainties, and delays."""
        self.stop = stop
        self.stop_sequence = stop_sequence
        if arrival_time is not None:
            self.real_arrival_time = self.__parse_datetime(arrival_time)
            if self.arrival_time is not None:
                self.arrival_delay = self.__compute_delay(self.real_arrival_time, self.arrival_time)
                self.time_to_arrival = self.__time_to(self.real_arrival_time, datetime.now().astimezone())
        if departure_time is not None:
            self.real_departure_time = self.__parse_datetime(departure_time)
            if self.departure_time is not None:
                self.departure_delay = self.__compute_delay(self.real_departure_time, self.departure_time)
                self.time_to_departure = self.__time_to(self.real_departure_time, datetime.now().astimezone())
        if arrival_uncertainty is not None:
            self.arrival_uncertainty = arrival_uncertainty
        if departure_uncertainty is not None:
            self.departure_uncertainty = departure_uncertainty

    def get_time(self) -> Optional[datetime]:
        """Return the most relevant time for the stop."""
        if self.real_departure_time is not None:
            return self.real_departure_time
        if self.departure_time is not None:
            return self.departure_time
        if self.real_arrival_time is not None:
            return self.real_arrival_time
        if self.arrival_time is not None:
            return self.arrival_time
        return None
    
    def get_delay(self) -> Optional[float]:
        """Return the most relevant delay for the stop."""
        if self.departure_delay is None and self.arrival_delay is None:
            return None
        if self.departure_delay is not None:
            return self.departure_delay
        if self.arrival_delay is not None:
            return self.arrival_delay
        return None
        
    def get_time_to(self) -> Optional[float]:
        """Return the most relevant time to for the stop."""
        return self.time_to_arrival or self.time_to_departure
    
    def get_uncertainty(self) -> Optional[str]:
        """Return the most relevant time to for the stop."""
        return self.arrival_uncertainty or self.departure_uncertainty

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

