import asyncio
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
        trips_name: str,
        logger: Optional[logging.Logger] = None)-> "TrainsHandler":

        """Asynchronous factory method to initialize TripsHandler."""
        instance = await super()._create(
            departure_stop_name=departure_stop_name,
            arrival_stop_name=arrival_stop_name,
            mbta_client=mbta_client,
            max_trips=1,
            logger=logger)
        
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance

        await instance.__update_mbta_trips_by_trip_name(trips_name)

        return instance

    async def __update_mbta_trips_by_trip_name(self, trips_name: str) -> None:
        self._logger.debug("Updating MBTA trips")
        try:
            mbta_trips, _ = await self.__fetch_trips_by_name(trips_name)
            if mbta_trips:
                for mbta_trip in mbta_trips:
                    if not MBTATripObjStore.get_by_id(mbta_trip.id):
                        MBTATripObjStore.store(mbta_trip)
                    self._mbta_trips_id = mbta_trip.id
            else:
                self._logger.error(f"Invalid MBTA trip name {trips_name}")
                raise MBTATripError(f"Invalid MBTA trip name {trips_name}")
  
        except Exception as e:
            self._logger.error(f"Error updating MBTA trips: {e}")
            raise

    async def __fetch_trips_by_name(self, train_name: str) -> Tuple[list[MBTATrip],float]:    

        params = {
            'filter[revenue]': 'REVENUE',
            'filter[name]': train_name
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
                    'filter[trip]': self._mbta_trips_id,
                    'filter[date]': date_to_try
                }

                updated_trips = await super()._update_scheduling(trips=trips,params=params)

                # Filter out departed trips
                filtered_trips = super()._filter_and_sort_trips(
                    trips=updated_trips, 
                    remove_departed=False)
                
                if len(filtered_trips) == self._max_trips:
                    break
                
                if len(filtered_trips) == 0:
                    if i == 6:
                        self._logger.error(f"No trips between the provided stops till {date_to_try}")
                        raise MBTATripError(f"No trips between the provided stops till {date_to_try}")
                    continue

            # Update stops for the trip
            task_stops = asyncio.create_task(super()._update_mbta_stops_for_trips(trips=filtered_trips.values()))
            # Update trip details
            tasks_trips_details = asyncio.create_task(super()._update_details(trips=filtered_trips))
    
            await task_stops                             
            detailed_trips = await tasks_trips_details

            return list(detailed_trips.values())

        except Exception as e:
            self._logger.error(f"Error updating trips scheduling and info: {e}")
            raise



                    
class MBTATripError(Exception):
    pass
