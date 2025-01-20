import asyncio
import logging

from datetime import datetime, timedelta
from itertools import chain
from abc import abstractmethod
from typing import Optional, Tuple, Union

from typing import Optional, Tuple, Union

from ..client.mbta_client import MBTAClient
from ..trip import Trip
from ..trip_stop import StopType
from ..models.mbta_stop import MBTAStop, MBTAStopError
from ..models.mbta_schedule import MBTASchedule
from ..models.mbta_prediction import MBTAPrediction
from ..models.mbta_alert import MBTAAlert
from ..models.mbta_route import MBTARoute


class MBTABaseHandler:
    
    def __init__( self, mbta_client: MBTAClient, max_trips: Optional[int],logger: Optional[logging.Logger]):
        
        self._mbta_client = mbta_client
        self._departure_mbta_stops: list[MBTAStop] = []        
        self._arrival_mbta_stops: list[MBTAStop] = []
        self._max_trips = max_trips
        
        self._trips: dict[str, Trip] = {}  # Dictionary to store Trip objects, keyed by trip ID
        
        self._last_processed_scheduling = {
             'data': None,
             'timestamp': None
        }
        
        self._logger = logger or logging.getLogger(__name__)  # Logger instance
        
        
    @property
    def _departure_mbta_stop_ids(self) -> list[Optional[str]]:
        departure_mbta_stop_ids = []
        for mbta_stop in self._departure_mbta_stops:
            departure_mbta_stop_ids.append(mbta_stop.id)
        return departure_mbta_stop_ids
            
    @property
    def _arrival_mbta_stop_ids(self) -> list[Optional[str]]:
        arrival_mbta_stop_ids = []
        for mbta_stop in self._arrival_mbta_stops:
            arrival_mbta_stop_ids.append(mbta_stop.id)
        return arrival_mbta_stop_ids
    
    
    @classmethod
    async def _create(
        cls, 
        mbta_client: MBTAClient,
        departure_stop_name: Optional[str] = None ,
        arrival_stop_name: Optional[str] = None,
        max_trips: Optional[int] = 1,
        logger: Optional[logging.Logger] = None)-> "MBTABaseHandler":
        
        instance: MBTABaseHandler = cls(mbta_client=mbta_client, max_trips=max_trips,logger=logger)
        await instance.__set_mbta_stops(departure_stop_name=departure_stop_name,arrival_stop_name=arrival_stop_name)
        return instance


    @abstractmethod
    def update(self) -> list[Trip]:
        """Update the self._trips info."""
        pass
    
    ### MBTA STOP
    async def __set_mbta_stops(self, departure_stop_name: str, arrival_stop_name: Optional[str]) -> None:
        
        self._logger.debug("Updating MBTA stops")
    
        try:                
            mbta_stops, _ = await self.__fetch_mbta_stops()
            self.__process_mbta_stops(mbta_stops, departure_stop_name,arrival_stop_name)
            
        except Exception as e:
            self._logger.error(f"Error updating MBTA stops: {e}")
            raise

    async def __fetch_mbta_stops(self, params: dict = None) -> Tuple[list[MBTAStop],float]:    
        base_params = {
            'filter[location_type]': '0'
            }
        
        if params is not None:
            base_params.update(params)
            
        mbta_stops, timestamp = await self._mbta_client.fetch_stops(base_params)
        return mbta_stops, timestamp
    

    def __process_mbta_stops(self, mbta_stops: list[MBTAStop], departure_stop_name: Optional[str], arrival_stop_name: Optional[str]) -> None:
        for mbta_stop in mbta_stops:
            if departure_stop_name and departure_stop_name.lower() == mbta_stop.name.lower() :
                self._departure_mbta_stops.append(mbta_stop)
            if arrival_stop_name and arrival_stop_name.lower() == mbta_stop.name.lower():
                self._arrival_mbta_stops.append(mbta_stop)

        if departure_stop_name and len(self._departure_mbta_stops) == 0:
            self._logger.error(f"Invalid departure stop name, no MBTA stop name matching {departure_stop_name} ")
            raise MBTAStopError(f"Invalid departure stop name, no MBTA stop name matching {departure_stop_name}")

        if arrival_stop_name and len( self._arrival_mbta_stops) == 0:
            self._logger.error(f"Invalid arrival stop name, no MBTA stop name matching {arrival_stop_name} ")
            raise MBTAStopError(f"Invalid arrival stop name, no MBTA stop name matching {arrival_stop_name}")
        
        
    ### SCHEDULING
    async def _update_scheduling(self, params: Optional[dict] = None) -> dict[str, Trip] :
        
        self._logger.debug("Updating scheduling")
        
        try:
            
            ####
            params_predictions = None
            if params:
                params_predictions = params.copy() 
                del params_predictions["filter[date]"]
            ####
            
            task_schedules = asyncio.create_task(self.__fetch_schedules(params))
            task_predictions = asyncio.create_task(self.__fetch_predictions(params_predictions))
       
            mbta_schedules, timestamp = await task_schedules
            
            if self._last_processed_scheduling['timestamp'] != timestamp:
                self._logger.debug("New MBTA schedules data detected. Processing...")
                scheduling_data = self.__process_scheduling(mbta_schedules)
                self._last_processed_scheduling['data'] = scheduling_data
                self._last_processed_scheduling['timestamp'] = timestamp
            else:    
                self._logger.debug("MBTA Schedules data are up-to-date. Skipping processing.")
                scheduling_data = self._last_processed_scheduling['data']
                
            mbta_predictions, _ = await task_predictions
            
            return self.__process_scheduling(mbta_predictions, scheduling_data)

        except Exception as e:
            self._logger.error(f"Error updating schedulifng: {e}")
            raise
    
    async def __fetch_schedules(self, params: Optional[dict] = None) -> Tuple[list[MBTASchedule],float]:

        base_params = {
            'filter[stop]': ','.join( self._departure_mbta_stop_ids + self._arrival_mbta_stop_ids ),
            'sort': 'departure_time',
        }
        
        if params is not None:
            base_params.update(params)
            
        mbta_schedules, timestamp = await self._mbta_client.fetch_schedules(base_params)
        return mbta_schedules, timestamp
    
    
    async def __fetch_predictions(self, params: Optional[dict] = None) -> Tuple[list[MBTAPrediction],float]:     
        base_params = {
            'filter[stop]': ','.join( self._departure_mbta_stop_ids + self._arrival_mbta_stop_ids ),
            'filter[revenue]': 'REVENUE',
            'sort': 'departure_time'
        }
        
        if params is not None:
            base_params.update(params)     
                  
        mbta_predictions, timestamp = await self._mbta_client.fetch_predictions(base_params)
        return mbta_predictions, timestamp
    
        
    def __process_scheduling(self, mbta_schedulings: Union[list[MBTASchedule],list[MBTAPrediction]], scheduling_data: Optional[dict[str, Trip]] = {} ) -> dict[str, Trip] :

        if not scheduling_data:
            scheduling_data = self._trips
        for mbta_scheduling in mbta_schedulings:
            # If the trip of the prediction is not in the trips dict
            if mbta_scheduling.trip_id not in scheduling_data:
                # Create the journey
                trip = Trip()
                # Add the trip to the trips dict using the trip_id as key
                scheduling_data[mbta_scheduling.trip_id] = trip

            # Validate stop
            mbta_stop: Optional[MBTAStop] = self._get_mbta_stop_by_id(mbta_scheduling.stop_id)
            if not mbta_stop:
                self._logger.error(f"Invalid stop ID: {mbta_scheduling.stop_id} for prediction: {mbta_scheduling}")
                continue  # Skip to the next prediction

            # Check if the prediction stop_id is in the departure or arrival stops lists
            if mbta_scheduling.stop_id in self._departure_mbta_stop_ids:
                scheduling_data[mbta_scheduling.trip_id].add_stop(
                    stop_type=StopType.DEPARTURE, 
                    scheduling_data=mbta_scheduling, 
                    mbta_stop=mbta_stop)
            elif mbta_scheduling.stop_id in self._arrival_mbta_stop_ids:
                scheduling_data[mbta_scheduling.trip_id].add_stop(
                    stop_type=StopType.ARRIVAL, 
                    scheduling_data=mbta_scheduling, 
                    mbta_stop=mbta_stop)
                
        return scheduling_data
    

    def _get_mbta_stop_by_id(self, id: str) -> Optional[MBTAStop]:
        for mbta_stop in chain(self._arrival_mbta_stops, self._departure_mbta_stops):
            if mbta_stop.id == id:
                return mbta_stop
        return None
    
    ## SET MBTA TRIP
    async def _set_mbta_trip(self, trip_id: str)-> None:
        self._logger.debug(f"Updating MBTA trip for trip {trip_id}")
        try:
            mbta_trip, _ = await self._mbta_client.fetch_trip(trip_id)
            self._trips[trip_id].mbta_trip = mbta_trip
            
        except Exception as e:
            self._logger.error(f"Error updating MBTA trip {trip_id}: {e}")
            raise
        
    ## SET TRIP DETAILS
    async def _update_trip_info(self, trip: Trip) -> None:
        self._logger.debug("Updating trip details")
        try:      
            task_route = asyncio.create_task(self.__set_mbta_route(trip))
            task_vehicles = asyncio.create_task(self.__set_mbta_vehicle(trip))
            task_alerts= asyncio.create_task(self.__set_mbta_alerts(trip))

            await task_route
            await task_vehicles
            await task_alerts
                
        except Exception as e:
            self._logger.error(f"Error updating trips details: {e}")
            raise          
        
    async def __set_mbta_vehicle(self, trip: Trip) -> None:
        self._logger.debug(f"Updating MBTA vehicle for trip {trip.mbta_trip.id}")  
        try: 
            if trip.mbta_trip:
                trip_id = trip.mbta_trip.id
                params = {
                    'filter[trip]': trip_id
                }
                    
                mbta_vehicles, _ = await self._mbta_client.fetch_vehicles(params)
                if mbta_vehicles:
                    self._trips[trip_id].mbta_vehicle = mbta_vehicles[0]         
        except Exception as e:
            self._logger.error(f"Error updating MBTA vehicle for trip {trip.mbta_trip.id}: {e}")
            raise  
    
    async def __set_mbta_route(self, trip: Trip)-> Optional[list[MBTARoute]]:
        self._logger.debug(f"Updating MBTA route for trip {trip.mbta_trip.id}")
        try:
            if trip.mbta_trip:
                route_id = trip.mbta_trip.route_id
                trip_id = trip.mbta_trip.id
                mbta_route, _ = await self._mbta_client.fetch_route(route_id)
                self._trips[trip_id].mbta_route = mbta_route
        except Exception as e:
            self._logger.error(f"Error updating  MBTA route for trip{trip.mbta_trip.id}: {e}")
            raise   
        
    async def __set_mbta_alerts(self, trip: Trip)-> None:
        self._logger.debug(f"Updating MBTA alerts for trip {trip.mbta_trip.id}")
        try:
            
            if trip.mbta_trip:
                trip_id = trip.mbta_trip.id
                datetime = trip.departure_time or trip.arrival_time
                stop_ids = trip.get_mbta_stop_ids()
                
                params = {
                    'filter[stop]': ','.join( stop_ids ),
                    'filter[datetime]': datetime,
                    'filter[trip]': trip_id
                }
                
                mbta_alerts, _ = await self.__fetch_alerts(params)
                self.__process_alerts(mbta_alerts)
                    
        except Exception as e:
            self._logger.error(f"Error updating  MBTA alerts for trip {trip.mbta_trip.id}: {e}")
            raise   
    
    async def __fetch_alerts(self, params: Optional[dict] = None) -> Tuple[list[MBTAAlert],float]:            
        base_params = {
            'filter[activity]': 'BOARD,EXIT,RIDE',
        }
        if params is not None:
            base_params.update(params)           
        mbta_alerts, timestamp = await self._mbta_client.fetch_alerts(base_params)
        return mbta_alerts, timestamp
    
    
    def __process_alerts(self, mbta_alerts: list[MBTAAlert]):
        
        for mbta_alert in mbta_alerts:

            # Iterate through each trip and associate relevant alerts
            for trip in self._trips.values():
                # Check if the alert is already associated by comparing IDs
                if any(existing_alert.id == mbta_alert.id for existing_alert in trip.mbta_alerts):
                    continue  # Skip if alert is already associated
                # Check if the alert is relevant to the trip
                if self.__is_alert_relevant(mbta_alert, trip):
                    trip.mbta_alerts.append(mbta_alert)         
    

    def __is_alert_relevant(self, mbta_alert: MBTAAlert, trip: Trip) -> bool:
        """Check if an alert is relevant to a given trip."""
        mbta_stop_ids = trip.get_mbta_stop_ids()  # Departure and arrival stop IDs
        mbta_route_id = trip.mbta_route.id if trip.mbta_route else None
        trip_id = trip.mbta_trip.id if trip.mbta_trip else None

        for entity in mbta_alert.informed_entities:
            # Check if the alert affects the trip or route
            # if (entity.get('route_id') == mbta_route_id and entity.get('stop_id') is None) or \
            if  (entity.get('trip_id') == trip_id) or \
            (entity.get('stop_id') in mbta_stop_ids):
                # Verify activities only if the alert affects a specific stop
                if entity.get('stop_id') in mbta_stop_ids:
                    if not self.__is_alert_activity_relevant(entity):
                        continue
                # If conditions are satisfied, the alert is relevant
                return True

        return False


    def __is_alert_activity_relevant(self, entity: dict) -> bool:
        """Check if the activities of the informed entity are relevant to the trip."""
        stop_id = entity.get('stop_id')
        activities = entity.get('activities', [])
        # Verify activities based on stop relevance
        if stop_id in self._departure_mbta_stop_ids and not any(activity in activities for activity in ['BOARD', 'RIDE']):
            return False
        if stop_id in self._arrival_mbta_stop_ids and not any(activity in activities for activity in ['EXIT', 'RIDE']):
            return False

        return True

    ##UTILY METHODS FOR SUBCLASSES
    def _filter_trips(self, remove_departed: bool = False) -> dict[str, Trip]:
        """Filter trips based on conditions like direction, departure, and arrival times."""
        self._logger.debug("Cleaning Trips")
        now = datetime.now().astimezone()
        processed_trips: dict[str, Trip] = {}
        try:
            for trip_id, trip in self._trips.items():
                departure_stop = trip.get_stop_by_type(StopType.DEPARTURE)
                arrival_stop = trip.get_stop_by_type(StopType.ARRIVAL)

                # Filter out trips where either departure or arrival stops are missing
                if not departure_stop or not arrival_stop:
                    continue
                
                #Filter out if stops are not in the right sequence
                if departure_stop.stop_sequence > arrival_stop.stop_sequence:
                    continue

                # Filter out trips where the arrival time is more than 5 minutes in the past
                if arrival_stop.get_time() < now - timedelta(minutes=5):
                    continue

                # If departed trips have to be filtered, filter out trips where the departure time is more than 5 minutes in the past
                if remove_departed and departure_stop.get_time() < now - timedelta(minutes=5):
                    continue

                # Add the valid trip to the processed trips
                processed_trips[trip_id] = trip

            return dict(list(processed_trips.items())[:self._max_trips])

        except Exception as e:
            self._logger.error(f"Error cleaning trips: {e}")
            raise   
        
    def _sort_trips(self, stop_type: StopType) -> dict[str, Trip]:
        self._logger.debug("Cleaning Trips")
        try:
            
            sorted_trips: dict[str, Trip] = {
                trip_id: trip
                for trip_id, trip in sorted(
                    self._trips.items(),
                    key=lambda item: item[1].get_stop_by_type(stop_type).get_time()
                )
            }

            return sorted_trips
        
        except Exception as e:
            self._logger.error(f"Error sorting and cleaning trips: {e}")
            raise   