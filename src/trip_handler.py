from typing import Optional
import traceback
import aiohttp

from base_handler import BaseHandler
from journey import Journey
from mbta_route import MBTARoute
from mbta_trip import MBTATrip
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction

class TripHandler(BaseHandler):
    """Handler for managing a specific trip."""

    def __init__(self, session: aiohttp.ClientSession, logger,  depart_from_name: str, arrive_at_name: str, trip_name: str, api_key:str = None ) :
        super().__init__(session, logger, depart_from_name, arrive_at_name, api_key) 
        self.trip_name = trip_name
        
            
    async def async_init(self):
        await super()._async_init()

        params = {
            'filter[revenue]' :'REVENUE',
            'filter[name]' : self.trip_name
        }
        trips: list[MBTATrip] = await super()._fetch_trips(params)
        
        journey = Journey()
        journey.trip = trips[0]
        
        route: MBTARoute = await super()._fetch_route(journey.trip.route_id)
        
        journey.route = route
        self.journeys[trips[0].id] = journey
    
    async def update(self) -> list[Journey]:
              
        schedules = await self.__fetch_schedules()
        await super()._process_schedules(schedules)
        
        predictions = await self.__fetch_predictions()
        await super()._process_predictions(predictions)
        
        alerts = await self.__fetch_alerts()
        super()._process_alerts(alerts)  
        return  list(self.journeys.values())
    
    
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