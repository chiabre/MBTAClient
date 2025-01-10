import aiohttp
import asyncio
import logging
import time
from aiohttp import ClientConnectionError, ClientResponseError
from typing import Optional, Any, Dict, List, Type

from .route import MBTARoute
from .stop import MBTAStop
from .schedule import MBTASchedule
from .prediction import MBTAPrediction
from .trip import MBTATrip
from .alert import MBTAAlert

MBTA_DEFAULT_HOST = "api-v3.mbta.com"

ENDPOINTS = {
    'STOPS': 'stops',
    'ROUTES': 'routes',
    'PREDICTIONS': 'predictions',
    'SCHEDULES': 'schedules',
    'TRIPS': 'trips',
    'ALERTS': 'alerts',
}

MAX_CONCURRENT_REQUESTS = 10

class MBTAAuthenticationError(Exception):
    """Custom exception for MBTA authentication errors."""

class MBTAClientError(Exception):
    """Custom exception class for MBTA API errors."""

class MBTAClient:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, session: aiohttp.ClientSession = None, logger: logging.Logger = None, api_key: Optional[str] = None, max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS):
        self._session = session
        self._api_key: Optional[str] = api_key
        self._max_concurrent_requests = max_concurrent_requests

        if self._session:
            # If an external session is provided, pass it to SessionManager
            SessionManager.configure(self._max_concurrent_requests, self._session, logger=logger)
        else:
            # If no session is provided, the SessionManager will manage it
            SessionManager.configure(self._max_concurrent_requests, logger=logger)
            
        self._logger: logging.Logger = logger or logging.getLogger(__name__)

    async def __aenter__(self):
        """Enter the context and return the client."""
        if not self._session:
            # If session is not passed, get it from SessionManager
            self._session = await SessionManager.get_session()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context."""
        await SessionManager.close_session()
        SessionManager.cleanup()

    # Generic fetch method for list operations
    async def fetch_list(
        self, endpoint: str, params: Optional[Dict[str, Any]], obj_class: Type
    ) -> List[Any]:
        """Fetch a list of objects from the MBTA API."""
        self._logger.debug(f"Fetching list from endpoint: {endpoint} with params: {params}")
        data = await self._fetch_data(endpoint, params)
        # Generalize by ensuring each object is created dynamically
        return [obj_class(item) for item in data["data"]]

    # Fetch data helper with retries
    async def _fetch_data(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Helper method to fetch data from the MBTA API."""
        self._logger.debug(f"Fetching data from https://{MBTA_DEFAULT_HOST}/{path} with params: {params}")
        try:
            response = await self.request("GET", path, params)
            data = await response.json()
            if "data" not in data:
                self._logger.error(f"Response missing 'data': {data}")
                raise MBTAClientError(f"Invalid response from API: {data}")
            return data
        except MBTAClientError as error:
            self._logger.error(f"MBTAClientError occurred: {error}")
            raise
        except Exception as error:
            self._logger.error(f"Unexpected error while fetching data: {error}")
            raise

    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> aiohttp.ClientResponse:
        """
        Make an HTTP request with optional query parameters and JSON body.
        
        Adds retry logic and configurable timeouts.
        
        Raises:
            MBTAAuthenticationError: For 403 Forbidden errors (invalid API key).
            MBTAClientError: For other HTTP or unexpected errors.
        """
        params = params or {}
        if self._api_key:
            params["api_key"] = self._api_key

        url = f"https://{MBTA_DEFAULT_HOST}/{path}"
        self._logger.debug(f"Making {method} request to {url} with params: {params}")

        retries = 3
        timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout

        for attempt in range(retries):
            try:
                async with SessionManager._semaphore:
                    response: aiohttp.ClientResponse = await self._session.request(method, url, params=params, timeout=timeout)
                    self._logger.debug(f"Received response {response.status} for {url}")
                    response.raise_for_status()  # Raise HTTP errors
                    return response

            except (ClientResponseError, ClientConnectionError) as error:
                self._logger.error(f"Error on attempt {attempt + 1}/{retries}: {error}")
                if attempt == retries - 1:
                    self._logger.error(f"Final attempt failed: {error}")
                    raise MBTAClientError(f"Request failed: {error}") from error
                await asyncio.sleep(2)  # Wait before retrying

            except Exception as error:
                self._logger.error(f"Unexpected error during {method} request to {url}: {error}", exc_info=True)
                raise MBTAClientError(f"Unexpected error: {error}") from error

    # Specific API methods
    async def get_route(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTARoute:
        """Get a route by its ID."""
        data = await self._fetch_data(f"{ENDPOINTS['ROUTES']}/{id}", params)
        return MBTARoute(data["data"])

    async def get_trip(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTATrip:
        """Get a trip by its ID."""
        data = await self._fetch_data(f"{ENDPOINTS['TRIPS']}/{id}", params)
        return MBTATrip(data["data"])

    async def get_stop(self, id: str, params: Optional[Dict[str, Any]] = None) -> MBTAStop:
        """Get a stop by its ID."""
        data = await self._fetch_data(f'{ENDPOINTS["STOPS"]}/{id}', params)
        return MBTAStop(data['data'])

    async def list_routes(self, params: Optional[Dict[str, Any]] = None) -> List[MBTARoute]:
        """List all routes."""
        return await self.fetch_list(ENDPOINTS["ROUTES"], params, MBTARoute)

    async def list_trips(self, params: Optional[Dict[str, Any]] = None) -> List[MBTATrip]:
        """List all trips."""
        return await self.fetch_list(ENDPOINTS["TRIPS"], params, MBTATrip)

    async def list_stops(self, params: Optional[Dict[str, Any]] = None) -> List[MBTAStop]:
        """List all stops."""
        data = await self._fetch_data(ENDPOINTS['STOPS'], params)
        return [MBTAStop(item) for item in data["data"]]

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

import logging
import aiohttp
import asyncio

class SessionManager:
    """Singleton class to manage a shared aiohttp.ClientSession."""

    _session: Optional[aiohttp.ClientSession] = None
    _semaphore: Optional[asyncio.Semaphore] = None
    _max_concurrent_requests: int = 10  # Default maximum concurrent requests
    _logger: logging.Logger = None

    @classmethod
    def configure(cls, max_concurrent_requests: int = 10, session: Optional[aiohttp.ClientSession] = None, logger: logging.Logger = None):
        """
        Configure the SessionManager with the maximum number of concurrent requests and optionally an external session.

        Args:
            max_concurrent_requests (int): The number of concurrent requests allowed.
            session (aiohttp.ClientSession, optional): An external session to use.
        """
        cls._logger: logging.Logger = logger or logging.getLogger(__name__)
        cls._max_concurrent_requests = max_concurrent_requests
        cls._semaphore = asyncio.Semaphore(max_concurrent_requests)
        if session:
            cls._session = session
            cls._logger.debug(f"Using provided external session: {session}")
        else:
            cls._logger.debug(f"Creating a new session with max concurrent requests: {max_concurrent_requests}")

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """
        Get the shared aiohttp.ClientSession instance, creating it if necessary.

        Returns:
            aiohttp.ClientSession: The shared session instance.
        """
        if cls._session is None or cls._session.closed:
            cls._logger.debug("No active session found, creating a new one.")
            cls._session = aiohttp.ClientSession()
        else:
            cls._logger.debug("Returning existing session.")
        return cls._session

    @classmethod
    async def close_session(cls):
        """Close the shared aiohttp.ClientSession."""
        if cls._session and not cls._session.closed:
            cls._logger.debug("Closing the shared session.")
            await cls._session.close()
            cls._session = None
        else:
            cls._logger.debug("No session to close or already closed.")

    @classmethod
    async def cleanup(cls):
        """Clean up resources when shutting down."""
        cls._logger.debug("Cleaning up resources and closing session.")
        await cls.close_session()
        cls._semaphore = None