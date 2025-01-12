import aiohttp
import asyncio
import logging
from typing import Optional, Any, Dict, List, Type

from .route import MBTARoute
from .stop import MBTAStop
from .schedule import MBTASchedule
from .prediction import MBTAPrediction
from .trip import MBTATrip
from .alert import MBTAAlert
from .cache_manager import CacheManager, memoize_async

MBTA_DEFAULT_HOST = "api-v3.mbta.com"

ENDPOINTS = {
    'STOPS': 'stops',
    'ROUTES': 'routes',
    'PREDICTIONS': 'predictions',
    'SCHEDULES': 'schedules',
    'TRIPS': 'trips',
    'ALERTS': 'alerts',
}

MAX_CONCURRENT_REQUESTS = 1
REQUEST_TIMEOUT = 5

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
                 cache_manager: Optional[CacheManager] = None, 
                 logger: Optional[logging.Logger] = None, 
                 max_concurrent_requests: Optional[int] = MAX_CONCURRENT_REQUESTS,
                 timeout: Optional[int] = REQUEST_TIMEOUT):
        self._session = session
        self._api_key = api_key
        self._max_concurrent_requests = max_concurrent_requests
        self._timeout = timeout
        self._cache_manager = cache_manager or CacheManager()

        if self._session:
            SessionManager.configure(self._session, logger=logger, max_concurrent_requests=self._max_concurrent_requests, timeout=self._timeout)
        else:
            SessionManager.configure(logger=logger, max_concurrent_requests=self._max_concurrent_requests, timeout=self._timeout)

        self._logger = logger or logging.getLogger(__name__)
        self._logger.debug("MBTAClient initialized.")

    async def __aenter__(self):
        """Enter the context and return the client."""
        if not self._session:
            self._session = await SessionManager.get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context."""
        await SessionManager.cleanup()

    async def fetch_list(
        self, endpoint: str, params: Optional[Dict[str, Any]], response_model_class: Type
    ) -> List[Any]:
        """Fetch a list of objects from the MBTA API."""
        data = await self._fetch_data(endpoint, params)
        return [response_model_class(item) for item in data["data"]]

    async def _fetch_data(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Helper method to fetch data from the MBTA API."""
        self._logger.debug(f"Fetching {path}")
        try:
            data = await self.request("GET", path, params)
            if "data" not in data:
                self._logger.warning(f"Response missing 'data': {data}")
                raise MBTAClientError("Invalid response from API.")
            return data
        except MBTAClientError as error:
            self._logger.error(f"MBTAClientError: {error}")
            raise
        except Exception as error:
            self._logger.error(f"Unexpected error: {error}")
            raise

    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> aiohttp.ClientResponse:
        """Make an HTTP request with optional query parameters."""
        params = params or {}
        headers = {}

        if self._api_key:
            params["api_key"] = self._api_key

        url = f"https://{MBTA_DEFAULT_HOST}/{path}"

        last_modified = self._cache_manager.get_last_modified(path, params)
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        headers["Accept-Encoding"] = "gzip"

        try:
            async with SessionManager._semaphore:
                self._logger.debug(f"{method} {url} {headers} {params}")
                response: aiohttp.ClientResponse = await self._session.request(
                    method, url, 
                    params=params, 
                    headers=headers
                )

                if response.status == 403:
                    self._logger.error(f"Authentication error: Invalid API key (HTTP 403).")
                    raise MBTAAuthenticationError("Invalid API key or credentials (HTTP 403).")
                
                if response.status == 429:
                    self._logger.error(f"Rate limit exceeded (HTTP 429).")
                    raise MBTATooManyRequestsError("Rate limit exceeded (HTTP 429). Please wait and try again.")

                if response.status == 304:
                    cached_data = self._cache_manager.get_cached_server_data(path, params)
                    if cached_data is not None:
                        return cached_data
                    else:
                        raise MBTAClientError(f"Cache empty for 304 response: {url}")

                response.raise_for_status()

                data = await response.json()
                last_modified = response.headers.get("Last-Modified")
                if last_modified:
                    self._cache_manager.update_server_cache(path=path, params=params, data=data, last_modified=last_modified)
                return data

        except Exception as error:
            self._logger.error(f"Error during request to {url}: {error}")
            raise MBTAClientError("Unexpected error during request.") from error

    @memoize_async()
    async def get_route(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTARoute:
        """Get a route by its ID."""
        data = await self._fetch_data(f"{ENDPOINTS['ROUTES']}/{id}", params)
        return MBTARoute(data["data"])
    
    @memoize_async()
    async def get_trip(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTATrip:
        """Get a trip by its ID."""
        data = await self._fetch_data(f"{ENDPOINTS['TRIPS']}/{id}", params)
        return MBTATrip(data["data"])

    @memoize_async()
    async def get_stop(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTAStop:
        """Get a stop by its ID."""
        data = await self._fetch_data(f'{ENDPOINTS["STOPS"]}/{id}', params)
        return MBTAStop(data['data'])
    
    @memoize_async()
    async def list_routes(self, params: Optional[Dict[str, Any]] = None) -> List[MBTARoute]:
        """List all routes."""
        return await self.fetch_list(ENDPOINTS["ROUTES"], params, MBTARoute)

    @memoize_async()
    async def list_trips(self, params: Optional[Dict[str, Any]] = None) -> List[MBTATrip]:
        """List all trips."""
        return await self.fetch_list(ENDPOINTS["TRIPS"], params, MBTATrip)
    
    @memoize_async()
    async def list_stops(self, params: Optional[Dict[str, Any]] = None) -> List[MBTAStop]:
        """List all stops."""
        data = await self._fetch_data(ENDPOINTS['STOPS'], params)
        return [MBTAStop(item) for item in data["data"]]

    @memoize_async()
    async def list_schedules(self, params: Optional[Dict[str, Any]] = None) -> List[MBTASchedule]:
        """List all schedules."""
        data = await self._fetch_data(ENDPOINTS['SCHEDULES'], params)
        return [MBTASchedule(item) for item in data["data"]]

    async def list_predictions(self, params: Optional[Dict[str, Any]] = None) -> List[MBTAPrediction]:
        """List all predictions."""
        data = await self._fetch_data(ENDPOINTS['PREDICTIONS'], params)
        return [MBTAPrediction(item) for item in data["data"]]

    async def list_alerts(self, params: Optional[Dict[str, Any]] = None) -> List[MBTAAlert]:
        """List all alerts."""
        data = await self._fetch_data(ENDPOINTS['ALERTS'], params)
        return [MBTAAlert(item) for item in data["data"]]

class SessionManager:
    """Singleton class to manage a shared aiohttp.ClientSession."""
    
    _session: Optional[aiohttp.ClientSession] = None
    _semaphore: Optional[asyncio.Semaphore] = None
    _logger: Optional[logging.Logger] = None
    _max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS
    _timeout: int = REQUEST_TIMEOUT

    @classmethod
    def configure(cls, 
                  session: Optional[aiohttp.ClientSession] = None, 
                  logger: logging.Logger = None,
                  max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS, 
                  timeout: int = REQUEST_TIMEOUT):
        """Configure the SessionManager."""
        cls._logger = logger or logging.getLogger(__name__)
        cls._max_concurrent_requests = max_concurrent_requests
        cls._semaphore = asyncio.Semaphore(max_concurrent_requests)
        cls._timeout = timeout

        if session:
            cls._session = session

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get the shared aiohttp.ClientSession instance, creating it if necessary."""
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cls._timeout))
        return cls._session

    @classmethod
    async def close_session(cls):
        """Close the shared aiohttp.ClientSession."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

    @classmethod
    async def cleanup(cls):
        """Clean up resources when shutting down."""
        await cls.close_session()
        cls._semaphore = None
