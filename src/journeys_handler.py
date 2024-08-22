import aiohttp
import logging

from datetime import datetime

from base_handler import BaseHandler
from journey import Journey
from mbta_route import MBTARoute
from mbta_trip import MBTATrip
from mbta_schedule import MBTASchedule


class JourneysHandler(BaseHandler):
    """Handler for managing a specific journey."""

    def __init__(self, session: aiohttp.ClientSession, logger: logging.Logger,  depart_from_name: str, arrive_at_name: str, max_journeys: int, api_key:str = None) :
        super().__init__(session, logger, depart_from_name,arrive_at_name, api_key)
        self.max_journeys = max_journeys
    
    async def async_init(self):
        await super()._async_init()
        
    async def update(self) -> list[Journey]:
       
        schedules = await self.__fetch_schedules()
        await super()._process_schedules(schedules)
        
        predictions = await self._fetch_predictions()
        await super()._process_predictions(predictions)
        
        self.__sort_and_clean()
        
        await self.__fetch_trips()
        
        await self.__fetch_routes()
        
        alerts = await self._fetch_alerts()
        super()._process_alerts(alerts)  
        
        return  list(self.journeys.values())
    
    async def __fetch_schedules(self) -> list[MBTASchedule]:
        
        now = datetime.now().astimezone()
        
        params = {
            'filter[stop]': ','.join(super()._get_stops_ids()),
            'filter[min_time]': now.strftime('%H:%M'),
        }
        
        schedules = await super()._fetch_schedules(params)
        
        return schedules
    
    def __sort_and_clean(self):
        """Clean up and sort valid journeys."""
        
        now = datetime.now().astimezone()
        
        processed_journeys = {
            trip_id: journey
            for trip_id, journey in self.journeys.items()
            if journey.stops['departure'] 
            and journey.stops['arrival'] 
            and journey.stops['departure'].stop_sequence < journey.stops['arrival'].stop_sequence
            and journey.stops['departure'].get_time()  >= now
        }

        sorted_journeys = dict(
            sorted(
                processed_journeys.items(),
                key=lambda item: item[1].stops['departure'].get_time()
            )
        )

        self.journeys = dict(list(sorted_journeys.items())[:self.max_journeys] if self.max_journeys > 0 else sorted_journeys)

    async def __fetch_trips(self):
        """Retrieve trip details for each journey."""
        for trip_id, journey in self.journeys.items():
            trip: MBTATrip = await super()._fetch_trip(trip_id)
            journey.trip = trip

    async def __fetch_routes(self):
        """Retrieve route details for each journey."""
        for journey in self.journeys.values():
            if journey.trip and journey.trip.route_id:
                route: MBTARoute = await super()._fetch_route(journey.trip.route_id)
                journey.route = route              