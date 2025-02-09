from typing import Optional, Any, Dict, Tuple
import logging
import aiohttp

from ..models.mbta_vehicle import MBTAVehicle
from ..models.mbta_route import MBTARoute
from ..models.mbta_stop import MBTAStop
from ..models.mbta_schedule import MBTASchedule
from ..models.mbta_prediction import MBTAPrediction
from ..models.mbta_trip import MBTATrip
from ..models.mbta_alert import MBTAAlert
from .mbta_cache_manager import MBTACacheManager, CacheEvent
from .mbta_session_manager import MBTASessionManager, MBTASessionManagerContext

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
        # This will hold our session manager context instance.
        self._session_context: Optional[MBTASessionManagerContext] = None

    def __repr__(self) -> str:
        return f"MBTAClient(own_cache={self._own_cache})"
    
    async def __aenter__(self):
        """Enter the context using MBTASessionManagerContext."""
        self._session_context = MBTASessionManagerContext()
        await self._session_context.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context and clean up."""
        if self._own_cache:
            # If your cache manager cleanup is async, you might await it.
            self._cache_manager.cleanup()
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc, tb)
        self._session_context = None

    async def _fetch_data(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], float]:
        """Helper method to fetch data from the MBTA API."""
        try:
            data, timestamp = await self.request("GET", path, params)
            if "data" not in data:
                self._logger.warning("Response missing 'data' in response: %s", data)
                raise MBTAClientError("Invalid response from API: 'data' key missing.")
            return data, timestamp
        except MBTAClientError as error:
            self._logger.error(
                "MBTAClientError: %s (HTTP %s - %s) | URL: %s", 
                error.message, 
                error.status_code, 
                error.reason, 
                error.url
            )
            raise
        except Exception as error:
            self._logger.error("Unexpected error: %s", error, exc_info=True)
            raise

    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Any, float]:
        """Make an HTTP request with optional query parameters."""
        params = params or {}
        headers = {}

        if self._api_key:
            params["api_key"] = self._api_key

        url = f"https://{MBTA_DEFAULT_HOST}/{path}"
        
        cached_data, timestamp, last_modified = self._cache_manager.get_cached_data(path, params)
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        headers["Accept-Encoding"] = "gzip"

        # Obfuscate the API key in logs if debug is enabled.
        if self._logger.isEnabledFor(logging.DEBUG):
            obfuscated_headers = headers.copy()
            if "api_key" in obfuscated_headers:
                obfuscated_headers["api_key"] = "***"
        else:
            obfuscated_headers = headers

        try:
            self._logger.debug("Request: %s %s %s %s", method, url, obfuscated_headers, params)
            response: aiohttp.ClientResponse = await MBTASessionManager.request_with_retries(
                method, url,
                params=params,
                headers=headers
            )

            self._logger.debug("Response for %s: %s", url, response.status)

            if response.status == 403:
                self._logger.error("Authentication error: Invalid API key (HTTP 403).")
                raise MBTAAuthenticationError("Invalid API key or credentials (HTTP 403).")
            if response.status == 429:
                self._logger.error("Rate limit exceeded (HTTP 429).")
                raise MBTATooManyRequestsError("Rate limit exceeded (HTTP 429). Please check your API key.")
            if response.status == 304:
                if cached_data is not None:
                    if self._cache_manager.cache_stats:
                        self._cache_manager.cache_stats.increase_counter(CacheEvent.HIT)
                    return cached_data, timestamp
                else:
                    raise MBTAClientError(f"Cache empty despite 304 response: {url}")

            response.raise_for_status()
            data = await response.json()
            last_modified = response.headers.get("Last-Modified")
            if last_modified:
                timestamp = self._cache_manager.update_cache(
                    path=path, params=params, data=data, last_modified=last_modified
                )
            if self._cache_manager.cache_stats:
                self._cache_manager.cache_stats.increase_counter(CacheEvent.MISS)
            return data, timestamp

        except MBTAAuthenticationError as error:
            self._logger.error("Authentication failed: %s", error)
            raise
        except MBTATooManyRequestsError as error:
            self._logger.error("Too many requests: %s", error)
            raise
        except TimeoutError as error:
            self._logger.error("Timeout during request to %s: %s", url, error)
            raise
        except aiohttp.ClientResponseError as error:
            request_url = str(error.request_info.url) if error.request_info else "Unknown URL"
            self._logger.error("Client response error (HTTP %s) for %s: %s", error.status, request_url, error.message)
            raise MBTAClientError("Client response error.", status_code=error.status, reason=error.message, url=request_url) from error
        except Exception as error:
            self._logger.error("Unexpected error during request to %s: %s", url or "Unknown URL", error)
            raise MBTAClientError("Unexpected error during request.", url=url or "Unknown URL") from error

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

class MBTAAuthenticationError(Exception):
    """Custom exception for MBTA authentication errors."""

class MBTATooManyRequestsError(Exception):
    """Custom exception for MBTA TooManyRequests errors."""

class MBTAClientError(Exception):
    """Custom exception for MBTA client errors."""
    
    def __init__(self, message, status_code=None, reason=None, url=None):
        self.status_code = status_code
        self.reason = reason
        self.url = url

        details = []
        if status_code:
            details.append(f"HTTP {status_code} - {reason or 'Unknown reason'}")
        if url:
            details.append(f"URL: {url}")

        # Save the full message in the `message` attribute
        self.message = f"{message} ({', '.join(details)})" if details else message
        super().__init__(self.message)  # Pass the full message to the base Exception class
