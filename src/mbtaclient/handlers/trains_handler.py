from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..models.mbta_trip import MBTATrip, MBTATripError
from ..trip_stop import StopType
from ..trip import Trip


class TrainsHandler(MBTABaseHandler):
    """Handler for managing Trips."""

    def __repr__(self) -> str:
        # Check if there are any trips
        if not self._trips:
            return "TrainsHandler(no trips available)"

        # Get the first trip to retrieve common departure and arrival stops
        first_trip = next(iter(self._trips.values()), None)

        # Extract departure and arrival stops from the first trip
        departure_stop = first_trip.get_stop_by_type(StopType.DEPARTURE) if first_trip else "Unknown"
        arrival_stop = first_trip.get_stop_by_type(StopType.ARRIVAL) if first_trip else "Unknown"

        # Collect all trip names
        trip_names = [trip.mbta_trip.name for trip in self._trips.values()]

        # Create the string representation with all necessary information
        return (f"TrainsHandler(departure from {departure_stop}, arrival to {arrival_stop}, trips: {', '.join(trip_names)})")
    
        
    @classmethod
    async def create(
        cls, 
        departure_stop_name: str ,
        mbta_client: MBTAClient, 
        arrival_stop_name: str,
        trips_names: str,
        logger: Optional[logging.Logger] = None)-> "TrainsHandler":
        
        """Asynchronous factory method to initialize TripsHandler."""
        instance = await super()._create(
            departure_stop_name=departure_stop_name, 
            arrival_stop_name=arrival_stop_name, 
            mbta_client=mbta_client,
            max_trips=len(trips_names),
            logger=logger)
        
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        
        await instance.__set_mbta_trips_by_trip_names(trips_names)

        return instance

    async def __set_mbta_trips_by_trip_names(self, trips_names: list[str]) -> None:
        self._logger.debug("Updating MBTA trips")
        try:
            mbta_trips, _ = await self.__fetch_trips_by_names(trips_names)
            if mbta_trips:
                for mbta_trip in mbta_trips:
                    new_trip = Trip()
                    new_trip.mbta_trip = mbta_trip
                    self._trips[mbta_trip.id] = new_trip    
            else:
                self._logger.error(f"Invalid MBTA trip name {trips_names}")
                raise MBTATripError(f"Invalid MBTA trip name {trips_names}")
            
        except Exception as e:
            self._logger.error(f"Error updating MBTA trips: {e}")
            raise

    async def __fetch_trips_by_names(self, train_names: list[str]) -> Tuple[list[MBTATrip],float]:    
        
        params = {
            'filter[revenue]': 'REVENUE',
            'filter[name]': ','.join(train_names)
            }
            
        mbta_trips, timestamp = await self._mbta_client.fetch_trips(params)
        return mbta_trips, timestamp
    
    
    async def update(self) -> list[Trip]:
        self._logger.debug("Updating trips scheduling and info")
        try:
           
            now = datetime.now().astimezone()
                    
            for i in range(7):
                date_to_try = (now + timedelta(days=i)).strftime('%Y-%m-%d')

                params = {
                    'filter[trip]': ','.join(self._trips.keys()),
                    'filter[date]': date_to_try
                }
            
                self._trips = await super()._update_scheduling(params)
        
                fileter_trips = super()._filter_trips(remove_departed=False)
                
                if len(fileter_trips) == 0:
                    if i == 6:
                        self._logger.error(f"Error retrieving scheduling for {self._trips.keys()}")
                        raise MBTATripError("No trip between the provided stops in the next 7 days")
                    continue
                
                self._trips = fileter_trips
                self._trips = super()._sort_trips(StopType.DEPARTURE)   
                                
                break
            
            for trip_id, trip in self._trips.items():
                
                await super()._set_mbta_trip(trip_id)
                await super()._update_trip_info(trip)                    
            
            return [value for value in self._trips.values()]
            
        except Exception as e:
            self._logger.error(f"Error updating trips scheduling and info: {e}")
            raise
        
    
    
