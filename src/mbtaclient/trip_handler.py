import aiohttp
import logging

from datetime import datetime, timedelta
from .base_handler import BaseHandler, MBTATripError
from .journey import Journey
from .route import MBTARoute
from .trip import MBTATrip
from .schedule import MBTASchedule

class TripHandler(BaseHandler):
    """Handler for managing a specific trip."""

    def __init__(self, depart_from_name: str, arrive_at_name: str, trip_name: str, api_key:str = None, session: aiohttp.ClientSession = None, logger: logging.Logger = None):
        super().__init__(depart_from_name=depart_from_name, arrive_at_name=arrive_at_name, api_key=api_key, session=session, logger=logger) 
        self.trip_name = trip_name
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
            
    async def async_init(self):
        self.logger.debug("Initializing TripHandler")
        try:
            await super()._async_init()

            self.logger.debug("Retrieving MBTA trip for {}".format(self.trip_name))
            params = {
                'filter[revenue]': 'REVENUE',
                'filter[name]': self.trip_name
            }
            
            # Fetch trips and validate the response
            trips: list[MBTATrip] = await super()._fetch_trips(params)
            if not trips or not isinstance(trips, list) or not trips[0]:
                self.logger.error("Error retrieving MBTA trip {}: Invalid trip name or response".format(self.trip_name))
                raise MBTATripError("Invalid trip name")

            # Create a new journey and assign the first trip
            journey = Journey()
            journey.trip = trips[0]
            
            self.logger.debug("Retrieving MBTA route for trip {}".format(self.trip_name))
            route: MBTARoute = await super()._fetch_route(journey.trip.route_id)
            if route is None:
                self.logger.error("Error retrieving MBTA route for trip {}".format(self.trip_name))
                raise MBTATripError("Invalid route")

            journey.route = route
            self.journeys[trips[0].id] = journey
            self.logger.info("Trip {} initialized successfully with route {}".format(self.trip_name, journey.route.id))
            
        except Exception as e:
            self.logger.error("Error during TripHandler initialization: {}".format(e))
    
    async def update(self) -> list[Journey]:
        now = datetime.now().astimezone()
        self.logger.debug("Updating trips for {}".format(self.trip_name))
        
        try:
            for i in range(7):
                params = {}
                date_to_try = (now + timedelta(days=i)).strftime('%Y-%m-%d')
                params['filter[date]'] = date_to_try
                if i == 0:
                    params['filter[min_time]'] = now.strftime('%H:%M')
                
                self.logger.debug("Fetching schedules for {} for trip {}".format(date_to_try, self.trip_name))
                schedules = await self.__fetch_schedules(params)
                await super()._process_schedules(schedules)
                
                # Check for valid schedules
                if next(iter(self.journeys.values())).get_stop_time_to('arrival') is not None:
                    self.logger.info("Valid schedule found for trip {} on {}".format(self.trip_name, date_to_try))
                    break

                # Log an error if no valid schedules after the final attempt
                if i == 6:
                    self.logger.error("Error retrieving scheduling for {} and {} on trip {}".format(self.depart_from['name'], self.arrive_at['name'], self.trip_name))
                    raise MBTATripError("Invalid stops for the trip")
                
        except MBTATripError as e:
            self.logger.error("{}".format(e))
        
        # Fetch predictions and alerts
        try:
            self.logger.debug("Fetching predictions for trip {}".format(self.trip_name))
            predictions = await self.__fetch_predictions()
            await super()._process_predictions(predictions)
        
            self.logger.debug("Fetching alerts for trip {}".format(self.trip_name))
            alerts = await self.__fetch_alerts()
            super()._process_alerts(alerts)  
        
        except Exception as e:
            self.logger.error("Error during predictions/alerts fetching for trip {}: {}".format(self.trip_name, e))
        
        return list(self.journeys.values())
    
    
    async def __fetch_schedules(self, params: dict) -> list[MBTASchedule]:
        self.logger.debug("Fetching schedules with params: {}".format(params))
        journey = next(iter(self.journeys.values()))
        trip_id = journey.trip.id

        base_params = {
            'filter[trip]': trip_id,
        }
        if params is not None:
            base_params.update(params)
        
        try:
            schedules = await super()._fetch_schedules(base_params)
            self.logger.debug("Fetched {} schedules for trip {}".format(len(schedules), trip_id))
            return schedules
        except Exception as e:
            self.logger.error("Error fetching schedules for trip {}: {}".format(trip_id, e))
  
