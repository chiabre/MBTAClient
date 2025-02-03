import asyncio
from datetime import datetime
from typing import Optional
import logging

from ..stop import StopType

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler

from ..trip import Trip

class TripsHandler(MBTABaseHandler):
    """Handler for managing Trips."""

    DEFAULT_MAX_TRIPS =  5
    
    @classmethod
    async def create(
        cls, 
        departure_stop_name: str ,
        mbta_client: MBTAClient,
        arrival_stop_name: str,
        max_trips: Optional[int] = DEFAULT_MAX_TRIPS,
        sort_by: Optional[StopType] = StopType.ARRIVAL,
        logger: Optional[logging.Logger] = None)-> "TripsHandler":

        """Asynchronous factory method to initialize TripsHandler."""
        instance = await super()._create(
            departure_stop_name=departure_stop_name,
            mbta_client=mbta_client,
            arrival_stop_name=arrival_stop_name, 
            max_trips=max_trips,
            logger=logger)

        instance._sort_by = sort_by
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance

        return instance

    async def update(self) -> list[Trip]:
        self._logger.debug("Updating trips scheduling and info")

        try:
            # Initialize trips
            trips: dict[str, Trip] = {}

            # round to the hour to leverage caching in fetch and processing (based on header hash)
            min_time = f"{datetime.now().strftime("%H")}:00"

            params = {
                'filter[min_time]': min_time
            }
            
            # Update trip scheduling
            updated_trips = await super()._update_scheduling(trips=trips,params=params)

            # Filter out departed trips
            filtered_trips = super()._filter_and_sort_trips(
                trips=updated_trips,
                remove_departed=True,
                sort_by=self._sort_by)
            
            # Update stops for the trip
            task_stops = asyncio.create_task(super()._update_mbta_stops_for_trips(trips=filtered_trips.values()))
            # Update trip details
            tasks_trips_details = asyncio.create_task(super()._update_details(trips=filtered_trips))
    
            await task_stops                             
            detailed_trips = await tasks_trips_details

            # Filter out departed trips again
            filtered_detailed_trips = super()._filter_and_sort_trips(
                trips=detailed_trips,
                remove_departed=True,
                sort_by=self._sort_by)

            # Limit trips to the maximum allowed
            limited_trips = dict(list(filtered_detailed_trips.items())[:self._max_trips])

            # Return the sorted trips as a list
            return list(limited_trips.values())

        except Exception as e:
            self._logger.error(f"Failed to update trips: {e}")
            return []
