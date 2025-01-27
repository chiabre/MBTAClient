from typing import Optional
import logging

from ..trip_stop import StopType

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler

from ..trip import Trip

class TripsHandler(MBTABaseHandler):
    """Handler for managing Trips."""
    
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
            # Initialize trips
            trips: dict[str, Trip] = {}

            # Update trip scheduling
            updated_trips = await super()._update_scheduling(trips=trips)

            # Filter out departed trips
            filtered_trips = super()._filter_trips(trips=updated_trips, remove_departed=True)

            # Update trip details
            detailed_trips = await super()._update_details(trips=filtered_trips)

            # Filter out departed trips again
            filtered_detailed_trips = super()._filter_trips(trips=detailed_trips, remove_departed=True)

            # Limit trips to the maximum allowed
            limited_trips = dict(list(filtered_detailed_trips.items())[:self._max_trips])

            # Sort trips by departure time
            #sorted_trips = super()._sort_trips(limited_trips, StopType.DEPARTURE)

            # Return the sorted trips as a list
            return list(limited_trips.values())

        except Exception as e:
            self._logger.error(f"Failed to update trips: {e}")
            return []

        
