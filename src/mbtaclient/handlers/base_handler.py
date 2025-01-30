import asyncio
import logging

from datetime import datetime, timedelta
from abc import abstractmethod
import traceback
from typing import Optional, Tuple, Union

from ..mbta_object_store import MBTARouteObjStore, MBTAStopObjStore

from ..client.mbta_client import MBTAClient

from ..trip import Trip
from ..stop import StopType

from ..models.mbta_stop import MBTAStop
from ..models.mbta_schedule import MBTASchedule
from ..models.mbta_prediction import MBTAPrediction, MBTAScheduleRelationship
from ..models.mbta_alert import MBTAAlert, MBTAAlertPassengerActivity, MBTAAlertsInformedEntity



class MBTABaseHandler:

    FILTER_TIME_BUFFER = timedelta(minutes=10)
    MAX_TRIPS = 50

    def __init__( self, mbta_client: MBTAClient, max_trips: Optional[int],logger: Optional[logging.Logger]):

        self._mbta_client = mbta_client
        self._mbta_stops_ids: dict[StopType, list[str]] = {
            StopType.DEPARTURE: [],
            StopType.ARRIVAL: []
        }
        self._max_trips = max_trips
        
        #self._trips: dict[str, Trip] = {}  # Dictionary to store Trip objects, keyed by trip ID
        
        self._last_processed_scheduling = {
             'data': None,
             'timestamp': None
        }
        
        self._logger = logger or logging.getLogger(__name__)  # Logger instance
    
    @classmethod
    async def _create(
        cls, 
        mbta_client: MBTAClient,
        departure_stop_name: Optional[str] = None ,
        arrival_stop_name: Optional[str] = None,
        max_trips: Optional[int] = 1,
        logger: Optional[logging.Logger] = None)-> "MBTABaseHandler":
        
        instance: MBTABaseHandler = cls(mbta_client=mbta_client, max_trips=max_trips,logger=logger)
        await instance.__update_mbta_stops(departure_stop_name=departure_stop_name,arrival_stop_name=arrival_stop_name)
        return instance

    @abstractmethod
    async def update(self) -> list[Trip]:
        """Update the trips info."""
        pass
    
    ### MBTA STOP
    async def __update_mbta_stops(self, departure_stop_name: str, arrival_stop_name: Optional[str]) -> None:
        
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
                MBTAStopObjStore.store(mbta_stop)
                self._mbta_stops_ids[StopType.DEPARTURE].append(mbta_stop.id)
            if arrival_stop_name and arrival_stop_name.lower() == mbta_stop.name.lower():
                MBTAStopObjStore.store(mbta_stop)
                self._mbta_stops_ids[StopType.ARRIVAL].append(mbta_stop.id)

        if departure_stop_name and len(self._mbta_stops_ids[StopType.DEPARTURE]) == 0:
            self._logger.error(f"Invalid departure stop name, no MBTA stop name matching {departure_stop_name} ")
            raise MBTAStopError(f"Invalid departure stop name, no MBTA stop name matching {departure_stop_name}")

        if arrival_stop_name and len(self._mbta_stops_ids[StopType.ARRIVAL]) == 0:
            self._logger.error(f"Invalid arrival stop name, no MBTA stop name matching {arrival_stop_name} ")
            raise MBTAStopError(f"Invalid arrival stop name, no MBTA stop name matching {arrival_stop_name}")
        
        
    ### SCHEDULING
    async def _update_scheduling(self, trips: dict[str, Trip], params: Optional[dict] = None) -> dict[str, Trip] :

        self._logger.debug("Updating scheduling")

        try:

            ####
            params_predictions = None
            if params and "filter[date]" in params.keys():
                params_predictions = params.copy()
                del params_predictions["filter[date]"]
            ####

            task_schedules = asyncio.create_task(self.__fetch_schedules(params))
            task_predictions = asyncio.create_task(self.__fetch_predictions(params_predictions))

            mbta_schedules, timestamp = await task_schedules

            if self._last_processed_scheduling['timestamp'] != timestamp:
                self._logger.debug("New MBTA schedules data detected. Processing...")
                trips = await self.__process_scheduling(schedulings=mbta_schedules,trips=trips)
                self._last_processed_scheduling['data'] = trips
                self._last_processed_scheduling['timestamp'] = timestamp
            else:    
                self._logger.debug("MBTA Schedules data are up-to-date. Skipping processing.")
                trips = self._last_processed_scheduling['data']

            mbta_predictions, _ = await task_predictions

            trips = await self.__process_scheduling(schedulings=mbta_predictions, trips=trips)

            return trips

        except Exception as e:
            self._logger.error(f"Error updating scheduling: {e}")
            raise

    async def __fetch_schedules(self, params: Optional[dict] = None) -> Tuple[list[MBTASchedule],float]:

        base_params = {
            'filter[stop]': ','.join(
                self._mbta_stops_ids.get(StopType.DEPARTURE, []) +
                self._mbta_stops_ids.get(StopType.ARRIVAL, [])
            ),
            'sort': 'departure_time',
        }

        if params is not None:
            base_params.update(params)

        mbta_schedules, timestamp = await self._mbta_client.fetch_schedules(base_params)
        return mbta_schedules, timestamp
    
    
    async def __fetch_predictions(self, params: Optional[dict] = None) -> Tuple[list[MBTAPrediction],float]:     
        base_params = {
            'filter[stop]': ','.join(
                self._mbta_stops_ids.get(StopType.DEPARTURE, []) +
                self._mbta_stops_ids.get(StopType.ARRIVAL, [])
            ),
            'filter[revenue]': 'REVENUE',
            'sort': 'departure_time'
        }
        
        if params is not None:
            base_params.update(params)     
                  
        mbta_predictions, timestamp = await self._mbta_client.fetch_predictions(base_params)
        return mbta_predictions, timestamp
    
        
    async def __process_scheduling(self, schedulings: Union[list[MBTASchedule],list[MBTAPrediction]], trips: dict[str, Trip] = None ) -> dict[str, Trip] :
        self._logger.debug("Processing scheduling")
        
        try:
            
            for scheduling in schedulings:
                
                # if schedulings is a prediciton and ScheduleRelationship == specific cases
                if isinstance(scheduling, MBTAPrediction) and scheduling.schedule_relationship in [MBTAScheduleRelationship.CANCELLED.value, MBTAScheduleRelationship.SKIPPED.value, MBTAScheduleRelationship.NO_DATA.value]:
                    # if the scheduling stop is already in the trips
                    if  scheduling.trip_id in trips:
                        # remove it
                        trips.pop(scheduling.trip_id)
                    # skip this scheduling
                    continue
                
                # If the trip of the prediction is not in the trips dict
                if scheduling.trip_id not in trips:
                    # Create the trip
                    trip = Trip()
                else:
                    # Or get the trip with same trop_id from the trips
                    trip = trips[scheduling.trip_id]
                    
                #Set the mbta_route for the trip, 
                if not trip.mbta_route and scheduling.route_id:
                    # if the route in the objStore
                    if MBTARouteObjStore.get_by_id(scheduling.route_id):
                        # set the route id for the trip
                        trip.mbta_route_id = scheduling.route_id
                    else:
                        # fetch the route
                        mbta_route, _ = await self._mbta_client.fetch_route(scheduling.route_id)
                        # set the route for the trip (it will set the route id and store the obj in the objstore)
                        trip.mbta_route = mbta_route
                
                # if route type 0 or 1 and MBTASchedule skipp
                #https://www.mbta.com/developers/v3-api/best-practices#predictions
                if trip.mbta_route.type in [0,1] and isinstance(scheduling, MBTASchedule):
                    #Unfortunately in some corner cases there may be more trips type for the same trip...cannot break
                    continue
                    
                # Check if the prediction stop_id is in the departure stops lists
                if scheduling.stop_id in self._mbta_stops_ids[StopType.DEPARTURE]:
                    #add/update the stop as departure
                    trip.add_stop(
                        stop_type=StopType.DEPARTURE, 
                        scheduling=scheduling, 
                        mbta_stop_id=scheduling.stop_id)
                #Check if the prediction stop_id is in the arrival stops lists
                elif scheduling.stop_id in self._mbta_stops_ids[StopType.ARRIVAL]:
                    #add/update the stop as arrival
                    trip.add_stop(
                        stop_type=StopType.ARRIVAL, 
                        scheduling=scheduling, 
                        mbta_stop_id=scheduling.stop_id)
                
                trips[scheduling.trip_id] = trip
                    
            return trips
        
        except Exception as e:
            self._logger.error(f"Error while processing scheduling: {e}")
            self._logger.error(traceback.format_exc())  # Log the stack trace
            raise  # Re-raise the exception

    def _get_mbta_stop_by_id(self, stop_id: str) -> Optional[MBTAStop]:
        if any(stop_id in stop_ids for stop_ids in self._mbta_stops_ids.values()):
            return MBTAStopObjStore.get_by_id(stop_id)
        return None
    
        
    ## SET TRIP DETAILS
    async def _update_details(self, trips: dict[str, Trip]) -> dict[str, Trip]:
        """Update trip details with MBTA trip, vehicle, and alert information."""
        self._logger.debug("Updating trips details")
        
        try:
            updated_trips: dict[str, Trip] = {}

            # Collect all trip IDs to fetch vehicles
            params = {'filter[trip]': ','.join(trips.keys())}
            mbta_stop_ids = self._mbta_stops_ids.get(StopType.DEPARTURE, []) + self._mbta_stops_ids.get(StopType.ARRIVAL, [])
            
            # Fetch vehicles and alerts concurrently
            task_vehicles = asyncio.create_task(self._mbta_client.fetch_vehicles(params))
            task_alerts = asyncio.create_task(self.__get_mbta_alerts(trips=trips, stops_ids=mbta_stop_ids))

            # Await results from both tasks
            mbta_vehicles, _ = await task_vehicles
            mbta_alerts, _ = await task_alerts

            for trip_id, trip in trips.items():
                # Assign the trip ID if not already set
                if not trip.mbta_trip_id:
                    trip.mbta_trip_id = trip_id

                # Fetch and assign the MBTA trip if not already set
                if not trip.mbta_trip:
                    mbta_trip, _ = await self._mbta_client.fetch_trip(id=trip_id)
                    trip.mbta_trip = mbta_trip

                # Match vehicle for the trip
                matching_vehicles = [vehicle for vehicle in mbta_vehicles if vehicle.trip_id == trip_id]

                # Assign the vehicle to the trip if exist
                trip.mbta_vehicle = matching_vehicles[0] if len(matching_vehicles) > 0 else None

                # Filter and sort relevant alerts
                processed_alerts = []
                for mbta_alert in mbta_alerts:
                    if mbta_alert not in processed_alerts and mbta_alert.severity > 1 and self.__is_alert_relevant(mbta_alert, trip):
                        processed_alerts.append(mbta_alert)
                        
                # Sort processed_alerts by severity (high to low)
                processed_alerts.sort(key=lambda mbta_alert: mbta_alert.severity, reverse=True)

                trip.mbta_alerts = processed_alerts

                # Add the updated trip to the results
                updated_trips[trip_id] = trip

            return updated_trips

        except Exception as e:
            self._logger.error(f"Error while updating trips details: {e}")
            raise


    async def __get_mbta_alerts(
        self,
        trips: Optional[dict[str, Trip]] = None, 
        stops_ids: Optional[list[str]] =  None)-> Tuple[list[MBTAAlert],str]:
        self._logger.debug("Updating MBTA alerts")
        try:

            trips_ids = list(trips.keys())

            params = {
                'filter[stop]': ','.join( stops_ids ),
                'filter[trip]': ','.join( trips_ids ),
            }

            mbta_alerts, timestamp = await self._mbta_client.fetch_alerts(params)

            return mbta_alerts, timestamp

        except Exception as e:
            self._logger.error(f"Error updating MBTA alerts: {e}")
            raise
        
    def __is_alert_relevant(self, mbta_alert: MBTAAlert, trip: Trip) -> bool:
        """
        Determines whether an MBTA alert is relevant to a specific trip.

        Args:
            mbta_alert (MBTAAlert): The alert object containing details such as informed entities and active period.
            trip (Trip): The trip object containing information about the route, stops, and timing.

        Returns:
            bool: True if the alert is relevant to the given trip, otherwise False.

        Relevance is determined based on the following criteria:
            - The alert matches the trip's route (route-level alert).
            - The alert's informed entity explicitly mentions the trip ID.
            - The alert's informed entity is tied to the departure or arrival stops with relevant activities (boarding or exiting).
            - The trip's departure or arrival time falls within the alert's active period.
        """

        def check_route_level_alert(informed_entity: MBTAAlertsInformedEntity):
            """
            Check if the informed entity is a route-level alert matching the trip's route and direction.

            Args:
                informed_entity (MBTAAlertsInformedEntity): The informed entity to check.

            Returns:
                bool: True if the entity matches the route-level alert criteria, otherwise False.
            """
            return (
                informed_entity.route_id == trip.mbta_route.id and
                not informed_entity.stop_id and
                not informed_entity.trip_id and
                (not informed_entity.direction_id or informed_entity.direction_id == trip.mbta_trip.direction_id)
            )

        trip_id = trip.mbta_trip.id if trip.mbta_trip else None
        departure_stop_id = trip.get_stop_id_by_stop_type(StopType.DEPARTURE)
        arrival_stop_id = trip.get_stop_id_by_stop_type(StopType.ARRIVAL)

        for informed_entity in mbta_alert.informed_entities:
            if (
                check_route_level_alert(informed_entity) or
                informed_entity.trip_id == trip_id or
                (
                    informed_entity.stop_id == departure_stop_id and 
                    MBTAAlertPassengerActivity.BOARD in informed_entity.activities
                ) or
                (
                    informed_entity.stop_id == arrival_stop_id and 
                    MBTAAlertPassengerActivity.EXIT in informed_entity.activities
                )
            ) and (
                    (
                        trip.departure_time and 
                        mbta_alert.active_period_start <= trip.departure_time and 
                        (mbta_alert.active_period_end is None or trip.departure_time <= mbta_alert.active_period_end)
                    ) or (
                        trip.arrival_time and 
                        mbta_alert.active_period_start <= trip.arrival_time and 
                        (mbta_alert.active_period_end is None or trip.arrival_time <= mbta_alert.active_period_end)
                    )
            ):
                return True

        return False

    ##UTILY METHODS FOR SUBCLASSES
    def _filter_and_sort_trips(
        self,
        trips: dict[str, Trip],
        remove_departed: Optional[bool] = True,
        require_both_stops: Optional[bool] = True,
        sort_by: Optional[StopType] = StopType.DEPARTURE) -> dict[str, Trip]:
       
        """Filter and sort trips based on conditions like direction, departure, and arrival times."""
        self._logger.debug("Filtering Trips")
        now = datetime.now().astimezone()
        filtered_trips: dict[str, Trip] = {}

        try:
   
            trips = self._sort_trips(trips, sort_by)
            
            for trip_id, trip in trips.items():
                departure_stop = trip.get_stop_by_type(StopType.DEPARTURE)
                arrival_stop = trip.get_stop_by_type(StopType.ARRIVAL)

                # Filter out trips where either departure or arrival stops are missing
                if require_both_stops: 
                    if not departure_stop or not arrival_stop:
                        continue

                    # Filter out trips where stops are not in the correct sequence
                    if departure_stop.stop_sequence > arrival_stop.stop_sequence:
                        continue

                # If removed_departed = true Filter out trips already departed (+10mins)
                if remove_departed and departure_stop.time < now - self.FILTER_TIME_BUFFER:
                    continue
                
                # Filter out trips already arrived (+10mins)
                if arrival_stop and arrival_stop.time < now - self.FILTER_TIME_BUFFER:
                    continue
                
                vehicle_current_stop_sequence = trip.vehicle_current_stop_sequence

                # If vehicle_current_stop_sequence exists, use it for validation
                if vehicle_current_stop_sequence:
                    # Check if the trip has departed and filter it out if remove_departed is true and trip has departed more than 1 min ago
                    if remove_departed and vehicle_current_stop_sequence > departure_stop.stop_sequence and departure_stop.time < now - timedelta(minutes=1):
                        continue

                    # Check if the trip has arrived Filter our if trip has arrived more than 1 min ago
                    if arrival_stop and vehicle_current_stop_sequence >= arrival_stop.stop_sequence and arrival_stop.time < now - timedelta(minutes=1):
                        continue

                # Add the valid trip to the processed trips
                filtered_trips[trip_id] = trip

            return dict(list(filtered_trips.items())[:self.MAX_TRIPS])

        except Exception as e:
            self._logger.error(f"Error filtering trips: {e}")
            raise

    def _sort_trips(
        self,
        trips: dict[str, Trip],
        sort_by: Optional[StopType]=StopType.DEPARTURE) -> dict[str, Trip]:

        self._logger.debug("Cleaning Trips")
        try:

            today = datetime.now()
            sorted_trips: dict[str, Trip] = {
                trip_id: trip
                for trip_id, trip in sorted(
                    trips.items(),
                    key=lambda item: (
                        item[1].get_stop_by_type(sort_by).time if item[1].get_stop_by_type(sort_by) is not None
                        else (today + timedelta(days=365)).astimezone()
                    )
                )
            }

            return sorted_trips

        except Exception as e:
            self._logger.error(f"Error sorting and cleaning trips: {e}")
            raise

class MBTAStopError(Exception):
    pass
