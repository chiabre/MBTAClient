from typing import Optional, Tuple
import logging
from datetime import datetime, timedelta

from mbtaclient.client.mbta_client import MBTAClient
from mbtaclient.trip_stop import StopType
from ..models.mbta_schedule import MBTASchedule
from .base_trip_handler import BaseTripHandler
from ..trip import Trip



class TripsHandler(BaseTripHandler):
    """Handler for managing Trips."""

    # def __init__(
    #     self, 
    #     max_trips: int,
    # ) -> None:            
    #     self.max_trips = max_trips

    def __repr__(self) -> str:
        return (
            f"TripHandler(depart_from_name={self.depart_from['name']}, "
            f"arrive_at_name={self.arrive_at['name']})"
        )
    @classmethod
    async def create(
        cls, 
        depart_from_name: str , 
        arrive_at_name: str,
        max_trips: int, 
        mbta_client: MBTAClient, 
        logger: Optional[logging.Logger] = None) -> "TripsHandler":
        
        """Asynchronous factory method to initialize TripsHandler."""
        instance = await super()._create(
            depart_from_name=depart_from_name, 
            arrive_at_name=arrive_at_name, 
            mbta_client=mbta_client, 
            logger=logger)
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        instance.max_trips = max_trips  # Set the max_journeys after initialization
        instance._logger.info("TripsHandler initialized successfully")
        return instance


    async def update(self) -> list[Trip]:
        self._logger.debug("Updating TripHandler")
        try:
            
            mbta_schedules, timestamp = await self.__fetch_schedules()
            if super()._should_reprocess('mbta_schedules',timestamp):
                self._logger.debug("New schedules data detected. Processing...")
                super()._process_schedules(mbta_schedules)
                self._last_processed_timestamps['mbta_schedules'] = timestamp
                mbta_schedules_up_to_date = False
                
            else:    
                mbta_schedules_up_to_date = True
                self._logger.debug("Schedules are up-to-date. Skipping processing.")
            
            mbta_predictions, timestamp = await super()._fetch_predictions()
            if self._should_reprocess('mbta_predictions',timestamp):
                self._logger.debug("New predictions data detected. Processing...")
                super()._process_schedules(mbta_predictions)
                self._last_processed_timestamps['mbta_predictions'] = timestamp
                mbta_predictions_up_to_date = False
            else:
                mbta_predictions_up_to_date = True
                self._logger.debug("Predictions are up-to-date. Skipping processing.")

            if mbta_schedules_up_to_date and mbta_predictions_up_to_date:
                self._logger.debug("Schedules and predictionsare are up-to-date. Skipping sorting and cleanin.")               
            else:
                self._logger.debug("New Schedules or predictionsare data detected. Sorting and updating...")
                self.__sort_and_clean()
            
            await self.__update_trips()
            
            await self.__update_routes()
            
            alerts, timestamp = await self._fetch_alerts()
            if super()._should_reprocess('mbta_alerts',timestamp):
                self._logger.debug("New alerts adata detected. Processing...")
                super()._process_alerts(alerts)
                self._last_processed_timestamps['mbta_alerts'] = timestamp
            else:
                self._logger.debug("Alerts are up-to-date. Skipping processing.")
                
            self._logger.info("TripHandler updated successfully")
            return list(self.trips.values())
        except Exception as e:
            self._logger.error(f"Failed to initialize TripHandler: {e}")
            raise
    
    
    async def __fetch_schedules(self) -> Tuple[list[MBTASchedule],float]:
        try:
            params = {
                'filter[stop]': ','.join(super()._get_stops_ids()),
            }
            schedules, timestamp = await super()._fetch_schedules(params)
            return schedules, timestamp
        except Exception:
            raise
        
  
    def __sort_and_clean(self):
        try:
            now = datetime.now().astimezone()

            processed_trips = {
                trip_id: trip
                for trip_id, trip in self.trips.items() # For each trip in trip
                if any(stop.stop_type == StopType.DEPARTURE for stop in trip.stops)  # Ensure departure stop exists
                and any(stop.stop_type == StopType.ARRIVAL for stop in trip.stops)   # Ensure arrival stop exists
                and any(  # Verify that the departure stop_sequnce < arrival stop_sequence = the trip is in the right direction
                    stop.stop_type == StopType.DEPARTURE 
                    and stop.stop_sequence < next(
                        (arrival.stop_sequence for arrival in trip.stops if arrival.stop_type == StopType.ARRIVAL), 
                        float('inf')  # Default to infinity if no arrival stop is found
                    )
                    for stop in trip.stops
                    if stop.stop_type == StopType.DEPARTURE
                )
                and any( # Verify that the departure time is within the last 5mins or in the future
                    stop.stop_type == StopType.DEPARTURE and stop.get_time() is not None 
                    and stop.get_time() >= now - timedelta(minutes=5)
                    for stop in trip.stops
                    if stop.stop_type == StopType.DEPARTURE
                )
            }

            # Sort by arrival time if available, otherwise fallback to departure time
            sorted_trips = dict(
                sorted(
                    processed_trips.items(),
                    key=lambda item: (
                        item[1].arrival_time if item[1]._arrival_stop else 
                        item[1].departure_time if item[1]._departure_stop else 
                        None
                    )
                )
            )

            self.trips = dict(list(sorted_trips.items())[:self.max_trips] if self.max_trips > 0 else sorted_trips)
        
        except Exception as e:
            self._logger.error(f"Error sorting and cleaning trips: {e}")
            raise   
        
    async def __update_trips(self) -> None:
        try:
            for trip_id, trip in self.trips.items():
                mbta_trip, _ = await self._mbta_client.fetch_trip(trip_id)
                trip.mbta_trip = mbta_trip
        except Exception as e:
            self._logger.error(f"Error updating trips: {e}")
            raise

    async def __update_routes(self)-> None:
        try:
            for trip in self.trips.values():
                if trip.mbta_trip and trip.mbta_trip.route_id:
                    mbta_route, _ = await self._mbta_client.fetch_route(trip.mbta_trip.route_id)
                    trip.mbta_route = mbta_route
        except Exception as e:
            self._logger.error(f"Error updating routes: {e}")
            raise
