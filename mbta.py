from typing import List, Optional, Dict, Any
import logging
from mbta_auth import MBTAAuth
from mbta_route import MBTARoute
from mbta_stop import MBTAStop
from mbta_schedule import MBTASchedule
from mbta_prediction import MBTAPrediction
from mbta_trip import MBTATrip
from mbta_alert import MBTAAlert

ENDPOINTS = {
    'STOPS': 'stops',
    'ROUTES': 'routes',
    'PREDICTIONS': 'predictions',
    'SCHEDULES': 'schedules',
    'TRIPS': 'trips',
    'ALERTS': 'alerts'
}

class MBTA:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, auth: MBTAAuth, route_name: Optional[str] = None, departure_name: Optional[str] = None, arrival_name: Optional[str] = None) -> None:
        """Initialize the MBTA client with authentication and optional route details."""
        self.auth = auth
    
    async def get_route(self, id: str, payload: Optional[Dict[str, Any]] = None) -> MBTARoute:
        """Get a route by its ID."""
        route_data = await self._fetch_data(f'{ENDPOINTS["ROUTES"]}/{id}', payload)
        return MBTARoute(route_data['data'])
    
    async def get_stop(self, id: str, payload: Optional[Dict[str, Any]] = None) -> MBTAStop:
        """Get a stop by its ID."""
        stop_data = await self._fetch_data(f'{ENDPOINTS["STOPS"]}/{id}', payload)
        return MBTAStop(stop_data['data'])
    
    async def get_trip(self, id: str, payload: Optional[Dict[str, Any]] = None) -> MBTATrip:
        """Get a stop by its ID."""
        trip_data = await self._fetch_data(f'{ENDPOINTS["TRIPS"]}/{id}', payload)
        return MBTATrip(trip_data['data'])
    
    async def list_routes(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTARoute]:
        """List all routes."""
        route_data = await self._fetch_data(ENDPOINTS['ROUTES'], payload)
        return [MBTARoute(item) for item in route_data['data']]

    async def list_stops(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAStop]:
        """List all stops."""
        stop_data = await self._fetch_data(ENDPOINTS['STOPS'], payload)
        return [MBTAStop(item) for item in stop_data['data']]

    async def list_schedules(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTASchedule]:
        """List all schedules."""
        schedule_data = await self._fetch_data(ENDPOINTS['SCHEDULES'], payload)
        return [MBTASchedule(item) for item in schedule_data['data']]
    
    async def list_predictions(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAPrediction]:
        """List all predictions."""
        prediction_data = await self._fetch_data(ENDPOINTS['PREDICTIONS'], payload)
        return [MBTAPrediction(item) for item in prediction_data['data']]

    async def list_alerts(self, payload: Optional[Dict[str, Any]] = None) -> List[MBTAAlert]:
        """List all predictions."""
        alert_data = await self._fetch_data(ENDPOINTS['ALERTS'], payload)
        return [MBTAAlert(item) for item in alert_data['data']]
    
    async def _fetch_data(self, endpoint: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Helper method to fetch data from API."""
        response = await self.auth.request("get", endpoint, params=payload)
        return await response.json()

