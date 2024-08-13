import logging
import traceback
from typing import Any, Dict, Optional, List
from datetime import datetime
from mbta_client import MBTAClient
from mbta_stop import MBTAStop
from mbta_route import MBTARoute
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_journey import MBTAJourney, MBTAJourneyStop

class MBTAJourneys:
    """A class to manage a journey on a route from/to stops."""

    def __init__(self, mbta_client: MBTAClient, max_journeys: int, depart_from_stops: List[MBTAStop], arrive_at_stops: List[MBTAStop], route: MBTARoute = None) -> None:
        self.mbta_client = mbta_client
        self.max_journeys = max_journeys
        self.depart_from_stops = depart_from_stops
        self.arrive_at_stops = arrive_at_stops
        self.route = route
        self.journeys: Dict[str, MBTAJourney] = {} 
        
    async def populate(self):
        """Populate the journeys with schedules, predictions, trips, routes, and alerts."""
        try:
            logging.debug("Starting to populate journeys...")
            await self.__schedules()
            await self.__predictions()
            self.__finalize_journeys()
            await self.__trips()
            await self.__routes()
            await self.__alerts()
            logging.debug("Finished populating journeys.")
        except Exception as e:
            logging.error(f"Error populating journeys: {e}")
            traceback.print_exc()  # This will print the full traceback to the console
            print()

    async def __schedules(self):
        """Retrieve and process schedules based on the provided stop IDs and route ID."""
        now = datetime.now()
        params = {
            'filter[stop]': ','.join(self._get_stop_ids_from_stops(self.depart_from_stops + self.arrive_at_stops)),
            'filter[min_time]': now.strftime('%H:%M'),
            'filter[date]': now.strftime('%Y-%m-%d'),
            'sort': 'departure_time'
        }
        if self.route:  
            params['filter[route]'] = self.route.id
        
        schedules: List[MBTASchedule] = await self.mbta_client.list_schedules(params)
        
        for schedule in schedules:
            # if the schedule trip id not in the journeys
            if schedule.trip_id not in self.journeys:
                # journey stops are ordered by departure time
                # if the first schedule stop is not in the depart stops ( = it's an arrival)
                if schedule.stop_id not in self._get_stop_ids_from_stops(self.depart_from_stops):
                    # skip the schedule
                    continue
                # create the journey
                journey = MBTAJourney()
                # add the journey to the journeys Dict using the trip_id as key
                self.journeys[schedule.trip_id] = journey
            
            # create the stop    
            journey_stop = MBTAJourneyStop(
                stop = self._get_stop_by_id((self.depart_from_stops + self.arrive_at_stops), schedule.stop_id),
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
            if len(stops) == 2 and (stops[0].stop.id not in self._get_stop_ids_from_stops(self.depart_from_stops) or stops[1].stop.id  not in self._get_stop_ids_from_stops(self.arrive_at_stops)):
                # delete the yourney from the journeys Dict
                del self.journeys[schedule.trip_id]
                              
    async def __predictions(self):
        """Retrieve and process predictions based on the provided stop IDs and route ID."""
        
        now = datetime.now().astimezone()
        
        journey_stops = self.depart_from_stops + self.arrive_at_stops
        journey_stops_ids = self._get_stop_ids_from_stops(self.depart_from_stops + self.arrive_at_stops)
        depart_stop_ids = self._get_stop_ids_from_stops(self.depart_from_stops)
        arrival_stop_ids = self._get_stop_ids_from_stops(self.arrive_at_stops)

        params = {
            'filter[stop]': ','.join(journey_stops_ids),
            'sort': 'departure_time'
        }
        if self.route:  
            params['filter[route]'] = self.route.id
        
        predictions: List[MBTAPrediction] = await self.mbta_client.list_predictions(params)
        
        for prediction in predictions:
            
            is_cancelled_trip = prediction.schedule_relationship in ['CANCELLED', 'SKIPPED']
            is_past_trip = prediction.arrival_time and datetime.fromisoformat(prediction.arrival_time) < now
            is_departure_stop = prediction.stop_id in depart_stop_ids
            is_arrival_stop = prediction.stop_id in arrival_stop_ids

            # If the trip of the prediction is cancelled/skipped
            if is_cancelled_trip:
                # remove the journey on the same trip_id from the journeys Dict
                self.journeys.pop(prediction.trip_id, None)
                continue
            
            # If the trip of the prediction is in the past remove it
            if is_past_trip:
                # remove the journey on the same trip_id from the journeys Dict
                self.journeys.pop(prediction.trip_id, None)
                continue
            
            # if the trip of the prediciton is not in the journeys Dict
            if prediction.trip_id not in self.journeys:
                # if the first stop is not a departure stop
                if is_departure_stop:
                    # skipp the prediction
                    continue
                
                # create the journey
                journey = MBTAJourney()
                # add the journey to the journeys Dict using the trip_id as key
                self.journeys[prediction.trip_id] = journey
                
                # add (smart update) the stop to the journey in position 0 (departure)
                journey.update_journey_stop(
                    0,
                    stop=self._get_stop_by_id(journey_stops, prediction.stop_id),
                    arrival_time=prediction.arrival_time,
                    departure_time=prediction.departure_time,
                    stop_sequence=prediction.stop_sequence,
                    arrival_uncertainty=prediction.arrival_uncertainty,
                    departure_uncertainty=prediction.departure_uncertainty
                )
            
            # if the prediciton trip is in the journeys
            else:
                # get the journey
                journey: MBTAJourney = self.journeys[prediction.trip_id]
                
                # if the prediction stop id is in the departure stop ids
                if is_departure_stop:
            
                    # add (smart update) the stop to the journey in position 0 (departure)
                    journey.update_journey_stop(
                        0,
                        stop=self._get_stop_by_id(journey_stops, prediction.stop_id),
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
                        stop=self._get_stop_by_id(journey_stops, prediction.stop_id),
                        arrival_time=prediction.arrival_time,
                        departure_time=prediction.departure_time,
                        stop_sequence=prediction.stop_sequence,
                        arrival_uncertainty=prediction.arrival_uncertainty,
                        departure_uncertainty=prediction.departure_uncertainty
                    )
                         
    def __finalize_journeys(self):
        """Clean up and sort valid journeys."""
        processed_journeys = {}
        
        for trip_id, journey in self.journeys.items():
            # remove journey with 1 stop or with wrong stop sequence
            stops = journey.journey_stops
            if len(stops) < 2 or stops[0].stop_sequence > stops[1].stop_sequence:
                continue
            processed_journeys[trip_id] = journey
            
        # Sort journeys based on departure time
        sorted_journeys = dict(
            sorted(
                processed_journeys.items(),
                key=lambda item: self._get_first_stop_departure_time(item[1])
            )
        )
        
        # Limit the number of journeys to `self.max_journeys`
        self.journeys = dict(list(sorted_journeys.items())[:self.max_journeys])

    async def __trips(self):
        """Retrieve trip details for each journey."""
        for trip_id, journey in self.journeys.items():
            try:
                trip: MBTATrip = await self.mbta_client.get_trip(trip_id)
                journey.trip = trip
            except Exception as e:
                logging.error(f"Error retrieving trip {trip_id}: {e}")
            
    async def __routes(self):
        """Retrieve route details for each journey."""

        routes: List[MBTARoute] = []
        
        if self.route is not None:
            routes.append(self.route)
        else:
            route_ids: List[str] = []
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
                
    async def __alerts(self):
        """Retrieve and associate alerts with the relevant journeys."""
        params = {
            'filter[stop]': ','.join(self._get_all_stop_ids()),
            'filter[trip]': ','.join(self._get_all_trip_ids()),
            'filter[route]': ','.join(self._get_all_route_ids()),
            'filter[activity]': 'BOARD,EXIT,RIDE'
        }
        
        alerts: List[MBTAAlert] = await self.mbta_client.list_alerts(params)
        
        now = datetime.now().astimezone()
               
        for alert in alerts:
            
            if datetime.fromisoformat(alert.active_period_start) > now and datetime.fromisoformat(alert.active_period_end) < now:
            
                for informed_entity in alert.informed_entities:
                    for journey in self.journeys.values():
                        
                        # if the alert is already in the journey
                        if alert in journey.alerts:
                            # skip the journey
                            continue
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

    def _get_stop_ids_from_stops(self, stops: List[MBTAStop]) -> List[str]:
        """Extract stop IDs from a list of MBTAstop objects."""
        stop_ids = [stop.id for stop in stops]
        return stop_ids
    
    def _get_stop_by_id(self, stops: List[MBTAStop], stop_id: str) -> Optional[MBTAStop]:
        """Retrieve a stop from the list of MBTAstop objects based on the stop ID."""
        for stop in stops:
            if stop.id == stop_id:
                return stop
        return None
                           
    def _get_first_stop_departure_time(self, journey: MBTAJourney) -> datetime:
        """Get the departure time of the first stop in a journey."""
        departure_stop = journey.journey_stops[0]
        return departure_stop.get_time()
    
    def _get_all_stop_ids(self) -> List[str]:
        """Retrieve a list of all unique stop IDs from the journeys."""
        stop_ids = set()
        for journey in self.journeys.values():
            stop_ids.update(journey.get_stop_ids())
        return sorted(list(stop_ids))

    def _get_all_trip_ids(self) -> List[str]:
        """Retrieve a list of all trip IDs from the journeys."""
        return list(self.journeys.keys())

    def _get_all_route_ids(self) -> List[str]:
        """Retrieve a list of all unique route IDs from the journeys."""
        route_ids = set()
        for journey in self.journeys.values():
            if journey.trip and journey.trip.route_id:
                route_ids.add(journey.trip.route_id)
        return sorted(list(route_ids))
    
    def get_route_short_name(self, journey: MBTAJourney) -> Optional[str]:
        """Get the long name of the route for a given journey."""
        if journey.route:
            return journey.route.short_name
        return None
        
    def get_route_long_name(self, journey: MBTAJourney) -> Optional[str]:
        """Get the long name of the route for a given journey."""
        if journey.route:
            return journey.route.long_name
        return None

    def get_route_color(self, journey: MBTAJourney) -> Optional[str]:
        """Get the color of the route for a given journey."""
        if journey.route:
            return journey.route.color
        return None

    def get_route_description(self, journey: MBTAJourney) -> Optional[str]:
        """Get the description of the route for a given journey."""
        if journey.route:
            return MBTARoute.get_route_type_desc_by_type_id(journey.route.type)
        return None

    def get_route_type(self, journey: MBTAJourney) -> Optional[str]:
        """Get the description of the route for a given journey."""
        if journey.route:
            return journey.route.type
        return None
    
    def get_trip_headsign(self, journey: MBTAJourney) -> Optional[str]:
        """Get the headsign of the trip for a given journey."""
        if journey.trip:
            return journey.trip.headsign
        return None

    def get_trip_name(self, journey: MBTAJourney) -> Optional[str]:
        if journey.trip:
            return journey.trip.name
        return None

    def get_trip_destination(self, journey: MBTAJourney) -> Optional[str]:
        if journey.trip and journey.route:
            trip_direction = journey.trip.direction_id
            return journey.route.direction_destinations[trip_direction]
        return None

    def get_trip_direction(self, journey: MBTAJourney) -> Optional[str]:
        if journey.trip and journey.route:
            trip_direction = journey.trip.direction_id
            return journey.route.direction_names[trip_direction]
        return None

    def get_stop_name(self, journey: MBTAJourney, stop_index: int) -> Optional[str]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.stop.name

    def get_platform_name(self, journey: MBTAJourney, stop_index: int) -> Optional[str]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.stop.platform_name

    def get_stop_time(self, journey: MBTAJourney, stop_index: int) -> Optional[datetime]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.get_time()

    def get_stop_delay(self, journey: MBTAJourney, stop_index: int) -> Optional[float]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.get_delay()
    
    def get_stop_time_to(self, journey: MBTAJourney, stop_index: int) -> Optional[float]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.get_time_to()
    
    def get_stop_uncertainty(self, journey: MBTAJourney, stop_index: int) -> Optional[str]:
        journey_stop = journey.journey_stops[stop_index]
        return journey_stop.get_uncertainty()
    
    def get_alert_header(self, journey: MBTAJourney, alert_index: int) -> Optional[str]:
        alert = journey.alerts[alert_index]
        return alert.header_text

