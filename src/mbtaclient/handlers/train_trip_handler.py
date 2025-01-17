
import logging

from datetime import datetime, timedelta
from typing import Optional, Tuple

from mbtaclient.client.mbta_client import MBTAClient
from mbtaclient.models.mbta_alert import MBTAAlert
from mbtaclient.models.mbta_prediction import MBTAPrediction
from mbtaclient.models.mbta_vehicle import MBTAVehicle
from mbtaclient.trip_stop import StopType
from .base_trip_handler import BaseTripHandler
from ..trip import Trip
from ..models.mbta_trip import MBTATrip, MBTATripError
from ..models.mbta_schedule import MBTASchedule

class TrainTripHandler(BaseTripHandler):
    """Handler for managing a specific trip."""

            
    @classmethod
    async def create(
        cls, 
        depart_from_name: str , 
        arrive_at_name: str,
        train_name: str, 
        mbta_client: MBTAClient, 
        logger: Optional[logging.Logger] = None)-> "TrainTripHandler":
        
        """Asynchronous factory method to initialize TrainTripHandler."""
        instance = await super()._create(depart_from_name=depart_from_name, arrive_at_name=arrive_at_name, mbta_client=mbta_client, logger=logger)
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        instance.train_name = train_name
        params = {
            'filter[revenue]': 'REVENUE',
            'filter[name]': train_name
            }
        try:
            # Fetch mbta trips and validate the response
            mbta_trips, _ = await instance._mbta_client.fetch_trips(params)
            if not mbta_trips or not isinstance(mbta_trips, list) or not isinstance(mbta_trips[0], MBTATrip):
                instance._logger.error(f"Error retrieving MBTA trip for train {train_name}: Invalid train name")
                raise MBTATripError("Invalid train name")

            # Create a new trip and assign the first trip
            trip = Trip()
            trip.mbta_trip  = mbta_trips[0]
            
            mbta_route, _ = await instance._mbta_client.fetch_route(trip.mbta_trip.route_id)
            if mbta_route is None:
                instance._logger.error(f"Error retrieving MBTA route for train {train_name}")
                raise MBTATripError("Invalid route")

            trip.mbta_route = mbta_route
     

            mbta_vehicles, _ = await instance.__fetch_vehicles(trip.mbta_trip.id)
            
            if mbta_vehicles:
                trip.mbta_vehicle = mbta_vehicles[0]
            
            instance.trips[trip.mbta_trip.id] = trip            
                        
            instance._logger.info("TrainTripHandler initialized successfully")
            
            return instance
        
        
        except Exception as e:
            instance._logger.error(f"Failed to initialize TrainTripHandler: {e}")
            raise     
            
    
    async def update(self) -> list[Trip]: 
        self._logger.debug(f"Updating TrainTripHandler")
        
        now = datetime.now().astimezone()
 
        try:

            
            for i in range(7):
                params = {}
                date_to_try = (now + timedelta(days=i)).strftime('%Y-%m-%d')
                params['filter[date]'] = date_to_try
                
                mbta_schedules, timestamp = await self.__fetch_schedules(params)
                if super()._should_reprocess('mbta_schedules',timestamp):
                    self._logger.debug("New schedules data detected. Processing...")
                    self._last_processed_timestamps['mbta_schedules'] = timestamp
                    super()._process_schedules(mbta_schedules)
                else:    
                    self._logger.debug("Schedules are up-to-date. Skipping processing.")
                
                trip_id, trip = next(iter(self.trips.items()))
                
                ####FIX the arrival time
                
                # Check for valid schedules, existing arrival time and not arrived yet
                if not trip.arrival_time or trip.arrival_time < (now + timedelta(minutes=5)):
                    trip.reset_stops()
                    continue

                mbta_vehicle, _ = await self.__fetch_vehicles(trip_id)
                if mbta_vehicle:
                    self.trips[trip_id].mbta_vehicle = mbta_vehicle[0]
                
                if i == 0: ## if today, check predictions
                    mbta_predictions,timestamp = await self.__fetch_predictions()
                    if super()._should_reprocess('mbta_predictions',timestamp):
                        self._logger.debug("New predictions data detected. Processing...")
                        self._last_processed_timestamps['mbta_predictions'] = timestamp
                        super()._process_predictions(mbta_predictions)
                    else:
                        self._logger.debug("Predictions are up-to-date. Skipping processing.")

                params = {}
                params['filter[datetime]'] = (now + timedelta(days=i)).isoformat()
                
                alerts, timestamp = await self.__fetch_alerts(params)
                if super()._should_reprocess('mbta_alerts',timestamp):
                    self._logger.debug("New alerts adata detected. Processing...")
                    self._last_processed_timestamps['mbta_alerts'] = timestamp
                    super()._process_alerts(alerts)  
                else:
                    self._logger.debug("Alerts are up-to-date. Skipping processing.")
                    
                if trip.arrival_time and trip.arrival_time > now:
                    break
                
                # Log an error if no valid schedules after the final attempt
                if i == 6:
                    self._logger.error(f"Error retrieving scheduling from {self.depart_from['name']} and {self.arrive_at['name']} on trip {self.train_name}")
                    raise MBTATripError("Invalid stops for the trip")
                        

            self._logger.info(f"TripHandler updated successfully")
            return list(self.trips.values())
        
        except Exception as e:
            self._logger.error(f"Failed to initialize TrainTripHandler: {e}")
            raise
    
    async def __fetch_schedules(self, params: dict) -> Tuple[list[MBTASchedule],float]:
        # Prepare filter parameters
        trip: Trip = next(iter(self.trips.values()))

        base_params = {
            'filter[trip]': trip.mbta_trip.id,
           # 'filter[route]': trip.mbta_route.id,
        }
        if params is not None:
            base_params.update(params)
        
        try:
            mbta_schedules, timestamp = await super()._fetch_schedules(base_params)
            return mbta_schedules, timestamp
        except Exception as e:
            self._logger.error(f"Error fetching MBTA schedules: {e}")
            raise

    async def __fetch_predictions(self) -> Tuple[list[MBTAPrediction],float]:       
        # Prepare filter parameters
        trip: Trip = next(iter(self.trips.values()))
        trip_id = trip.mbta_trip.id
        base_params = {
            'filter[trip]': trip_id,
        }
        try:
            mbta_predictions, timestamp = await super()._fetch_predictions(base_params)
            return mbta_predictions, timestamp
        except Exception as e:
            self._logger.error(f"Error fetching MBTA predictions: {e}")
            raise
             
    async def __fetch_alerts(self, params: Optional[dict] = None) -> Tuple[list[MBTAAlert],float]:       
        # Prepare filter parameters
        trip: Trip = next(iter(self.trips.values()))
        trip_id = trip.mbta_trip.id
        base_params = {
            'filter[trip]': trip_id,
            #'filter[route]': trip.mbta_route.id,
        }
        if params is not None:
            base_params.update(params)
            
        try:
            mbta_alerts, timestamp = await super()._fetch_alerts(params)
            return mbta_alerts, timestamp
        except Exception as e:
            self._logger.error(f"Error fetching MBTA alerts: {e}")
            raise
  
    async def __fetch_vehicles(self, trip_id: str) -> Tuple[list[MBTAVehicle],float]:       
        # Prepare filter parameters
        params = {
            'filter[trip]': trip_id,
        }

        try:
            mbta_vehicles, timestamp = await self._mbta_client.fetch_vehicles(params)
            return mbta_vehicles, timestamp
        except Exception as e:
            self._logger.error(f"Error fetching MBTA vehicles: {e}")
            raise
    