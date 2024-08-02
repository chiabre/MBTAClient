from typing import List, Optional, Dict, Any
from mbta_auth import Auth
from mbta_route import MBTAroute
from mbta_stop import MBTAstop
from mbta_schedule import MBTAschedule
from mbta_prediction import MBTAprediction

ENDPOINT_STOPS = 'stops'
ENDPOINT_ROUTES = 'routes'
ENDPOINT_PREDICTIONS = 'predictions'
ENDPOINT_SCHEDULES = 'schedules'

class MBTA:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, auth: Auth, route_name: Optional[str] = None, departure_name: Optional[str] = None, arrival_name: Optional[str] = None) -> None:
        """Initialize the MBTA client with authentication and optional route details."""
        self.auth = auth
    
    async def get_route(self, id: str, payload: Optional[Dict[str, Any]] = None) -> MBTAroute:
        """Get a route by its ID."""
        route_data = await self._fetch_data(f'{ENDPOINT_ROUTES}/{id}', payload)
        return MBTAroute(route_data['data'])
    
    async def get_stop(self, id: str, payload: Optional[Dict[str, Any]] = None) -> MBTAstop:
        """Get a stop by its ID."""
        stop_data = await self._fetch_data(f'{ENDPOINT_STOPS}/{id}', payload)
        return MBTAstop(stop_data['data'])
    
    async def list_routes(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAroute]:
        """List all routes."""
        route_data = await self._fetch_data(ENDPOINT_ROUTES, payload)
        return [MBTAroute(item) for item in route_data['data']]

    async def list_stops(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAstop]:
        """List all stops."""
        stop_data = await self._fetch_data(ENDPOINT_STOPS, payload)
        return [MBTAstop(item) for item in stop_data['data']]

    async def list_schedules(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAschedule]:
        """List all schedules."""
        schedule_data = await self._fetch_data(ENDPOINT_SCHEDULES, payload)
        return [MBTAschedule(item) for item in schedule_data['data']]
    
    async def list_predictions(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAprediction]:
        """List all predictions."""
        prediction_data = await self._fetch_data(ENDPOINT_PREDICTIONS, payload)
        return [MBTAprediction(item) for item in prediction_data['data']]
    
    async def _fetch_data(self, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper method to fetch data from API."""
        response = await self.auth.request("get", endpoint, params=payload)
        return await response.json()
