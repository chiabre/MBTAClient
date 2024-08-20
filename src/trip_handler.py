import aiohttp
import datetime

from base_handler import BaseHandler
from journey import Journey
from mbta_route import MBTARoute
from mbta_trip import MBTATrip
from mbta_stop import MBTAStop
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_utils import MBTAUtils

class TripHandler(BaseHandler):
    """Handler for managing a specific trip."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str, depart_from_name: str, arrive_at_name: str, trip_name: str):
        super().__init__(session, api_key,depart_from_name,arrive_at_name)
        self.trip_name = trip_name
        
    async def fetch_trip(self):
        
        await self.trip_init()
       
        schedules = await self.__fetch_schedules()
        await self._process_schedules(schedules)
        
        predictions = await self.__fetch_predictions()
        await self._process_predictions(predictions)
        
        alerts = await self.__fetch_alerts()
        self._process_alerts(alerts)  
        
        return  next(iter(self.journeys.values()))
    
    
    async def trip_init(self):
        
        params = {
            'filter[revenue]' :'REVENUE',
            'filter[name]' : self.trip_name
        }
        
        trips: list[MBTATrip] = await self.mbta_client.list_trips(params)
        
        journey = Journey()
        
        journey.trip = trips[0]
        
        route: MBTARoute = await self.mbta_client.get_route(journey.trip.route_id)
        
        journey.route = route
        
        self.journeys[trips[0].id] = journey


    async def __fetch_schedules(self) -> list[MBTASchedule]:
        
        jounrey = next(iter(self.journeys.values()))
        jounrey.trip.id
        
        params = {
            'filter[trip]':  jounrey.trip.id,
        }
        
        schedules = await super()._fetch_schedules(params)
        
        return schedules


    async def __fetch_predictions(self) -> list[MBTAPrediction]:
        
        jounrey = next(iter(self.journeys.values()))
        jounrey.trip.id
        
        params = {
            'filter[trip]':  jounrey.trip.id,
        }
        
        predictions = await super()._fetch_predictions(params)
        
        return predictions                   


    async def __fetch_alerts(self) -> list[MBTAPrediction]:
        
        jounrey = next(iter(self.journeys.values()))
        jounrey.trip.id
        
        params = {
            'filter[trip]':  jounrey.trip.id,
        }
        
        alerts = await super()._fetch_alerts(params)
        
        return alerts   