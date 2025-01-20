from datetime import datetime, timedelta
from typing import Optional
import logging

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..trip_stop import StopType
from ..trip import Trip


class TimetableHandler(MBTABaseHandler):
    """Handler for managing timetable."""

    def __repr__(self) -> str:
        if self._departures:
            # Access the first trip safely and fetch the departure stop
            first_trip = next(iter(self._trips.values()), None)
            departure_stop = first_trip.get_stop_by_type(StopType.DEPARTURE) if first_trip else "Unknown"
            return f"TimetableHandler(departures from {departure_stop})"
        else:
            # Access the first trip safely and fetch the arrival stop
            first_trip = next(iter(self._trips.values()), None)
            arrival_stop = first_trip.get_stop_by_type(StopType.ARRIVAL) if first_trip else "Unknown"
            return f"TimetableHandler(arrivals to {arrival_stop})"
    
    @classmethod
    async def create(
        cls, 
        stop_name: str ,
        mbta_client: MBTAClient, 
        max_trips: Optional[int] = 25,
        departures: Optional[bool] = True,
        logger: Optional[logging.Logger] = None)-> "TimetableHandler":
        
        """Asynchronous factory method to initialize TimetableHandler."""
        if departures:
            departure_stop_name = stop_name
            arrival_stop_name = None
        else :
            departure_stop_name = None
            arrival_stop_name = stop_name
        instance = await super()._create(mbta_client=mbta_client, departure_stop_name=departure_stop_name, arrival_stop_name=arrival_stop_name,max_trips=max_trips,logger=logger)
        
        instance._departures  = departures
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        
        return instance

    async def update(self) -> list[Trip]:
        self._logger.debug("Updating Trips")
        try:
            
            await super()._update_scheduling()
            
            self._trips = await self.create_timetable()
            
            if self._departures:
                self._trips = super()._sort_trips(StopType.DEPARTURE)
            else:
                self._trips = super()._sort_trips(StopType.ARRIVAL)   
        
            
            return [value for value in self._trips.values()]
            
        except Exception as e:
            self._logger.error(f"Error updating trips: {e}")
            raise
        
    async def create_timetable(self) -> dict[str, Trip]:
        
        now = datetime.now().astimezone()
        filtered_trips: dict[str, Trip] = {}
        i = 0
        for trip_id, trip in self._trips.items():
            
            if self._departures:
                # Skip trips with departure_datetime in the past
                if not trip.departure_datetime or trip.departure_datetime < now - timedelta(minutes=5):
                    continue
            else:
                if not trip.arrival_datetime or trip.arrival_datetime < now - timedelta(minutes=5):
                    continue
            
            await super()._set_mbta_trip(trip_id)
            await super()._update_trip_info(trip)
            # Check if the list of trips for the route has reached the max limit
           
            filtered_trips[trip_id] = trip
            i +=1
            if i == self._max_trips:
                break
        
        return filtered_trips