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
from mbta_utils import MBTAUtils


class BaseHandler:
    """Base class for handling MBTA data."""
    
    def __init__(self, session: aiohttp.ClientSession, api_key: str, depart_from_name: str , arrive_at_name: str) -> None:

        mbta_client = MBTAClient(session, api_key)
    
        self.mbta_client = mbta_client
        self.depart_from_name = depart_from_name
        self.arrive_at_name = arrive_at_name
        self.journeys: dict[str, Journey] = {} 
  
        # Caches 
        self._stops_cache: Optional[list[MBTAStop]] = None
        self._schedules_cache: Optional[dict] = None  # Will hold {'schedules': list[MBTASchedule], 'timestamp': datetime}
        self._trip_cache: dict[str, MBTATrip] = {}
        self._route_cache: dict[str, MBTARoute] = {}
        self._stop_name_cache: dict[str, list[MBTAStop]] = {}
    
    async def _fetch_stops(self, params: dict = None) -> list[MBTAStop]:
        """Retrieve and process stops with a non-expiring cache."""
        
        # Check if stops are already cached
        if self._stops_cache is not None:
            logging.info("Returning cached stops")
            return self._stops_cache

        # Cache is empty, so we fetch the stops from the API
        base_params = {'filter[location_type]': '0'}
        
        if params is not None:
            base_params.update(params)
        
        try:
            stops: list[MBTAStop] = await self.mbta_client.list_stops(base_params)
            # Update the cache
            self._stops_cache = stops
            return stops
        
        except Exception as e:
            logging.error(f"Error fetching stops: {e}")
            traceback.print_exc()
            return []

    async def _get_stops_ids(self)  -> list[str]:
        departure_stop_ids = await self.__get_stops_ids_by_name(self.depart_from_name)
        arrival_stop_ids = await self.__get_stops_ids_by_name(self.arrive_at_name)
        return departure_stop_ids + arrival_stop_ids                

    async def __get_stops_ids_by_name(self, stop_name: str ) -> list[str]:
        stops = await self.__get_stops_by_name(stop_name)
        stop_ids = [stop.id for stop in stops]
        return stop_ids
                      
    async def _get_stops(self)  -> list['MBTAStop']:
        departure_stops = await self.__get_stops_by_name(self.depart_from_name)
        arrival_stops = await self.__get_stops_by_name(self.arrive_at_name)
        return departure_stops + arrival_stops     
      
    async def __get_stops_by_name(self, stop_name: str) -> list[MBTAStop]:
        # Check if the stops for the stop_name are already cached
        if stop_name.lower() in self._stop_name_cache:
            logging.info(f"Returning cached stops for stop_name: {stop_name}")
            return self._stop_name_cache[stop_name.lower()]

        # Fetch all stops (assuming _fetch_stops is asynchronous)
        stops = await self._fetch_stops()

        # Filter stops by the given name
        matching_stops = [stop for stop in stops if stop.name.lower() == stop_name.lower()]

        # Cache the result
        self._stop_name_cache[stop_name.lower()] = matching_stops

        return matching_stops
    
    async def _get_stop_by_id(self, stop_id: str) -> MBTAStop:

        # Fetch all stops (assuming _fetch_stops is asynchronous)
        stops = await self._fetch_stops()

        # Find the first stop that matches the given stop_id
        for stop in stops:
            if stop.id == stop_id:
                return stop

        # Return None if no matching stop is found
        return None
                    
    async def _fetch_schedules(self, params: dict = None) -> list[MBTASchedule]:
        """Retrieve and process schedules based on the provided stop IDs and route ID.""" 
        
        # # Check if schedules are already cached and valid for today
        if self._schedules_cache and self._schedules_cache['date'] == date.today():
            logging.info("Returning cached schedules")
            return self._schedules_cache['schedules']
                                            
        base_params = {
            'filter[stop]': ','.join(await self._get_stops_ids()),
            'sort': 'departure_time'
        }
                   
        if params is not None:
            base_params.update(params)     
                  
        try:
            schedules: list[MBTASchedule] = await self.mbta_client.list_schedules(base_params)
            # Update the cache with the schedules and the current date
            self._schedules_cache = {
                'schedules': schedules,
                'date': date.today()  # Store only the current date
            }
            return schedules
        
        except Exception as e:
            logging.error(f"Error fetching schedule: {e}")
            traceback.print_exc()
            return []
            
    async def _process_schedules(self, schedules: list[MBTASchedule]):
              
        for schedule in schedules:               
            
            # if the schedule trip id not in the journeys
            if schedule.trip_id not in self.journeys:
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[schedule.trip_id] = journey
                
            stop: MBTAStop = await self._get_stop_by_id(schedule.stop_id) 
            departure_stop_ids = await self.__get_stops_ids_by_name(self.depart_from_name)    
            arrival_stop_id = await self.__get_stops_ids_by_name(self.arrive_at_name)          
            
            if schedule.stop_id in departure_stop_ids:
                self.journeys[schedule.trip_id].add_stop('departure',schedule,stop,'SCHEDULED')
            elif schedule.stop_id in arrival_stop_id:
                self.journeys[schedule.trip_id].add_stop('arrival',schedule, stop,'SCHEDULED')
    

    async def _fetch_predictions(self, params: str = None) -> list[MBTAPrediction]:
        """Retrieve and process predictions based on the provided stop IDs and route ID."""

        base_params = {
            'filter[stop]': ','.join(await self._get_stops_ids()),
            'filter[revenue]': 'REVENUE',
            'sort': 'departure_time'
        }
        
        if params is not None:
            base_params.update(params)           
        
        try:
            predictions: list[MBTAPrediction] = await self.mbta_client.list_predictions(base_params)
            return predictions
        
        except Exception as e:
            logging.error(f"Error fetching predictions: {e}")
            traceback.print_exc()
          
    async def _process_predictions (self, predictions: list[MBTAPrediction]):   
        
        for prediction in predictions:
        
            # if the trip of the prediciton is not in the journeys dict
            if prediction.trip_id not in self.journeys:             
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[prediction.trip_id] = journey
                
            stop: MBTAStop = await self._get_stop_by_id(prediction.stop_id)
            departure_stop_ids = await self.__get_stops_ids_by_name(self.depart_from_name)    
            arrival_stop_id = await self.__get_stops_ids_by_name(self.arrive_at_name)     
                        
            if prediction.schedule_relationship is None:
                prediction.schedule_relationship = 'DELAYED'   
            
            # if the prediction stop id is in the departure stop ids
            if prediction.stop_id in departure_stop_ids:
        
                self.journeys[prediction.trip_id].add_stop('departure',prediction,stop,prediction.schedule_relationship)
                        
            # if the prediction stop id is in the arrival stop ids 
            if prediction.stop_id in arrival_stop_id:

                self.journeys[prediction.trip_id].add_stop('arrival',prediction,stop,prediction.schedule_relationship)

    async def _fetch_alerts(self,params: str = None) -> list[MBTAAlert]:
        """Retrieve and associate alerts with the relevant journeys."""
        
        # Prepare filter parameters
        base_params = {
            'filter[stop]': ','.join(await self._get_stops_ids()),
            'filter[activity]': 'BOARD,EXIT,RIDE',
            'filter[datetime]': 'NOW'
        }

        if params is not None:
            base_params.update(params)           
        
        try:
            alerts: list[MBTAAlert] = await self.mbta_client.list_alerts(base_params)
            return alerts
        except Exception as e:
            logging.error(f"Error fetching alerts: {e}")
            traceback.print_exc()
            
    def _process_alerts(self, alerts: list[MBTAAlert]):
        
            for alert in alerts:
                
                # Iterate through each journey and associate relevant alerts
                for journey in self.journeys.values():
                    if alert in journey.alerts:
                        continue  # Skip if alert is already associated

                    # Check if the alert is relevant to the journey
                    if self._is_alert_relevant(alert, journey):
                        journey.alerts.append(alert)

    def _is_alert_relevant(self, alert: MBTAAlert, journey: Journey) -> bool:
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
            if not self._is_alert_activity_relevant(informed_entity, journey):
                continue
            return True  # Alert is relevant if all checks pass
        return False  # Alert is not relevant

    def _is_alert_activity_relevant(self, informed_entity: dict, journey: Journey) -> bool:
        """Check if the activities of the informed entity are relevant to the journey."""
        departure_stop_id = journey.get_stop_id('departure')
        arrival_stop_id = journey.get_stop_id('arrival')

        if informed_entity['stop'] == departure_stop_id and not any(activity in informed_entity.get('activities', []) for activity in ['BOARD', 'RIDE']):
            return False
        if informed_entity['stop'] == arrival_stop_id and not any(activity in informed_entity.get('activities', []) for activity in ['EXIT', 'RIDE']):
            return False
        return True
    
    async def _fetch_trip(self, trip_id: str, params: dict = None) -> MBTATrip:
        """Retrieve and process a trip with a non-expiring cache based on trip_id."""
        
        # Check if the trip is already cached
        if trip_id in self._trip_cache:
            logging.info(f"Returning cached trip for trip_id: {trip_id}")
            return self._trip_cache[trip_id]
        
        # Trip is not in the cache, so fetch it from the API
        try:
            trip: MBTATrip = await self.mbta_client.get_trip(trip_id, params)
            # Update the cache
            self._trip_cache[trip_id] = trip
            return trip
        
        except Exception as e:
            logging.error(f"Error fetching trip: {e}")
            traceback.print_exc()
            return None
        
    async def _fetch_route(self, route_id: str, params: dict = None) -> MBTARoute:
        """Retrieve and process a route with a non-expiring cache based on route_id."""
        
        # Check if the trip is already cached
        if route_id in self._route_cache:
            logging.info(f"Returning cached trip for route_id: {route_id}")
            return self._route_cache[route_id]
        
        # Trip is not in the cache, so fetch it from the API
        try:
            route: MBTARoute = await self.mbta_client.get_route(route_id, params)
            # Update the cache
            self._route_cache[route_id] = route
            return route
        
        except Exception as e:
            logging.error(f"Error fetching route: {e}")
            traceback.print_exc()
            return None