from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

from ..mbta_object_store import MBTATripObjStore

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..models.mbta_trip import MBTATrip
from ..trip import Trip


class TrainsHandler(MBTABaseHandler):
    """Handler for managing Trips."""

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

        instance._mbta_trips_ids = []
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance

        await instance.__update_mbta_trips_by_trip_names(trips_names)

        return instance

    async def __update_mbta_trips_by_trip_names(self, trips_names: list[str]) -> None:
        self._logger.debug("Updating MBTA trips")
        try:
            mbta_trips, _ = await self.__fetch_trips_by_names(trips_names)
            if mbta_trips:
                for mbta_trip in mbta_trips:
                    if not MBTATripObjStore.get_by_id(mbta_trip.id):
                        MBTATripObjStore.store(mbta_trip)
                    self._mbta_trips_ids.append(mbta_trip.id)
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

            # Initialize trips
            trips: dict[str, Trip] = {}

            for i in range(7):
                date_to_try = (now + timedelta(days=i)).strftime('%Y-%m-%d')

                params = {
                    'filter[trip]': ','.join(self._mbta_trips_ids),
                    'filter[date]': date_to_try
                }

                updated_trips = await super()._update_scheduling(trips=trips,params=params)

                # Filter out departed trips
                filtered_trips = super()._filter_and_sort_trips(
                    trips=updated_trips, 
                    remove_departed=False)

                if len(filtered_trips) == 0:
                    if i == 6:
                        self._logger.error(f"Error retrieving scheduling for {trips.keys()}")
                        raise MBTATripError("No trip between the provided stops in the next 7 days")
                    continue

                break

            # Update trip details
            detailed_trips = await super()._update_details(trips=filtered_trips)

            return list(detailed_trips.values())

        except Exception as e:
            self._logger.error(f"Error updating trips scheduling and info: {e}")
            raise

class MBTATripError(Exception):
    pass
