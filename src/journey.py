import logging
import traceback
import aiohttp

from typing import Optional
from datetime import datetime

from mbta_client import MBTAClient
from mbta_stop import MBTAStop
from mbta_route import MBTARoute
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert
from mbta_utils import MBTAUtils

class JourneyManager:
    """A class to manage a journey on a route from/to stops."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str, max_journeys: int, depart_from_name: str , arrive_at_name: str, route_name: str = None) -> None:

        mbta_client = MBTAClient(session, api_key)
    
        self.mbta_client = mbta_client
        self.max_journeys = max_journeys
        self.depart_from_name = depart_from_name
        self.arrive_at_name = arrive_at_name
        self.route_name = route_name
        self.journeys: dict[str, Journey] = {} 
        self.route = None
        
    async def async_init(self):

        
        params = {
            'filter[location_type]' :'0'
        }
        
        tmp_stops = await self.mbta_client.list_stops(params)
        
        self.depart_from_stops = MBTAUtils.get_stops_by_name(tmp_stops, self.depart_from_name )
        self.arrive_at_stops = MBTAUtils.get_stops_by_name(tmp_stops, self.arrive_at_name )
        
        del tmp_stops
        
        if self.route_name is not None:
            tmp_routes: list[MBTARoute] = await self.mbta_client.list_routes()
            for route in tmp_routes:
                if route.long_name == self.route_name:
                    self.route: MBTARoute = route
                    break  # Found the route, no need to continue the loop
            del tmp_routes
            
        
    async def fetch_data(self):
        """Populate the journeys with schedules, predictions, trips, routes, and alerts."""
        try:
            logging.debug("Starting to populate journeys...")
            await self.__fetch_schedules()
            await self.__fetch_predictions()
            self.__sort_and_clean()
            await self.__fetch_trips()
            await self.__fetch_routes()
            await self.__fetch_alerts()
            logging.debug("Finished populating journeys.")
        except Exception as e:
            logging.error(f"Error populating journeys: {e}")
            traceback.print_exc()  # This will print the full traceback to the console

    async def __fetch_schedules(self):
        """Retrieve and process schedules based on the provided stop IDs and route ID."""        
        now = datetime.now().astimezone()
        
        params = {
            'filter[stop]': ','.join(MBTAUtils.get_stop_ids_from_stops(self.depart_from_stops + self.arrive_at_stops)),
            'filter[min_time]': now.strftime('%H:%M'),
            'filter[date]': now.strftime('%Y-%m-%d'),
            'sort': 'departure_time'
        }
        if self.route is not None:  
            params['filter[route]'] = self.route.id
        
        schedules: list[MBTASchedule] = await self.mbta_client.list_schedules(params)
        
        for schedule in schedules:
            
            # if the schedule trip id not in the journeys
            if schedule.trip_id not in self.journeys:
                # journey stops are ordered by departure time
                # if the first schedule stop is not in the depart stops ( = it's an arrival)
                if schedule.stop_id not in MBTAUtils.get_stop_ids_from_stops(self.depart_from_stops):
                    # skip the schedule
                    continue
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[schedule.trip_id] = journey
            
            # create the stop    
            journey_stop = JourneyStop(
                stop = MBTAUtils.get_stop_by_id((self.depart_from_stops + self.arrive_at_stops), schedule.stop_id),
                arrival_time=schedule.arrival_time,
                departure_time=schedule.departure_time,
                stop_sequence=schedule.stop_sequence
            )
            # add the stop to the journey 
            self.journeys[schedule.trip_id].add_stop(journey_stop)
            
            # get the journey stops
            stops = self.journeys[schedule.trip_id].journey_stops
            # if there are 2 stops and 
            # the departure stop (stops[0]) id is not in the departure stop ids OR the arrival stop (stops[1]) id is not in the arrival stop ids
            # ( = the trip is in the wrong direction)
            if len(stops) == 2 and (stops[0].stop.id not in MBTAUtils.get_stop_ids_from_stops(self.depart_from_stops) or stops[1].stop.id not in MBTAUtils.get_stop_ids_from_stops(self.arrive_at_stops)):
                # delete the yourney from the journeys dict
                del self.journeys[schedule.trip_id]
                              
    async def __fetch_predictions(self):
        """Retrieve and process predictions based on the provided stop IDs and route ID."""
        
        now = datetime.now().astimezone()
        
        journey_stops = self.depart_from_stops + self.arrive_at_stops
        journey_stops_ids = MBTAUtils.get_stop_ids_from_stops(self.depart_from_stops + self.arrive_at_stops)
        depart_stop_ids = MBTAUtils.get_stop_ids_from_stops(self.depart_from_stops)
        arrival_stop_ids = MBTAUtils.get_stop_ids_from_stops(self.arrive_at_stops)

        params = {
            'filter[stop]': ','.join(journey_stops_ids),
            'sort': 'departure_time'
        }
        if self.route is not None:  
            params['filter[route]'] = self.route.id
        
        predictions: list[MBTAPrediction] = await self.mbta_client.list_predictions(params)
        
        for prediction in predictions:
            
            is_cancelled_trip = prediction.schedule_relationship in ['CANCELLED', 'SKIPPED']
            is_past_trip = prediction.arrival_time and MBTAUtils.parse_datetime(prediction.arrival_time) < now
            is_departure_stop = prediction.stop_id in depart_stop_ids
            is_arrival_stop = prediction.stop_id in arrival_stop_ids

            # If the trip of the prediction is cancelled/skipped
            if is_cancelled_trip:
                # remove the journey on the same trip_id from the journeys dict
                self.journeys.pop(prediction.trip_id, None)
                continue
            
            # If the trip of the prediction is in the past remove it
            if is_past_trip:
                # remove the journey on the same trip_id from the journeys dict
                self.journeys.pop(prediction.trip_id, None)
                continue
            
            # if the trip of the prediciton is not in the journeys dict
            if prediction.trip_id not in self.journeys:
                # if the first stop is not a departure stop
                if is_departure_stop:
                    # skipp the prediction
                    continue
                
                # create the journey
                journey = Journey()
                # add the journey to the journeys dict using the trip_id as key
                self.journeys[prediction.trip_id] = journey
                
                # add (smart update) the stop to the journey in position 0 (departure)
                journey.update_journey_stop(
                    0,
                    stop=MBTAUtils.get_stop_by_id(journey_stops, prediction.stop_id),
                    arrival_time=prediction.arrival_time,
                    departure_time=prediction.departure_time,
                    stop_sequence=prediction.stop_sequence,
                    arrival_uncertainty=prediction.arrival_uncertainty,
                    departure_uncertainty=prediction.departure_uncertainty
                )
            
            # if the prediciton trip is in the journeys
            else:
                # get the journey
                journey: Journey = self.journeys[prediction.trip_id]
                
                # if the prediction stop id is in the departure stop ids
                if is_departure_stop:
            
                    # add (smart update) the stop to the journey in position 0 (departure)
                    journey.update_journey_stop(
                        0,
                        stop=MBTAUtils.get_stop_by_id(journey_stops, prediction.stop_id),
                        arrival_time=prediction.arrival_time,
                        departure_time=prediction.departure_time,
                        stop_sequence=prediction.stop_sequence,
                        arrival_uncertainty=prediction.arrival_uncertainty,
                        departure_uncertainty=prediction.departure_uncertainty
                    )
                            
                # if the prediction stop id is in the arrival stop ids 
                elif is_arrival_stop:

                    # add (smart update) the stop to the journey in position 1 (arrival)                    
                    journey.update_journey_stop(
                        1,
                        stop=MBTAUtils.get_stop_by_id(journey_stops, prediction.stop_id),
                        arrival_time=prediction.arrival_time,
                        departure_time=prediction.departure_time,
                        stop_sequence=prediction.stop_sequence,
                        arrival_uncertainty=prediction.arrival_uncertainty,
                        departure_uncertainty=prediction.departure_uncertainty
                    )
                         
    def __sort_and_clean(self):
        """Clean up and sort valid journeys."""
        now = datetime.now().astimezone()
       # Filter out invalid journeys
        processed_journeys = {
            trip_id: journey
            for trip_id, journey in self.journeys.items()
            if len(journey.journey_stops) >= 2 and 
            journey.journey_stops[0].stop_sequence <= journey.journey_stops[1].stop_sequence and
            journey.journey_stops[0].get_time() >= now
        }
        # Sort journeys based on departure time
        sorted_journeys = dict(
            sorted(
                processed_journeys.items(),
                key=lambda item: item[1].journey_stops[0].get_time()
            )
        )
        
        # Limit the number of journeys to `self.max_journeys`
        if self.max_journeys > 0:
            self.journeys = dict(list(sorted_journeys.items())[:self.max_journeys])
        else:
            self.journeys = {}

    async def __fetch_trips(self):
        """Retrieve trip details for each journey."""
        for trip_id, journey in self.journeys.items():
            try:
                trip: MBTATrip = await self.mbta_client.get_trip(trip_id)
                journey.trip = trip
            except Exception as e:
                logging.error(f"Error retrieving trip {trip_id}: {e}")
            
    async def __fetch_routes(self):
        """Retrieve route details for each journey."""

        routes: list[MBTARoute] = []
        
        if self.route is not None:
            routes.append(self.route)
        else:
            route_ids: list[str] = []
            for journey in self.journeys.values():
                if journey.trip and journey.trip.route_id and journey.trip.route_id not in route_ids:
                    route_ids.append(journey.trip.route_id)
                    
            # Fetch route details
            for route_id in route_ids:
                try:
                    route: MBTARoute = await self.mbta_client.get_route(route_id)
                    routes.append(route)
                except Exception as e:
                    logging.error(f"Error retrieving route {route_id}: {e}")
        
        route_dict = {route.id: route for route in routes}
        
        for journey in self.journeys.values():
            if journey.trip and journey.trip.route_id in route_dict:
                journey.route = route_dict[journey.trip.route_id]
                
    async def __fetch_alerts(self):
        """Retrieve and associate alerts with the relevant journeys."""
        params = {
            'filter[stop]': ','.join(self._get_all_stop_ids()),
            'filter[trip]': ','.join(self._get_all_trip_ids()),
            'filter[route]': ','.join(self._get_all_route_ids()),
            'filter[activity]': 'BOARD,EXIT,RIDE'
        }
        
        alerts: list[MBTAAlert] = await self.mbta_client.list_alerts(params)
        
        now = datetime.now().astimezone()
               
        for alert in alerts:
            
            if MBTAUtils.parse_datetime(alert.active_period_start) < now and  MBTAUtils.parse_datetime(alert.active_period_end) > now:
            

                for journey in self.journeys.values():
                    
                    # if the alert is already in the journey
                    if alert in journey.alerts:
                        # skip the journey
                        continue
                    
                    for informed_entity in alert.informed_entities:
                                        
                        # if informed entity stop is not null and the stop id is in not in the journey stop id
                        if informed_entity.get('stop') != '' and informed_entity['stop'] not in journey.get_stop_ids():
                            # skip the journey
                            continue
                        # if informed entity trip is not null and the trip id is not in the journey trip id
                        if informed_entity.get('trip')  != '' and informed_entity['trip'] != journey.trip.id:
                            # skip the journey
                            continue
                        # if informed entity route is not null and the route id is not in the journey route id
                        if informed_entity.get('route') != '' and informed_entity['route'] != journey.route.id:
                            # skip the journey
                            continue
                        # If the informed entity stop is a departure and the informed entity activities don't include BOARD or RIDE
                        if informed_entity['stop'] == journey.journey_stops[0].stop.id and not any(activity in informed_entity.get('activities', []) for activity in ['BOARD', 'RIDE']):
                            # Skip the journey
                            continue
                        # If the informed entity stop is an arrival and the informed entity activities don't include EXIT or RIDE
                        if informed_entity['stop'] == journey.journey_stops[1].stop.id and not any(activity in informed_entity.get('activities', []) for activity in ['EXIT', 'RIDE']):
                            # Skip the journey
                            continue
                        # add the alert to the journy
                        journey.alerts.append(alert)

    def _get_all_stop_ids(self) -> list[str]:
        """Retrieve a list of all unique stop IDs from the journeys."""
        stop_ids = set()
        for journey in self.journeys.values():
            stop_ids.update(journey.get_stop_ids())
        return sorted(list(stop_ids))

    def _get_all_trip_ids(self) -> list[str]:
        """Retrieve a list of all trip IDs from the journeys."""
        return list(self.journeys.keys())
 
    def _get_all_route_ids(self) -> list[str]:
        """Retrieve a list of all unique route IDs from the journeys."""
        route_ids = set()
        for journey in self.journeys.values():
            if journey.trip and journey.trip.route_id:
                route_ids.add(journey.trip.route_id)
        return sorted(list(route_ids))
    

class Journey:
    """A class to manage a journey with multiple stops."""

    def __init__(self) -> None:
        
        self.route: Optional[MBTARoute] = None
        self.trip: Optional[MBTATrip] = None
        self.alerts: list[MBTAAlert] = []
        self.journey_stops: list[JourneyStop] = []

    def __repr__(self) -> str:
        stops_repr = ', '.join([repr(stop) for stop in self.journey_stops])
        return f"MBTAjourney(route={self.route}, trip={self.trip}, stops=[{stops_repr}])"
    
    def add_stop(self, stop: 'JourneyStop') -> None:
        """Add a stop to the journey."""
        self.journey_stops.append(stop) 
    
    def get_stop_ids(self) -> list[str]:
        """Return a list of stop IDs for all stops in the journey."""
        return [journey_stop.stop.id for journey_stop in self.journey_stops]
    
    def find_jounrey_stop_by_id(self, stop_id: str) -> Optional['JourneyStop']:
        """Return the MBTAjourneyStop with the given stop_id, or None if not found."""
        for journey_stop in self.journey_stops:
            if journey_stop.stop.id == stop_id:
                return journey_stop
        return None
    
    def update_journey_stop(self, stop_index: int, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None):
    
        if (stop_index == 0 and len(self.journey_stops ) == 0) or (stop_index == 1 and len(self.journey_stops ) == 1):
            journey_stop = JourneyStop(stop, arrival_time, departure_time, stop_sequence, arrival_uncertainty, departure_uncertainty)
            self.journey_stops.append(journey_stop)
        else:
            self.journey_stops[stop_index].update_stop(stop, arrival_time, departure_time, stop_sequence, arrival_uncertainty, departure_uncertainty)


    def get_route_short_name(self) -> Optional[str]:
        if self.route:
            return self.route.short_name
        return None
        
    def get_route_long_name(self) -> Optional[str]:
        if self.route:
            return self.route.long_name
        return None

    def get_route_color(self) -> Optional[str]:
        if self.route:
            return self.route.color
        return None

    def get_route_description(self) -> Optional[str]:
        from mbta_utils import MBTAUtils
        if self.route:
            return MBTAUtils.get_route_type_desc_by_type_id(self.route.type)
        return None

    def get_route_type(self) -> Optional[str]:
        if self.route:
            return self.route.type
        return None
    
    def get_trip_headsign(self) -> Optional[str]:
        if self.trip:
            return self.trip.headsign
        return None

    def get_trip_name(self) -> Optional[str]:
        if self.trip:
            return self.trip.name
        return None

    def get_trip_destination(self) -> Optional[str]:
        if self.trip and self.route:
            trip_direction = self.trip.direction_id
            return self.route.direction_destinations[trip_direction]
        return None

    def get_trip_direction(self) -> Optional[str]:
        if self.trip and self.route:
            trip_direction = self.trip.direction_id
            return self.route.direction_names[trip_direction]
        return None

    def get_stop_name(self, stop_index: int) -> Optional[str]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.stop.name

    def get_platform_name(self, stop_index: int) -> Optional[str]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.stop.platform_name

    def get_stop_time(self, stop_index: int) -> Optional[datetime]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.get_time()

    def get_stop_delay(self, stop_index: int) -> Optional[float]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.get_delay()
    
    def get_stop_time_to(self, stop_index: int) -> Optional[float]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.get_time_to()
    
    def get_stop_uncertainty(self, stop_index: int) -> Optional[str]:
        journey_stop = self.journey_stops[stop_index]
        return journey_stop.get_uncertainty()
    
    def get_alert_header(self, alert_index: int) -> Optional[str]:
        alert = self.alerts[alert_index]
        return alert.header_text

class JourneyStop:
    
    """A journey stop object to hold and manage arrival and departure details."""

    def __init__(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None) -> None:

        now = datetime.now().astimezone()

        self.stop = stop
        self.arrival_time = MBTAUtils.parse_datetime(arrival_time)
        self.real_arrival_time = None
        self.arrival_uncertainty = MBTAUtils.get_uncertainty_description(arrival_uncertainty)
        self.arrival_delay = None
        self.time_to_arrival = MBTAUtils.time_to(self.arrival_time, now)

        self.departure_time = MBTAUtils.parse_datetime(departure_time)
        self.real_departure_time = None
        self.departure_uncertainty = MBTAUtils.get_uncertainty_description(departure_uncertainty)
        self.departure_delay = None
        self.time_to_departure = MBTAUtils.time_to(self.departure_time, now)

        self.stop_sequence = stop_sequence

    def __repr__(self) -> str:
        return (f"MBTAjourneyStop(stop={repr(self.stop)}")

    def update_stop(self, stop: MBTAStop, arrival_time: str, departure_time: str, stop_sequence: int = None, arrival_uncertainty: Optional[str] = None,   departure_uncertainty: Optional[str] = None) -> None:
        """Update the stop details, including real arrival and departure times, uncertainties, and delays."""
        
        now = datetime.now().astimezone()
                
        self.stop = stop
        self.stop_sequence = stop_sequence
        if arrival_time is not None:
            self.real_arrival_time = MBTAUtils.parse_datetime(arrival_time)
            if self.arrival_time is not None:
                self.arrival_delay = MBTAUtils.compute_delay(self.real_arrival_time, self.arrival_time)
                self.time_to_arrival = MBTAUtils.time_to(self.real_arrival_time, now)
        if departure_time is not None:
            self.real_departure_time = MBTAUtils.parse_datetime(departure_time)
            if self.departure_time is not None:
                self.departure_delay = MBTAUtils.compute_delay(self.real_departure_time, self.departure_time)
                self.time_to_departure = MBTAUtils.time_to(self.real_departure_time, now)
        if arrival_uncertainty is not None:
            self.arrival_uncertainty = arrival_uncertainty
        if departure_uncertainty is not None:
            self.departure_uncertainty = departure_uncertainty

    def get_time(self) -> Optional[datetime]:
        """Return the most relevant time for the stop."""
        if self.real_arrival_time is not None:
            return self.real_arrival_time
        if self.real_departure_time is not None:
            return self.real_departure_time
        if self.arrival_time is not None:
            return self.arrival_time
        if self.departure_time is not None:
            return self.departure_time
        return None
    
    def get_delay(self) -> Optional[float]:
        """Return the most relevant delay for the stop."""
        if self.arrival_delay is not None:
            return self.arrival_delay
        if self.departure_delay is not None:
            return self.departure_delay
        return None
        
    def get_time_to(self) -> Optional[float]:
        """Return the most relevant time to for the stop."""
        return self.time_to_arrival or self.time_to_departure
    
    def get_uncertainty(self) -> Optional[str]:
        """Return the most relevant time to for the stop."""
        return self.arrival_uncertainty or self.departure_uncertainty



