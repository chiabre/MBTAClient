import aiohttp
import logging
from aiohttp import ClientConnectionError, ClientResponseError
from typing import Optional, Any
from mbta_route import MBTARoute
from mbta_stop import MBTAStop
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert

MBTA_DEFAULT_HOST = "api-v3.mbta.com"

ENDPOINTS = {
    'STOPS': 'stops',
    'ROUTES': 'routes',
    'PREDICTIONS': 'predictions',
    'SCHEDULES': 'schedules',
    'TRIPS': 'trips',
    'ALERTS': 'alerts'
}

class MBTAClient:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, session: aiohttp.ClientSession,  logger: logging.Logger, api_key: Optional[str] = None)-> None:
        self._session = session
        self._api_key = api_key
        self.logger: logging.Logger = logger
    
    async def get_route(self, id: str, params: Optional[dict[str, Any]] = None) -> MBTARoute:
        """Get a route by its ID."""
        route_data = await self._fetch_data(f'{ENDPOINTS["ROUTES"]}/{id}', params)
        return MBTARoute(route_data['data'])
    
    async def get_trip(self, id: str, params: Optional[dict[str, Any]] = None) -> MBTATrip:
        """Get a trip by its ID."""
        trip_data = await self._fetch_data(f'{ENDPOINTS["TRIPS"]}/{id}', params)
        return MBTATrip(trip_data['data'])
    
    async def get_stop(self, id: str, params: Optional[dict[str, Any]] = None) -> MBTAStop:
        """Get a stop by its ID."""
        stop_data = await self._fetch_data(f'{ENDPOINTS["STOPS"]}/{id}', params)
        return MBTAStop(stop_data['data'])
        
    async def list_routes(self, params: Optional[dict[str, Any]] = None) -> list[MBTARoute]:
        """list all routes."""
        route_data = await self._fetch_data(ENDPOINTS['ROUTES'], params)
        return [MBTARoute(item) for item in route_data['data']]
    
    async def list_trips(self, params: Optional[dict[str, Any]] = None) -> list[MBTARoute]:
        """list all trips."""
        route_data = await self._fetch_data(ENDPOINTS['TRIPS'], params)
        return [MBTATrip(item) for item in route_data['data']]

    async def list_stops(self, params: Optional[dict[str, Any]] = None) -> list[MBTAStop]:
        """list all stops."""
        stop_data = await self._fetch_data(ENDPOINTS['STOPS'], params)
        return [MBTAStop(item) for item in stop_data['data']]

    async def list_schedules(self, params: Optional[dict[str, Any]] = None) -> list[MBTASchedule]:
        """list all schedules."""
        schedule_data = await self._fetch_data(ENDPOINTS['SCHEDULES'], params)
        return [MBTASchedule(item) for item in schedule_data['data']]
    
    async def list_predictions(self, params: Optional[dict[str, Any]] = None) -> list[MBTAPrediction]:
        """list all predictions."""
        prediction_data = await self._fetch_data(ENDPOINTS['PREDICTIONS'], params)
        return [MBTAPrediction(item) for item in prediction_data['data']]

    async def list_alerts(self, params: Optional[dict[str, Any]] = None) -> list[MBTAAlert]:
        """list all predictions."""
        alert_data = await self._fetch_data(ENDPOINTS['ALERTS'], params)
        return [MBTAAlert(item) for item in alert_data['data']]
    
    async def _fetch_data(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Helper method to fetch data from the MBTA API."""
        try:
            response = await self.request("get", endpoint, params)
            data = await response.json() 
            if 'data' not in data:
                raise ValueError("Unexpected response format")
            return data
        except Exception as error:
            self.logger.error(f"Error fetching data: {error}")
            raise
        
    async def request(
        self, method: str, path: str, params: Optional[dict[str, Any]] = None) -> aiohttp.ClientResponse:
        """Make an HTTP request with Optional query parameters and JSON body."""
        
        if params is None:
            params = {}
        if self._api_key:
            params['api_key'] = self._api_key
        
        try:
            response: aiohttp.ClientResponse = await self._session.request(
                method,
                f'https://{MBTA_DEFAULT_HOST}/{path}',
                params=params
            )
                    
            response.raise_for_status()
            
            return response
            
        except ClientConnectionError as error:
            self.logger.error(f"Connection error: {error}")
            raise
        except ClientResponseError as error:
            self.logger.error(f"Client response error: {error.status} - {str(error)}")
            raise
        except Exception as error:
            self.logger.error(f"An unexpected error occurred: {error}")
            raise        



