from typing import Optional
import logging

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..trip_stop import StopType
from ..trip import Trip


class TripsHandler(MBTABaseHandler):
    """Handler for managing Trips."""

    def __repr__(self) -> str:
        return (f"TripHandler)")
    
    @classmethod
    async def create(
        cls, 
        departure_stop_name: str ,
        mbta_client: MBTAClient, 
        arrival_stop_name: str,
        max_trips: Optional[int] = 5,
        logger: Optional[logging.Logger] = None)-> "TripsHandler":
        
        """Asynchronous factory method to initialize TripsHandler."""
        instance = await super()._create(
            departure_stop_name=departure_stop_name,
            mbta_client=mbta_client,
            arrival_stop_name=arrival_stop_name, 
            max_trips=max_trips,
            logger=logger)
        
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        
        return instance


    async def update(self) -> list[Trip]:
        self._logger.debug("Updating trips scheduling and info")
        try:
            
            self._trips = await super()._update_scheduling()
            
            self._trips = super()._filter_trips(remove_departed=True)
            
            for trip_id, trip in self._trips.items():
            
                await super()._set_mbta_trip(trip_id)
                await super()._update_trip_info(trip)
            
            return self._trips.values()
            
        except Exception as e:
            self._logger.error(f"Error updating trips scheduling and info: {e}")
            raise
        
