import aiohttp
import logging
from typing import Optional, Any, Dict, Tuple

from ..models.mbta_vehicle import MBTAVehicle
from ..models.mbta_route import MBTARoute
from ..models.mbta_stop import MBTAStop
from ..models.mbta_schedule import MBTASchedule
from ..models.mbta_prediction import MBTAPrediction
from ..models.mbta_trip import MBTATrip
from ..models.mbta_alert import MBTAAlert
from .mbta_cache_manager import MBTACacheManager, CacheEvent
from .mbta_session_manager import MBTASessionManager

MBTA_DEFAULT_HOST = "api-v3.mbta.com"

ENDPOINTS = {
    'STOPS': 'stops',
    'ROUTES': 'routes',
    'PREDICTIONS': 'predictions',
    'SCHEDULES': 'schedules',
    'TRIPS': 'trips',
    'ALERTS': 'alerts',
    'VEHICLES': 'vehicles', 
}

class MBTAAuthenticationError(Exception):
    """Custom exception for MBTA authentication errors."""

class MBTATooManyRequestsError(Exception):
    """Custom exception for MBTA TooManyRequests errors."""

class MBTAClientError(Exception):
    """Custom exception class for MBTA API errors."""

class MBTAClient:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, 
                 api_key: Optional[str] = None,
                 session: Optional[aiohttp.ClientSession] = None, 
                 cache_manager: Optional[MBTACacheManager] = None, 
                 logger: Optional[logging.Logger] = None, 
                 max_concurrent_requests: Optional[int] = None,
                 timeout: Optional[int] = None):
        self._api_key = api_key

        self._logger = logger or logging.getLogger(__name__)
        
        MBTASessionManager.configure(
            session=session,
            logger=logger,
            max_concurrent_requests=max_concurrent_requests,
            timeout=timeout,
        )
        
        if cache_manager is None:
            self._cache_manager = MBTACacheManager()
            self._own_cache = True
        else:
            self._cache_manager = cache_manager
            self._own_cache = False
                    
        self._logger.debug("MBTAClient initialized")

    def __repr__(self) -> str:
        return (f"MBTAClient(own_cache={self._own_cache})"
        )
        
    async def __aenter__(self):
        """Enter the context and prepare the session."""
        await MBTASessionManager.get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context and clean up."""
        if self._own_cache == True:
            self._cache_manager.cleanup()
        await MBTASessionManager.cleanup()

    async def _fetch_data(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Helper method to fetch data from the MBTA API."""
        try:
            data, timestamp = await self.request("GET", path, params)
            if "data" not in data:
                self._logger.warning(f"Response missing 'data': {data}")
                raise MBTAClientError("Invalid response from API.")
            return data, timestamp
        except MBTAClientError as error:
            self._logger.error(f"MBTAClientError: {error}")
            raise
        except Exception as error:
            self._logger.error(f"Unexpected error: {error}")
            raise

    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Any,float]:
        """Make an HTTP request with optional query parameters."""
        session = await MBTASessionManager.get_session()
        params = params or {}
        headers = {}

        if self._api_key:
            params["api_key"] = self._api_key

        url = f"https://{MBTA_DEFAULT_HOST}/{path}"
        
        cached_data, timestamp, last_modified = self._cache_manager.get_cached_data(path, params)
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        headers["Accept-Encoding"] = "gzip"

        try:
            async with MBTASessionManager._semaphore:
                
                self._logger.debug(f"{method} {url} {headers} {params}")                
                response: aiohttp.ClientResponse = await session.request(
                    method, url, 
                    params=params, 
                    headers=headers
                )

                if response.status == 403:
                    self._logger.error("Authentication error: Invalid API key (HTTP 403).")
                    raise MBTAAuthenticationError("Invalid API key or credentials (HTTP 403).")
                
                if response.status == 429:
                    self._logger.error("Rate limit exceeded (HTTP 429).")
                    raise MBTATooManyRequestsError("Rate limit exceeded (HTTP 429). Please uscheck your API key.")

                if response.status == 304:
                    if cached_data is not None:
                        if  self._cache_manager.stats:
                            self._cache_manager.cache_stats.increase_counter(CacheEvent.HIT)
                        return cached_data, timestamp
                    else:
                        raise MBTAClientError(f"Cache empty for 304 response: {url}")

                response.raise_for_status()
                
                data = await response.json()
                last_modified = response.headers.get("Last-Modified")
                if last_modified:
                    timestamp = self._cache_manager.update_cache(path=path, params=params, data=data, last_modified=last_modified)
                if  self._cache_manager.stats:
                    self._cache_manager.cache_stats.increase_counter(CacheEvent.MISS)
                return data, timestamp

        except TimeoutError as error:
            self._logger.error(f"Timeout during request to {url}: {error}")
            raise TimeoutError
        
        except Exception as error:
            self._logger.error(f"Error during request to {url}: {error}")
            raise MBTAClientError("Unexpected error during request.") from error

    async def fetch_route(self, id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[MBTARoute, float]:
        """Fetch a MBTARoute by its ID."""
        self._logger.debug(f"Fetching MBTA route with ID: {id}")
        data, timestamp = await self._fetch_data(f"{ENDPOINTS['ROUTES']}/{id}", params)
        return MBTARoute(data["data"]), timestamp

    async def fetch_trip(self, id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[MBTATrip, float]:
        """Fetch a MBTATrip by its ID."""
        self._logger.debug(f"Fetching MBTA trip with ID: {id}")
        data, timestamp = await self._fetch_data(f"{ENDPOINTS['TRIPS']}/{id}", params)
        return MBTATrip(data["data"]), timestamp
    
    async def fetch_stop(self, id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[MBTAStop, float]:
        """Fetch a MBTAStop by its ID."""
        self._logger.debug(f"Fetching MBTA stop with ID: {id}")
        data, timestamp = await self._fetch_data(f'{ENDPOINTS["STOPS"]}/{id}', params)
        return MBTAStop(data['data']), timestamp
    
    async def fetch_vehicle(self, id: str, params: Optional[Dict[str, Any]] = None) -> Tuple[MBTAVehicle, float]:
        """Fetch a MBTAVehicle by its ID."""
        self._logger.debug("Fetching MBTA vehicle with ID: {id}")
        data, timestamp = await self._fetch_data(ENDPOINTS['VEHICLES']/{id}, params)
        return MBTAVehicle(data['data']), timestamp

    async def fetch_routes(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTARoute], float]:
        """Fetch a list of MBTARoute."""
        self._logger.debug("Fetching all MBTA routes")
        data, timestamp = await self._fetch_data(ENDPOINTS["ROUTES"], params)
        return [MBTARoute(item) for item in data["data"]], timestamp

    async def fetch_trips(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTATrip], float]:
        """Fetch a list of MBTATrip."""
        self._logger.debug("Fetching MBTA trips")
        data, timestamp = await self._fetch_data(ENDPOINTS["TRIPS"], params)
        return [MBTATrip(item) for item in data["data"]], timestamp

    async def fetch_stops(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTAStop], float]:
        """Fetch a list of MBTAStops."""
        self._logger.debug("Fetching MBTA stops")
        data, timestamp = await self._fetch_data(ENDPOINTS['STOPS'], params)
        return [MBTAStop(item) for item in data["data"]], timestamp

    async def fetch_schedules(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTASchedule], float]:
        """Fetch a list of MBTASchedules."""
        self._logger.debug("Fetching MBTA schedules")
        data, timestamp = await self._fetch_data(ENDPOINTS['SCHEDULES'], params)
        return [MBTASchedule(item) for item in data["data"]], timestamp

    async def fetch_vehicles(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTAVehicle], float]:
        """Fetch a list of MBTAAlerts."""
        self._logger.debug("Fetching MBTA vehicles")
        data, timestamp = await self._fetch_data(ENDPOINTS['VEHICLES'], params)
        return [MBTAVehicle(item) for item in data["data"]], timestamp

    async def fetch_predictions(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTAPrediction], float]:
        """Fetch a list of MBTAPredictions."""
        self._logger.debug("Fetching MBTA predictions")
        data, timestamp = await self._fetch_data(ENDPOINTS['PREDICTIONS'], params)
        return [MBTAPrediction(item) for item in data["data"]], timestamp

    async def fetch_alerts(self, params: Optional[Dict[str, Any]] = None) -> Tuple[list[MBTAAlert], float]:
        """Fetch a list of MBTAAlerts."""
        self._logger.debug("Fetching MBTA alerts")
        data, timestamp = await self._fetch_data(ENDPOINTS['ALERTS'], params)
        return [MBTAAlert(item) for item in data["data"]], timestamp

