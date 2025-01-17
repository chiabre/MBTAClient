import logging


from typing import Optional, Tuple


from ..client.mbta_client import MBTAClient
from ..trip import Trip
from ..trip_stop import StopType
from ..models.mbta_stop import MBTAStop, MBTAStopError
from ..models.mbta_schedule import MBTASchedule
from ..models.mbta_prediction import MBTAPrediction
from ..models.mbta_alert import MBTAAlert

 
class BaseTripHandler:
    """Base class for handling trips."""

    def __init__(
        self, 
        depart_from_name: str, 
        arrive_at_name: str, 
        mbta_client: MBTAClient,
        logger: logging.Logger = None
    ) -> None:
        """
        Initialize the BaseTripHandler.

        Args:
            depart_from_name (str): Name of the departure location.
            arrive_at_name (str): Name of the arrival location.
            mbta_client (MBTAClient): Client for interacting with the MBTA API.
            logger (Optional[logging.Logger]): Logger instance. Defaults to a module-level logger.
        """
        self.depart_from = {
            'name': depart_from_name,
            'mbta_stops': [],  # List of MBTAStop objects for departure location
            'ids': [],         # List of IDs corresponding to departure stops
        }
        self.arrive_at = {
            'name': arrive_at_name,
            'mbta_stops': [],  # List of MBTAStop objects for arrival location
            'ids': [],         # List of IDs corresponding to arrival stops
        }
        self._last_processed_timestamps = {
            'mbta_stops': None,  # Timestamp for the last time stops were processed
            'mbta_schedules': None,   # Timestamp for the last time schedules were processed
            'mbta_predictions': None, # Timestamp for the last time predictions were processed
        }
        self._mbta_client = mbta_client  # MBTA API client instance
        self._logger = logger or logging.getLogger(__name__)  # Logger instance
        self.trips: dict[str, Trip] = {}  # Dictionary of Trip objects, keyed by trip ID

    def __repr__(self) -> str:
        return (
            f"BaseTripHandler(depart_from_name={self.depart_from['name']}, "
            f"arrive_at_name={self.arrive_at['name']})"
        )
    
    @classmethod
    async def _create(
        cls, 
        depart_from_name: str , 
        arrive_at_name: str, 
        mbta_client: MBTAClient, 
        logger: Optional[logging.Logger] = None)-> "BaseTripHandler":
        """Asynchronous factory method to initialize BaseTripHandler by and fetching/processing stops data"""
        instance = cls(depart_from_name, arrive_at_name,mbta_client,logger)
        try:
            stops, timestamp = await instance._fetch_stops()
            instance._process_stops(stops)
            instance._last_processed_timestamps['stops'] = timestamp
            instance._logger.info("BaseTripHandler initialized successfully")
            return instance
        except Exception as e:
            instance._logger.error(f"Failed to initialize BaseTripHandler: {e}")
            raise
    
    #fetching methods
    async def _fetch_stops(self, params: dict = None) -> Tuple[list[MBTAStop],float]:
        """Retrieve stops."""
        base_params = {'filter[location_type]': '0'}
        if params is not None:
            base_params.update(params)
        try:
            mbta_stops, timestamp = await self._mbta_client.fetch_stops(base_params)
            return mbta_stops, timestamp
        except Exception as e:
            self._logger.error(f"Error fetching MBTA stops: {e}")
            raise 

    async def _fetch_schedules(self, params: Optional[dict] = None) -> Tuple[list[MBTASchedule],float]:
        """Retrieve MBTA schedules"""
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'sort': 'departure_time'
        }
        if params is not None:
            base_params.update(params)
        try:
            mbta_schedules, timestamp = await self._mbta_client.fetch_schedules(base_params)
            return mbta_schedules, timestamp
        except Exception as e:
            self._logger.error(f"Error retrieving MBTA schedules: {e}")
            raise
        
    async def _fetch_predictions(self, params: str = None) -> Tuple[list[MBTAPrediction],float]:
        """Retrieve MBTA predictions based on the provided stop IDs"""
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'filter[revenue]': 'REVENUE',
            'sort': 'departure_time'
        }
        if params is not None:
            base_params.update(params)           
        try:
            mbta_predictions, timestamp = await self._mbta_client.fetch_predictions(base_params)
            return mbta_predictions, timestamp
        except Exception as e:
            self._logger.error(f"Error retrieving MBTA predictions: {e}")
 
    async def _fetch_alerts(self, params: str = None) -> Tuple[list[MBTAAlert],float]:
        """Retrieve MBTA alerts"""               
        # Prepare filter parameters
        base_params = {
            'filter[stop]': ','.join(self._get_stops_ids()),
            'filter[activity]': 'BOARD,EXIT,RIDE',
            'filter[datetime]': 'NOW'
        }

        if params is not None:
            base_params.update(params)           
        
        try:
            mbta_alerts, timestamp = await self._mbta_client.fetch_alerts(base_params)
            return mbta_alerts, timestamp
        except Exception as e:
            self._logger.error(f"Error retrieving MBTA alerts: {e}")
            raise
        
    #processing methods  
    def _process_stops(self, mbta_stops: list[MBTAStop]):
        depart_from_stops = []
        depart_from_ids = []
        arrive_at_stops = []
        arrive_at_ids = []

        for mbta_stop in mbta_stops:
            if mbta_stop.name.lower() == self.depart_from['name'].lower():
                depart_from_stops.append(mbta_stop)
                depart_from_ids.append(mbta_stop.id)

            if mbta_stop.name.lower() == self.arrive_at['name'].lower():
                arrive_at_stops.append(mbta_stop)
                arrive_at_ids.append(mbta_stop.id)

        if len(depart_from_stops) == 0:
            self._logger.error(f"Invalid MBTA stop name {self.depart_from['name']}")
            raise MBTAStopError(f"Invalid MBTA stop name {self.depart_from['name']}")

        if len(arrive_at_stops) == 0:
            self._logger.error(f"Invalid MBTA stop name {self.arrive_at['name']}")
            raise MBTAStopError(f"Invalid MBTA stop name {self.arrive_at['name']}")

        self.depart_from['mbta_stops'] = depart_from_stops
        self.depart_from['ids'] = depart_from_ids
        self.arrive_at['mbta_stops'] = arrive_at_stops
        self.arrive_at['ids'] = arrive_at_ids


    def _process_schedules(self, mbta_schedules: list[MBTASchedule]):
        for mbta_schedule in mbta_schedules:
            # If the schedule trip_id is not in the trips
            if mbta_schedule.trip_id not in self.trips:
                # Create the trip
                trip = Trip()
                # Add the trip to the trips dict using the trip_id as key
                self.trips[mbta_schedule.trip_id] = trip

            # Validate stop
            mbta_stop: Optional[MBTAStop] = self._get_stop_by_id(mbta_schedule.stop_id)
            if not mbta_stop:
                continue  # Skip to the next schedule

            # Check if the stop_id is in the departure or arrival stops lists
            if mbta_schedule.stop_id in self.depart_from['ids']:
                self.trips[mbta_schedule.trip_id].add_stop(
                    stop_type=StopType.DEPARTURE, 
                    scheduling_data=mbta_schedule, 
                    mbta_stop=mbta_stop)
            elif mbta_schedule.stop_id in self.arrive_at['ids']:
                self.trips[mbta_schedule.trip_id].add_stop(
                    stop_type=StopType.ARRIVAL,  
                    scheduling_data=mbta_schedule, 
                    mbta_stop=mbta_stop)
            else:
                self._logger.warning(f"Stop ID {mbta_schedule.stop_id} is not categorized as departure or arrival for schedule: {mbta_schedule.id}")    

    def _process_predictions(self, mbta_predictions: list[MBTAPrediction]):

        for mbta_prediction in mbta_predictions:
            # Validate prediction data
            if not mbta_prediction.trip_id or not mbta_prediction.stop_id:
                self._logger.error(f"Invalid prediction data: {mbta_prediction}")
                continue  # Skip to the next prediction

            # If the trip of the prediction is not in the trips dict
            if mbta_prediction.trip_id not in self.trips:
                # Create the journey
                trip = Trip()
                # Add the trip to the trips dict using the trip_id as key
                self.trips[mbta_prediction.trip_id] = trip

            # Validate stop
            mbta_stop: Optional[MBTAStop] = self._get_stop_by_id(mbta_prediction.stop_id)
            if not mbta_stop:
                self._logger.error(f"Invalid stop ID: {mbta_prediction.stop_id} for prediction: {mbta_prediction}")
                continue  # Skip to the next prediction

            # Check if the prediction stop_id is in the departure or arrival stops lists
            if mbta_prediction.stop_id in self.depart_from['ids']:
                self.trips[mbta_prediction.trip_id].add_stop(
                    stop_type=StopType.DEPARTURE, 
                    scheduling_data=mbta_prediction, 
                    mbta_stop=mbta_stop, 
                    status=mbta_prediction.status)
            elif mbta_prediction.stop_id in self.arrive_at['ids']:
                self.trips[mbta_prediction.trip_id].add_stop(
                    stop_type=StopType.ARRIVAL, 
                    scheduling_data=mbta_prediction, 
                    mbta_stop=mbta_stop, 
                    status=mbta_prediction.status)
            else:
                self._logger.warning(f"Stop ID {mbta_prediction.stop_id} is not categorized as departure or arrival for prediction: {mbta_prediction}")               
  
    def _process_alerts(self, mbta_alerts: list[MBTAAlert]):
        for mbta_alert in mbta_alerts:
            # Validate alert data
            if not mbta_alert.id or not mbta_alert.effect:
                self._logger.error(f"Invalid alert data: {mbta_alert}")
                continue  # Skip to the next alert

            # Iterate through each trip and associate relevant alerts
            for trip in self.trips.values():
                # Check if the alert is already associated by comparing IDs
                if any(existing_alert.id == mbta_alert.id for existing_alert in trip.mbta_alerts):
                    continue  # Skip if alert is already associated

                # Check if the alert is relevant to the trip
                try:
                    if self.__is_alert_relevant(mbta_alert, trip):
                        trip.mbta_alerts.append(mbta_alert)
                except Exception as e:
                    self._logger.error(f"Error processing MBTA alert {mbta_alert.id}: {e}")
                    continue  # Skip to the next trip if an error occurs
    
    def _get_stops_ids(self) -> list[str]:
        return self.depart_from['ids'] + self.arrive_at['ids']

    def _get_stop_by_id(self, stop_id: str) -> Optional[MBTAStop]:
        # Check if the stop is in the depart_from or arrive_at lists
        for stop in self.depart_from['mbta_stops'] + self.arrive_at['mbta_stops']:
            if stop.id == stop_id:
                return stop
        self._logger.error(f"Stop with ID {stop_id} not found.")
        return None

    def __is_alert_relevant(self, mbta_alert: MBTAAlert, trip: Trip) -> bool:
        """Check if an alert is relevant to a given trip."""
        try:
            for informed_entity in mbta_alert.informed_entities:
                
                # Check informed entity stop relevance
                #trip.stop_ids()
                stops_ids = []
                stops_ids.append(trip.stops[0].mbta_stop.id)
                stops_ids.append(trip.stops[1].mbta_stop.id)
                    
                if informed_entity['stop_id'] not in stops_ids:
                    continue           
                    
                # Check informed entity trip relevance
                if informed_entity.get('trip_id') and informed_entity['trip_id'] != trip.mbta_trip.id:
                    continue
                # Check informed entity route relevance
                # if informed_entity.get('route_id') and informed_entity['route_id'] != trip.mbta_route.id:
                #     continue
                # Check activities relevance based on departure or arrival
                if not self.__is_alert_activity_relevant(informed_entity):
                    continue
                # If all checks pass, the alert is relevant
                return True
            return False
        except KeyError as e:
            self._logger.error(f"Missing expected key in alert data: {e}")
            raise ValueError(f"Invalid alert data: missing {e} key.")
        except Exception as e:
            self._logger.error(f"Error occurred while checking alert relevance: {e}")
            raise RuntimeError("An error occurred while determining alert relevance.") from e

    def __is_alert_activity_relevant(self, informed_entity: dict) -> bool:
        """Check if the activities of the informed entity are relevant to the trip."""
        try:
            if informed_entity.get('stop') == self.depart_from['ids'] and not any(activity in informed_entity.get('activities', []) for activity in ['BOARD', 'RIDE']):
                return False
            if informed_entity.get('stop') == self.arrive_at['ids'] and not any(activity in informed_entity.get('activities', []) for activity in ['EXIT', 'RIDE']):
                return False
            return True
        except KeyError as e:
            self._logger.error(f"Missing expected key in activity check: {e}")
            raise ValueError(f"Invalid activity data: missing {e} key.")
        except Exception as e:
            self._logger.error(f"Error occurred while checking alert activity relevance: {e}")
            raise RuntimeError("An error occurred while determining activity relevance.") from e

    def _should_reprocess(self, data_type: str, new_timestamp: float) -> bool:
        """Determine if data should be reprocessed based on its timestamp."""
        last_timestamp = self._last_processed_timestamps.get(data_type)
        return last_timestamp is None or new_timestamp > last_timestamp