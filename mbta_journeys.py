import logging
from typing import Any, Dict, Optional, List, Union, OrderedDict
from datetime import datetime
from mbta import MBTA
from mbta_route import MBTAroute
from mbta_schedule import MBTAschedule
from mbta_prediction import MBTAprediction
from mbta_journey import MBTAjourney, MBTAjourneyStop

class MBTAjourneys:
    """A class to manage a journey on a route from/to stops."""

    def __init__(self, mbta_client: MBTA, route: MBTAroute, depart_from: str, arrive_at: str) -> None:
        self.mbta_client = mbta_client
        self.route = route
        
        self.direction_id = None
        self.direction_name = None
        self.direction_destination= None
        
        self.stop_ids = {}
        self.journeys = {}

        self.depart_from = depart_from
        self.arrive_at = arrive_at
        
    def __repr__(self) -> str:
        return (f"MBTAjourneys(mbta_client={self.mbta_client}, route={self.route}, "
                f"depart_from='{self.depart_from}', arrive_at='{self.arrive_at}', "
                f"direction_name={self.direction_name}, direction_destination={self.direction_destination}, "
                f"stops={self.stops}, journeys={self.journeys})")
        
    async def populate(self):
        
        await self._initialize()
        await self._add_schedules()
        await self._add_predictions()
        self._process_journeys()
        

    async def _initialize(self):
        """Initialize the stops with their IDs."""
        depart_from_stop_id, arrive_at_stop_id = await self._get_stops_ids(self.depart_from, self.arrive_at)
        
        self.stop_ids['depart_from'] = [depart_from_stop_id]
        self.stop_ids['arrive_at'] = [arrive_at_stop_id]
        
        
    async def _get_stops_ids(self, depart_from_stop_name: str, arrive_at_stop_name: str):
        params = {'filter[route]': self.route.route_id}
        route_stops = await self.mbta_client.list_stops(params)
        
        depart_from_stop_id = next((stop.stop_id for stop in route_stops if stop.stop_name == depart_from_stop_name), None)
        arrive_at_stop_id = next((stop.stop_id for stop in route_stops if stop.stop_name == arrive_at_stop_name), None)
        
        return depart_from_stop_id, arrive_at_stop_id
         
        
    async def _add_schedules(self):
        
        now = datetime.now()
        
        params = {
            'filter[route]': self.route.route_id,
            'filter[stop]': ','.join([self.stop_ids['depart_from'][0], self.stop_ids['arrive_at'][0]]),
            'filter[min_time]': now.strftime('%H:%M'),
            'filter[date]': now.strftime('%Y-%m-%d'),
            'sort': 'departure_time'
        }
        
        # Get schedules 
        schedules: List[MBTAschedule] = await self.mbta_client.list_schedules(params)
        
        # Process schedules
        for schedule in schedules:
            # Add the current schedule to the journey
            self._add_journey(schedule)
            
            # Get the stop type corresponding to the schedule.stop_id
            stop_type = await self._retrieve_stop_type(schedule.stop_id)
            
            # if diretion has not been detected yet and the journey alteady exist and has already 1 stop
            if self.direction_id is None and self.journeys[schedule.trip_id] and self.journeys[schedule.trip_id].count_stops() == 1:
                # if the second stop is a depart
                if stop_type == 'depart_from':
                    # delete the existing journey
                    del self.journeys[schedule.trip_id]
                    continue
                else:
                    # set journeys direction
                    self.direction_id = schedule.direction_id
                    self.direction_name = self.route.route_direction_names[schedule.direction_id]
                    self.direction_destination = self.route.route_direction_destinations[schedule.direction_id]
                
            # if direction has not been set yet or the direction is the expected one    
            if self.direction_id is None or self.direction_id == schedule.direction_id:
            
                # Add the stop to the current journey
                self.journeys[schedule.trip_id].add_stop(stop_type, MBTAjourneyStop(
                    stop_id=schedule.stop_id,
                    arrival_time=schedule.arrival_time,
                    departure_time=schedule.departure_time,
                    stop_sequence=schedule.stop_sequence
                ))
                
            else:
                # delete the existing journey
                del self.journeys[schedule.trip_id]
                

    def _add_journey(self, data: Union[MBTAschedule, MBTAprediction]):
      
        trip_id = data.trip_id
        
        headsign = getattr(data, 'stop_headsign', None) if isinstance(data, MBTAschedule) else None
        
        if trip_id not in self.journeys:
            self.journeys[trip_id] = MBTAjourney(
                direction_id = data.direction_id,
                headsign=headsign
            )
            
    async def _retrieve_stop_type(self, stop_id: str) -> str:
        if stop_id in self.stop_ids['depart_from']:
            return 'depart_from'
        
        if stop_id in self.stop_ids['arrive_at']:
            return 'arrive_at'

        # The stop_id is not tracked; retrieve stop details
        stop = await self.mbta_client.get_stop(stop_id)
        
        # Check and categorize the stop
        if stop.stop_name == self.depart_from:
            self.stop_ids['depart_from'].append(stop_id)
            return 'depart_from'
        
        if stop.stop_name == self.arrive_at:
            self.stop_ids['arrive_at'].append(stop_id)
            return 'arrive_at'
        

        
    async def _add_predictions(self):
            
            params = {
                'filter[route]': self.route.route_id,
                'filter[stop]': ','.join([self.stop_ids['depart_from'][0], self.stop_ids['arrive_at'][0]]),
                'sort': 'departure_time'
            }
            
            # Get schedules 
            predictions: List[MBTAprediction] = await self.mbta_client.list_predictions(params)
            
            # Process schedules
            for prediction in predictions:
                
                #if the journey update is not of type CANCELLED or SKIPPED or the journey direction is not the expected one 
                if prediction.schedule_relationship == 'CANCELLED' or prediction.schedule_relationship == 'SKIPPED' or self.direction_id != prediction.direction_id:
                    # if thre trip is in the journeys
                    if prediction.trip_id in self.journeys:
                        # delete it
                        del self.journeys[prediction.trip_id]
                
                else:
                    
                    # add the current prediction to the journey
                    self._add_journey(prediction)
                        
                    # Get the stop name corresponding to the journeys.stop_id
                    stop_type = await self._retrieve_stop_type(prediction.stop_id)
                    
                    # get the stop corresponding to the stop_name
                    stop = self.journeys[prediction.trip_id].get_stop_by_stop_type(stop_type)
        
                    # if stop is none (= not in the journeys)
                    if stop == None:
                        # add the stop
                        self.journeys[prediction.trip_id].add_stop(stop_type, MBTAjourneyStop(
                            stop_id=prediction.stop_id,
                            arrival_time=prediction.arrival_time,
                            departure_time=prediction.departure_time,
                            stop_sequence=prediction.stop_sequence
                        ))
                    else:
                        # update the existing stop
                        stop.update_stop(prediction.stop_id, prediction.arrival_time,prediction.arrival_uncertainty, prediction.departure_time,prediction.departure_uncertainty )
   
                                    
    def _process_journeys(self):
        """Clean up and sort valid journeys."""
        processed_journeys = {}


        for trip_id, journey in self.journeys.items():
            
            if journey.direction_id  != self.direction_id:
                continue

            processed_journeys[trip_id] = journey
            
        self.journeys = dict(
            sorted(
                processed_journeys.items(),
                key=lambda item: self._get_first_stop_departure_time(item[1])
            )
        )
        

    def _get_first_stop_departure_time(self, journey: MBTAjourney) -> datetime:
        """Get the departure time of the first stop in a journey."""
        first_stop = journey.get_stops()[0]
        return first_stop.get_time()
