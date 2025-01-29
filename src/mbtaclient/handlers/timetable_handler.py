from datetime import datetime
from typing import Optional
import logging

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..trip import Trip


class TimetableHandler(MBTABaseHandler):
    """Handler for managing timetable."""

    @classmethod
    async def create(
        cls,
        stop_name: str ,
        mbta_client: MBTAClient, 
        max_trips: Optional[int] = 5,
        logger: Optional[logging.Logger] = None)-> "TimetableHandler":

        """Asynchronous factory method to initialize TimetableHandler."""
        departure_stop_name = stop_name
        arrival_stop_name = None

        instance = await super()._create(
            mbta_client=mbta_client, 
            departure_stop_name=departure_stop_name, 
            arrival_stop_name=arrival_stop_name,
            max_trips=max_trips,
            logger=logger)

        instance._logger = logger or logging.getLogger(__name__)  # Logger instance

        return instance

    async def update(self) -> list[Trip]:
        self._logger.debug("Updating Trips")
        try:

            # Initialize trips
            trips: dict[str, Trip] = {}

            params = {
                'filter[min_time]': datetime.now().strftime("%H:%M")
            }
            
            # Update trip scheduling
            updated_trips = await super()._update_scheduling(trips=trips, params=params)

            # Filter out departed trips'
            filtered_trips = super()._filter_and_sort_trips(
                trips=updated_trips, 
                remove_departed=True, 
                require_both_stops=False)

            # Update trip details
            detailed_trips = await super()._update_details(trips=filtered_trips)

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
