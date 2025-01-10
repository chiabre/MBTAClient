import logging
import aiohttp

from typing import Optional

from .client import MBTAClient
from .journey import Journey
from .stop import MBTAStop
from .route import MBTARoute
from .schedule import MBTASchedule
from .prediction import MBTAPrediction
from .trip import MBTATrip
from .alert import MBTAAlert
from .utils import memoize_async


class BaseHandler:
    """Base class for handling MBTA journeys."""
    
    def __init__(self, depart_from_name: str , arrive_at_name: str, api_key: str = None, session: aiohttp.ClientSession = None, logger: logging.Logger = None) -> None:
    
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
        
        client_session = session or aiohttp.ClientSession()
        self.mbta_client = MBTAClient(client_session, logger, api_key)
        
        self.journeys: dict[str, Journey] = {} 

        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        
    def __repr__(self) -> str:
        return "BaseHandler(depart_from_name={}, arrive_at_name={})".format(self.depart_from['name'], self.arrive_at['name'])
 
    async def __aenter__(self):
        # Entering context, initialize and return the handler
        await self._async_init()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        # Exit context, clean up resources if necessary
        await self.mbta_client.close()
        
    async def _async_init(self):
        stops = await self.__fetch_stops()
        self.__process_stops(stops)
    
    @memoize_async()
    async def __fetch_stops(self, params: dict = None) -> list[MBTAStop]:
        """Retrieve stops."""
        self.logger.debug("Retrieving MBTA stops")
        base_params = {'filter[location_type]': '0'}
        if params is not None:
            base_params.update(params)
        try:
            stops: list[MBTAStop] = await self.mbta_client.list_stops(base_params)
            return stops
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA stops: {}".format(e))
            return []
        except Exception as e:
            self.logger.error("Error retrieving MBTA stops: {}".format(e))
            return []
        
    def __process_stops(self, stops: list[MBTAStop]):
        self.logger.debug("Processing MBTA stops")
        depart_from_stops = []
        depart_from_ids = []
        arrive_at_stops = []
        arrive_at_ids = []

        for stop in stops:
            if not isinstance(stop, MBTAStop):  # Validate data type
                self.logger.warning("Unexpected data type for stop: {}".format(type(stop)))
                continue  # Skip invalid data

            if stop.name.lower() == self.depart_from['name'].lower():
                depart_from_stops.append(stop)
                depart_from_ids.append(stop.id)

            if stop.name.lower() == self.arrive_at['name'].lower():
                arrive_at_stops.append(stop)
                arrive_at_ids.append(stop.id)

        if len(depart_from_stops) == 0:
            self.logger.error("Error processing MBTA stop data for {}".format(self.depart_from['name']))
            raise MBTAStopError("Invalid stop name: {}".format(self.depart_from['name']))

        if len(arrive_at_stops) == 0:
            self.logger.error("Error processing MBTA stop data for {}".format(self.arrive_at['name']))
            raise MBTAStopError("Invalid stop name: {}".format(self.arrive_at['name']))

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
        return self.depart_from['ids'] + self.arrive_at['ids']         
    
    def __get_stops_ids_by_stop_type(self, stop_type: str) -> Optional[list[str]]:
        if stop_type == 'departure':
            return self.depart_from['ids']
        elif stop_type == 'arrival':
            return self.arrive_at['ids']  
        return None
    
    @memoize_async(expire_at_end_of_day=True)
    async def _fetch_schedules(self, params: Optional[dict] = None) -> list[MBTASchedule]:
        """Retrieve MBTA schedules"""
        self.logger.debug("Retrieving MBTA schedules")
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'sort': 'departure_time'
        }
        if params is not None:
            base_params.update(params)
        try:
            schedules: list[MBTASchedule] = await self.mbta_client.list_schedules(params)
            return schedules
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA schedules: {}".format(e))
            return []
        except Exception as e:
            self.logger.error("Error retrieving MBTA schedules: {}".format(e))
            return []
            
    async def _process_schedules(self, schedules: list[MBTASchedule]):
        self.logger.debug("Processing MBTA schedules")

        for schedule in schedules:
            # Validate schedule data
            if not schedule.trip_id or not schedule.stop_id:
                self.logger.error("Invalid schedule data: {}".format(schedule))
                continue  # Skip to the next schedule

            # If the schedule trip_id is not in the journeys
            if schedule.trip_id not in self.journeys:
                # Create the journey
                journey = Journey()
                # Add the journey to the journeys dict using the trip_id as key
                self.journeys[schedule.trip_id] = journey

            # Validate stop
            stop = self.__get_stop_by_id(schedule.stop_id)
            if not stop:
                self.logger.debug("Stop {} of schedule {} doesn't belong to the journey stop ids".format(schedule.stop_id, schedule.id))
                continue  # Skip to the next schedule

            departure_stops_ids = self.__get_stops_ids_by_stop_type('departure')
            arrival_stops_ids = self.__get_stops_ids_by_stop_type('arrival')

            # Check if the stop_id is in the departure or arrival stops lists
            if schedule.stop_id in departure_stops_ids:
                self.journeys[schedule.trip_id].add_stop('departure', schedule, stop, 'SCHEDULED')
            elif schedule.stop_id in arrival_stops_ids:
                self.journeys[schedule.trip_id].add_stop('arrival', schedule, stop, 'SCHEDULED')
            else:
                self.logger.warning("Stop ID {} is not categorized as departure or arrival for schedule: {}".format(schedule.stop_id, schedule))

    async def _fetch_predictions(self, params: str = None) -> list[MBTAPrediction]:
        """Retrieve MBTA predictions based on the provided stop IDs"""
        self.logger.debug("Retrieving MBTA predictions")
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
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA predictions: {}".format(e))
            return []
        except Exception as e:
            self.logger.error("Error retrieving MBTA predictions: {}".format(e))

    async def _process_predictions(self, predictions: list[MBTAPrediction]):
        self.logger.debug("Processing MBTA predictions")

        for prediction in predictions:
            # Validate prediction data
            if not prediction.trip_id or not prediction.stop_id:
                self.logger.error("Invalid prediction data: {}".format(prediction))
                continue  # Skip to the next prediction

            # If the trip of the prediction is not in the journeys dict
            if prediction.trip_id not in self.journeys:
                # Create the journey
                journey = Journey()
                # Add the journey to the journeys dict using the trip_id as key
                self.journeys[prediction.trip_id] = journey

            # Validate stop
            stop = self.__get_stop_by_id(prediction.stop_id)
            if not stop:
                self.logger.error("Invalid stop ID: {} for prediction: {}".format(prediction.stop_id, prediction))
                continue  # Skip to the next prediction

            departure_stops_ids = self.__get_stops_ids_by_stop_type('departure')
            arrival_stops_ids = self.__get_stops_ids_by_stop_type('arrival')

            # Default schedule relationship to 'PREDICTED' if not set
            if prediction.schedule_relationship is None:
                prediction.schedule_relationship = 'PREDICTED'

            # Check if the prediction stop_id is in the departure or arrival stops lists
            if prediction.stop_id in departure_stops_ids:
                self.journeys[prediction.trip_id].add_stop('departure', prediction, stop, prediction.schedule_relationship)
            elif prediction.stop_id in arrival_stops_ids:
                self.journeys[prediction.trip_id].add_stop('arrival', prediction, stop, prediction.schedule_relationship)
            else:
                self.logger.warning("Stop ID {} is not categorized as departure or arrival for prediction: {}".format(prediction.stop_id, prediction))               

    async def _fetch_alerts(self, params: str = None) -> list[MBTAAlert]:
        """Retrieve MBTA alerts"""
        self.logger.debug("Retrieving MBTA alerts")
                
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
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA alerts: {}".format(e))
            return []
        except Exception as e:
            self.logger.error("Error retrieving MBTA alerts: {}".format(e))
            return []
            
    def _process_alerts(self, alerts: list[MBTAAlert]):
        self.logger.debug("Processing MBTA alerts")
        
        for alert in alerts:
            # Validate alert data
            if not alert.id or not alert.effect:
                self.logger.error("Invalid alert data: {}".format(alert))
                continue  # Skip to the next alert

            # Iterate through each journey and associate relevant alerts
            for journey in self.journeys.values():
                # Check if the alert is already associated by comparing IDs
                if any(existing_alert.id == alert.id for existing_alert in journey.alerts):
                    continue  # Skip if alert is already associated

                # Check if the alert is relevant to the journey
                try:
                    if self.__is_alert_relevant(alert, journey):
                        journey.alerts.append(alert)
                except Exception as e:
                    self.logger.error("Error processing MBTA alert {}: {}".format(alert.id, e))
                    continue  # Skip to the next journey if an error occurs

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
    
    @memoize_async()
    async def _fetch_trip(self, trip_id: str, params: dict = None) -> Optional[MBTATrip]:
        """Retrieve MBTA trip based on trip_id."""
        self.logger.debug("Retrieving MBTA trip: {}".format(trip_id))
        try:
            trip: MBTATrip = await self.mbta_client.get_trip(trip_id, params)
            return trip
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while fetching trip {}: {}".format(trip_id, e))
            return None
        except Exception as e:
            self.logger.error("Error fetching trip {}: {}".format(trip_id, e))
            return None
    
    @memoize_async()
    async def _fetch_route(self, route_id: str, params: dict = None) -> Optional[MBTARoute]:
        """Retrieve MBTA route based on route_id."""
        self.logger.debug("Retrieving MBTA route: {}".format(route_id))
        try:
            route: MBTARoute = await self.mbta_client.get_route(route_id, params)
            return route
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA route {}: {}".format(route_id, e))
            return None
        except Exception as e:
            self.logger.error("Error retrieving MBTA route {}: {}".format(route_id, e))
            return None
    
    @memoize_async()
    async def _fetch_trips(self, params: dict = None) -> Optional[MBTARoute]:
        """Retrieve MBTA trips"""
        self.logger.debug("Retrieving MBTA trips")
        try:
            trips: list[MBTATrip] = await self.mbta_client.list_trips(params)
            return trips
        except aiohttp.ClientError as e:
            self.logger.error("HTTP error occurred while retrieving MBTA trips: {}".format(e))
            return None
        except Exception as e:
            self.logger.error("Error retrieving MBTA trips: {}".format(e))
            return None

class MBTAStopError(Exception):
    pass

class MBTATripError(Exception):
    pass