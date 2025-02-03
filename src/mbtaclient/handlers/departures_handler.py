import asyncio
import logging
from datetime import datetime
from typing import Optional

from .base_handler import MBTABaseHandler
from ..client.mbta_client import MBTAClient
from ..trip import Trip


class DeparturesHandler(MBTABaseHandler):
    """Handler for managing timetable."""

    DEFAULT_MAX_TRIPS =  5

    @classmethod
    async def create(
        cls,
        mbta_client: MBTAClient,
        departure_stop_name: str ,
        max_trips: Optional[int] = DEFAULT_MAX_TRIPS,
        logger: Optional[logging.Logger] = None)-> "DeparturesHandler":

        """Asynchronous factory method to initialize DeparturesHandler."""

        instance = await super()._create(
            mbta_client=mbta_client, 
            departure_stop_name=departure_stop_name, 
            max_trips=max_trips,
            logger=logger)

        instance._logger = logger or logging.getLogger(__name__)  # Logger instance

        return instance

    async def update(self) -> list[Trip]:
        self._logger.debug("Updating Trips")
        try:

            # Initialize trips
            trips: dict[str, Trip] = {}
            
            # roudn to the hour to leverage caching in fetch and processing (based on header hash)
            min_time = f"{datetime.now().strftime("%H")}:00"

            params = {
                'filter[min_time]': min_time
            }

            # Update trip scheduling
            updated_trips = await super()._update_scheduling(trips=trips, params=params)

            # Filter out departed trips'
            filtered_trips = super()._filter_and_sort_trips(
                trips=updated_trips, 
                remove_departed=True, 
                require_both_stops=False)

            # Update stops for the trip
            task_stops = asyncio.create_task(
                super()._update_mbta_stops_for_trips(trips=filtered_trips.values()))
            # Update trip details
            tasks_trips_details = asyncio.create_task(
                super()._update_details(trips=filtered_trips))

            await task_stops                 
            detailed_trips = await tasks_trips_details

            # Filter out departed trips again
            filtered_trips = super()._filter_and_sort_trips(
                trips=detailed_trips,
                remove_departed=True,
                require_both_stops=False)

            # Limit trips to the maximum allowed
            limited_trips = dict(list(filtered_trips.items())[:self._max_trips])

            return list(limited_trips.values())

        except Exception as e:
            self._logger.error(f"Error updating trips: {e}")
            raise
