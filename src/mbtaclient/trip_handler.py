import aiohttp
import logging

from datetime import datetime, timedelta
from .base_handler import BaseHandler, MBTATripError
from .journey import Journey
from .mbta_route import MBTARoute
from .mbta_trip import MBTATrip
from .mbta_schedule import MBTASchedule
from .mbta_prediction import MBTAPrediction

class TripHandler(BaseHandler):
    """Handler for managing a specific trip."""

    def __init__(self, depart_from_name: str, arrive_at_name: str, trip_name: str, api_key:str = None, session: aiohttp.ClientSession = None, logger: logging.Logger = None):
        super().__init__( depart_from_name=depart_from_name, arrive_at_name=arrive_at_name, api_key=api_key, session=session, logger=logger) 
        self.trip_name = trip_name
        
            
    async def async_init(self):
        self.logger.debug("Initializing TripHandler")
        try:
            await super()._async_init()

            self.logger.debug("Retriving MBTA trip")
            params = {
                'filter[revenue]': 'REVENUE',
                'filter[name]': self.trip_name
            }
            
            # Fetch trips and validate the response
            trips: list[MBTATrip] = await super()._fetch_trips(params)
            if not trips or not isinstance(trips, list) or not trips[0]:
                self.logger.error(f"Error retriving MBTA trip {self.trip_name}")
                raise MBTATripError("Invalid trip name")                

            
            # Create a new journey and assign the first trip
            journey = Journey()
            journey.trip = trips[0]
            
            # Fetch route and validate the response
            self.logger.debug("Retriving MBTA route")
            route: MBTARoute = await super()._fetch_route(journey.trip.route_id)

            journey.route = route
            self.journeys[trips[0].id] = journey

        except Exception as e:
            self.logger.error(f"Error during TripHandler initialization: {e}")
    
    async def update(self) -> list[Journey]:
        now = datetime.now().astimezone()

        try:
            for i in range(7):
                params = {}
                # Calculate the date for each attempt (i days after today)
                date_to_try = (now + timedelta(days=i)).strftime('%Y-%m-%d')
                params['filter[date]'] = date_to_try
                if i == 0:
                    params['filter[min_time]'] = now.strftime('%H:%M')
                
                # Attempt to get schedules for up to the next 7 days
                schedules = await self.__fetch_schedules(params)
                await super()._process_schedules(schedules)
                if next(iter(self.journeys.values())).get_stop_time_to('arrival') is not None:
                    break
                
                # If it's the last attempt and no valid schedules were found, log an error and raise an exception
                if i == 6:
                    self.logger.error(
                        f"Error retrieving scheduling for {self.depart_from['name']} and {self.arrive_at['name']} on trip {self.trip_name}"
                    )
                    raise MBTATripError("Invalid stops for the trip")
                
        except MBTATripError as e:
            # Handle the error here without re-raising it
            self.logger.error(f"{e}")
            # Continue with other operations despite the failure
                   
        predictions = await self.__fetch_predictions()
        await super()._process_predictions(predictions)
        
        alerts = await self.__fetch_alerts()
        super()._process_alerts(alerts)  
        return  list(self.journeys.values())
    
    
    async def __fetch_schedules(self, params: dict) -> list[MBTASchedule]:
        journey = next(iter(self.journeys.values()))
        trip_id = journey.trip.id
      

        base_params = {
            'filter[trip]': trip_id,
        }
        if params is not None:
            base_params.update(params)
 
        schedules = await super()._fetch_schedules(base_params)
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
    
    
