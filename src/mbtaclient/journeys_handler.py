import aiohttp
import logging
from datetime import datetime

from .base_handler import BaseHandler
from .journey import Journey
from .route import MBTARoute
from .trip import MBTATrip
from .schedule import MBTASchedule


class JourneysHandler(BaseHandler):
    """Handler for managing a specific journey."""

    def __init__(self, depart_from_name: str, arrive_at_name: str, max_journeys: int = 4, api_key: str = None, session: aiohttp.ClientSession = None, logger: logging.Logger = None):
        super().__init__(depart_from_name=depart_from_name, arrive_at_name=arrive_at_name, api_key=api_key, session=session, logger=logger) 
        self.max_journeys = max_journeys
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
            
    async def async_init(self):
        try:
            await super()._async_init()
        except Exception as e:
            self.logger.error("Error during async initialization: {}".format(e))
            raise
    
    async def update(self) -> list[Journey]:
        try:
            schedules = await self.__fetch_schedules()
            await super()._process_schedules(schedules)
            
            predictions = await self._fetch_predictions()
            await super()._process_predictions(predictions)
            
            self.__sort_and_clean()
            
            await self.__fetch_trips()
            
            await self.__fetch_routes()
            
            alerts = await self._fetch_alerts()
            super()._process_alerts(alerts)  
            
            return list(self.journeys.values())
        except Exception as e:
            self.logger.error("Error during update: {}".format(e))
            raise
    
    async def __fetch_schedules(self) -> list[MBTASchedule]:
        try:
            now = datetime.now().astimezone()
            
            params = {
                'filter[stop]': ','.join(super()._get_stops_ids()),
                'filter[min_time]': now.strftime('%H:%M'),
            }
            
            schedules = await super()._fetch_schedules(params)
            return schedules
        except Exception as e:
            self.logger.error("Error fetching schedules: {}".format(e))
            raise
    
    def __sort_and_clean(self):
        try:
            now = datetime.now().astimezone()
            
            processed_journeys = {
                trip_id: journey
                for trip_id, journey in self.journeys.items()
                if journey.stops['departure'] 
                and journey.stops['arrival'] 
                and journey.stops['departure'].stop_sequence < journey.stops['arrival'].stop_sequence
                #and journey.stops['departure'].get_time() is not None 
                and journey.stops['departure'].get_time() >= now
            }

            sorted_journeys = dict(
                sorted(
                    processed_journeys.items(),
                    key=lambda item: item[1].stops['departure'].get_time()
                )
            )

            self.journeys = dict(list(sorted_journeys.items())[:self.max_journeys] if self.max_journeys > 0 else sorted_journeys)
        
        except Exception as e:
            self.logger.error("Error sorting and cleaning journeys: {}".format(e))
            raise

    async def __fetch_trips(self):
        try:
            for trip_id, journey in self.journeys.items():
                trip: MBTATrip = await super()._fetch_trip(trip_id)
                journey.trip = trip
        except Exception as e:
            self.logger.error("Error fetching trips: {}".format(e))
            raise

    async def __fetch_routes(self):
        try:
            for journey in self.journeys.values():
                if journey.trip and journey.trip.route_id:
                    route: MBTARoute = await super()._fetch_route(journey.trip.route_id)
                    journey.route = route
        except Exception as e:
            self.logger.error("Error fetching routes: {}".format(e))
            raise
