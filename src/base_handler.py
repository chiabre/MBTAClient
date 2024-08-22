import logging
import traceback
import aiohttp

from typing import Optional
from datetime import date


from mbta_client import MBTAClient
from journey import Journey
from mbta_stop import MBTAStop
from mbta_route import MBTARoute
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert


class BaseHandler:
    """Base class for handling MBTA journeys."""
    
    def __init__(self, session: aiohttp.ClientSession, logger: logging.Logger, depart_from_name: str , arrive_at_name: str, api_key: str = None) -> None:
    
        self.depart_from = {
            'name' : depart_from_name,
            'stops' : None,
            'ids' : None
        }
        self.arrive_at = {
            'name' : arrive_at_name,
            'stops' : None,
            'ids' : None
        }
        self.mbta_client = MBTAClient(session,logger, api_key=api_key)

        self.journeys: dict[str, Journey] = {} 
  
        # Caches 
        self._stops_cache: Optional[list[MBTAStop]] = None
        self._schedules_cache: Optional[list[MBTASchedule]] = None  
        self._schedules_cache_date: Optional[date] = None
        self._trip_cache: dict[str, MBTATrip] = {}
        self._route_cache: dict[str, MBTARoute] = {}
        
        # Logger
        self.logger: logging.Logger = logger
 
    def __repr__(self) -> str:
        return (f"BaseHandler(depart_from_name={self.depart_from['name']}, arrive_at_name={self.arrive_at['name']})")
 
        
    async def _async_init(self):
        stops = await self.__fetch_stops()
        self.__process_stops(stops)
    
    async def __fetch_stops(self, params: dict = None) -> list[MBTAStop]:
        """Retrieve and process stops with a non-expiring cache."""
        self.logger.debug("Fetching MBTA stops")
        
        # Check if stops are already cached
        if self._stops_cache is not None:
            return self._stops_cache

        # Cache is empty, so we fetch the stops from the API
        base_params = {'filter[location_type]': '0'}
        
        if params is not None:
            base_params.update(params)
        
        try:
            stops: list[MBTAStop] = await self.mbta_client.list_stops(base_params)
            self.logger.debug("Updating cached stops")
            self._stops_cache = stops
            return stops
        
        except Exception as e:
            self.logger.error(f"Error fetching stops: {e}")
            traceback.print_exc()
            return []
        
    def  __process_stops(self, stops: list[MBTAStop]):
        depart_from_stops = []
        depart_from_ids = []
        arrive_at_stops = []
        arrive_at_ids = []
        for stop in stops:
            if stop.name.lower() == self.depart_from['name'].lower():
                depart_from_stops.append(stop)
                depart_from_ids.append(stop.id)
            if stop.name.lower() == self.arrive_at['name'].lower():
                arrive_at_stops.append(stop)
                arrive_at_ids.append(stop.id)
                
        if len(depart_from_stops) == 0:
            self.logger.error(f"Error fetching MBTA stop data for {self.depart_from['name']}")
            raise ValueError(f"Invalid stop name: {self.depart_from['name']}")
        
        if len(arrive_at_stops) == 0:
            self.logger.error(f"Error fetching MBTA stop data for {self.arrive_at['name']}")
            raise ValueError(f"Invalid stop name: {self.arrive_at['name']}")
        else:    
            self.depart_from['stops'] = depart_from_stops
            self.depart_from['ids'] = depart_from_ids
            self.arrive_at['stops'] = arrive_at_stops
            self.arrive_at['ids'] = arrive_at_ids

    def __get_stop_by_id(self, stop_id: str) -> Optional[MBTAStop]:
        for stop in (self.depart_from['stops'] + self.arrive_at['stops']):
            if stop.id == stop_id:
                return stop
        return None
    
    def _get_stops_ids(self) -> list[str]:
        return  self.depart_from['ids'] + self.arrive_at['ids']         
    
    def __get_stops_ids_by_stop_type(self, stop_type: str) -> Optional[list[str]]:
        if stop_type == 'departure':
            return self.depart_from['ids']
        elif stop_type == 'arrival':
            return self.arrive_at['ids']  
        return None           
    
    async def _fetch_schedules(self, params: Optional[dict] = None) -> list[MBTASchedule]:
        """Retrieve and process schedules for today."""
        self.logger.debug("Fetching MBTA schedules")
        
        # Check if the cache is outdated
        if self._schedules_cache_date is not None and self._schedules_cache_date == date.today():
            self.logger.debug("Returning cached schedules")
            return self._schedules_cache

        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'sort': 'departure_time'
        }
        if params is not None:
            base_params.update(params)

        try:
            schedules: list[MBTASchedule] = await self.mbta_client.list_schedules(base_params)
            # Update the cache with new data and timestamp
            self.logger.debug("Updating cached schedules")
            self._schedules_cache = schedules
            self._schedules_cache_date = date.today()
            return schedules
        except Exception as e:
            self.logger.error(f"Error fetching schedules: {e}")
            traceback.print_exc()
            return []
            
    async def _process_schedules(self, schedules: list[MBTASchedule]):
        self.logger.debug("Processing schedules")
              
        for schedule in schedules:               
            
            # if the schedule trip id not in the journeys
            if schedule.trip_id not in self.journeys:
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[schedule.trip_id] = journey
                
            stop: MBTAStop = self.__get_stop_by_id(schedule.stop_id)
            departure_stops_ids = self.__get_stops_ids_by_stop_type('departure')
            arrival_stops_ids = self.__get_stops_ids_by_stop_type('arrival')
            
            if schedule.stop_id in departure_stops_ids:
                self.journeys[schedule.trip_id].add_stop('departure',schedule,stop,'SCHEDULED')
            elif schedule.stop_id in arrival_stops_ids:
                self.journeys[schedule.trip_id].add_stop('arrival',schedule, stop,'SCHEDULED')
    

    async def _fetch_predictions(self, params: str = None) -> list[MBTAPrediction]:
        """Retrieve and process predictions based on the provided stop IDs and route ID."""
        self.logger.debug("Fetching MBTA predictions")
                
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'filter[revenue]': 'REVENUE',
            'sort': 'departure_time'
        }
        
        if params is not None:
            base_params.update(params)           
        
        try:
            predictions: list[MBTAPrediction] = await self.mbta_client.list_predictions(base_params)
            return predictions
        
        except Exception as e:
            self.logger.error(f"Error fetching predictions: {e}")
            traceback.print_exc()
          
    async def _process_predictions (self, predictions: list[MBTAPrediction]):   
        self.logger.debug("Processing predictions")
                
        for prediction in predictions:
        
            # if the trip of the prediciton is not in the journeys dict
            if prediction.trip_id not in self.journeys:             
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[prediction.trip_id] = journey
                
            stop: MBTAStop = self.__get_stop_by_id(prediction.stop_id)
            departure_stops_ids = self.__get_stops_ids_by_stop_type('departure')
            arrival_stops_ids = self.__get_stops_ids_by_stop_type('arrival')
                        
            if prediction.schedule_relationship is None:
                prediction.schedule_relationship = 'PREDICTED'   
            
            # if the prediction stop id is in the departure stop ids
            if prediction.stop_id in departure_stops_ids:
                self.journeys[prediction.trip_id].add_stop('departure',prediction,stop,prediction.schedule_relationship)
            # if the prediction stop id is in the arrival stop ids 
            if prediction.stop_id in arrival_stops_ids:
                self.journeys[prediction.trip_id].add_stop('arrival',prediction,stop,prediction.schedule_relationship)

    async def _fetch_alerts(self,params: str = None) -> list[MBTAAlert]:
        """Retrieve and associate alerts with the relevant journeys."""
        self.logger.debug("Fetching MBTA alerts")
                
        # Prepare filter parameters
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'filter[activity]': 'BOARD,EXIT,RIDE',
            'filter[datetime]': 'NOW'
        }

        if params is not None:
            base_params.update(params)           
        
        try:
            alerts: list[MBTAAlert] = await self.mbta_client.list_alerts(base_params)
            return alerts
        except Exception as e:
            self.logger.error(f"Error fetching alerts: {e}")
            traceback.print_exc()
            
    def _process_alerts(self, alerts: list[MBTAAlert]):
        self.logger.debug("Processing alerts")
        
        for alert in alerts:
            
            # Iterate through each journey and associate relevant alerts
            for journey in self.journeys.values():
                if alert in journey.alerts:
                    continue  # Skip if alert is already associated

                # Check if the alert is relevant to the journey
                if self.__is_alert_relevant(alert, journey):
                    journey.alerts.append(alert)

    def __is_alert_relevant(self, alert: MBTAAlert, journey: Journey) -> bool:
        """Check if an alert is relevant to a given journey."""
        for informed_entity in alert.informed_entities:
            # Check informed entity stop relevance
            if informed_entity.get('stop') and informed_entity['stop'] not in journey.get_stops_ids():
                continue
            # Check informed entity trip relevance
            if informed_entity.get('trip') and informed_entity['trip'] != journey.trip.id:
                continue
            # Check informed entity route relevance
            if informed_entity.get('route') and informed_entity['route'] != journey.route.id:
                continue
            # Check activities relevance based on departure or arrival
            if not self.__is_alert_activity_relevant(informed_entity, journey):
                continue
            return True  # Alert is relevant if all checks pass
        return False  # Alert is not relevant

    def __is_alert_activity_relevant(self, informed_entity: dict, journey: Journey) -> bool:
        """Check if the activities of the informed entity are relevant to the journey."""
        departure_stop_id = journey.get_stop_id('departure')
        arrival_stop_id = journey.get_stop_id('arrival')

        if informed_entity['stop'] == departure_stop_id and not any(activity in informed_entity.get('activities', []) for activity in ['BOARD', 'RIDE']):
            return False
        if informed_entity['stop'] == arrival_stop_id and not any(activity in informed_entity.get('activities', []) for activity in ['EXIT', 'RIDE']):
            return False
        return True
    
    async def _fetch_trip(self, trip_id: str, params: dict = None) -> Optional[MBTATrip]:
        """Retrieve and process a trip with a non-expiring cache based on trip_id."""
        self.logger.debug(f"Fetching MBTA trip: {trip_id} ")
        
        # Check if the trip is already cached
        if trip_id in self._trip_cache:
            self.logger.debug(f"Returning cached trip: {trip_id}")
            return self._trip_cache[trip_id]
        
        # Trip is not in the cache, so fetch it from the API
        try:
            trip: MBTATrip = await self.mbta_client.get_trip(trip_id, params)
            self.logger.debug(f"Updating cached trip: {trip_id}")
            self._trip_cache[trip_id] = trip
            return trip
        
        except Exception as e:
            self.logger.error(f"Error fetching trip: {e}")
            traceback.print_exc()
            return None
        
    async def _fetch_route(self, route_id: str, params: dict = None) -> Optional[MBTARoute]:
        """Retrieve and process a route with a non-expiring cache based on route_id."""
        self.logger.debug(f"Fetching MBTA route: {route_id} ")
        
        # Check if the trip is already cached
        if route_id in self._route_cache:
            return self._route_cache[route_id]
        
        # Trip is not in the cache, so fetch it from the API
        try:
            route: MBTARoute = await self.mbta_client.get_route(route_id, params)
            # Update the cache
            self.logger.debug(f"Updating cached route: {route_id}")
            self._route_cache[route_id] = route
            return route
        
        except Exception as e:
            self.logger.error(f"Error fetching route: {e}")
            traceback.print_exc()
            return None
        
    async def _fetch_trips(self, params: dict = None) -> Optional[MBTARoute]:
        self.logger.debug("Fetching MBTA trips")
        try:
            trips: list[MBTATrip] = await self.mbta_client.list_trips(params)
            return trips
        except Exception as e:
            self.logger.error(f"Error fetching route: {e}")
            traceback.print_exc()
            return None
        
