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
REQUEST_TIMEOUT = 5

class MBTAAuthenticationError(Exception):
    """Custom exception for MBTA authentication errors."""
    
class MBTATooManyRequestsError(Exception):
    """Custom exception for MBTA TooManyReuqests errors."""

class MBTAClientError(Exception):
    """Custom exception class for MBTA API errors."""

class MBTAClient:
    """Class to interact with the MBTA v3 API."""

    def __init__(self, 
                session: aiohttp.ClientSession = None, 
                logger: logging.Logger = None, 
                api_key: Optional[str] = None, 
                max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS,
                timeout: Optional[int] = REQUEST_TIMEOUT):
        self._session = session
        self._api_key = api_key
        self._max_concurrent_requests = max_concurrent_requests
        self._timeout = timeout 

        if self._session:
            # If an external session is provided, pass it to SessionManager
            SessionManager.configure(self._session, logger=logger, max_concurrent_requests=self._max_concurrent_requests, timeout=self._timeout)
        else:
            # If no session is provided, the SessionManager will manage it
            SessionManager.configure(logger=logger, max_concurrent_requests=self._max_concurrent_requests, timeout=self._timeout)

        
        self._logger = logger or logging.getLogger(__name__)
        self._logger.debug(f"MBTAClient initialized with API key: {'Provided' if self._api_key else 'Not Provided'}")

    async def __aenter__(self):
        """Enter the context and return the client."""
        if not self._session:
            # If session is not passed, get it from SessionManager
            self._session = await SessionManager.get_session()
            self._logger.debug("Created a new session for MBTAClient.")
        else:
            self._logger.debug("Using existing session for MBTAClient.")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the context."""
        await SessionManager.cleanup()

    # Generic fetch method for list operations
    async def fetch_list(
        self, endpoint: str, params: Optional[Dict[str, Any]], response_model_class: Type
    ) -> List[Any]:
        """Fetch a list of objects from the MBTA API."""
        data = await self._fetch_data(endpoint, params)
        # Generalize by ensuring each object is created dynamically
        return [response_model_class(item) for item in data["data"]]

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
        
        Raises:
            MBTAAuthenticationError: For 403 Forbidden errors (invalid API key).
            MBTATooManyRequestsError: For 429 Too Many Requests errors (rate limit exceeded).
            MBTAClientError: For other HTTP or unexpected errors.
        """
        params = params or {}

        # Avoid unnecessary assignment if API key is not provided
        if self._api_key:
            params["api_key"] = self._api_key

        url = f"https://{MBTA_DEFAULT_HOST}/{path}"
        
        headers = {
            "Accept-Encoding": "gzip",  # Enable gzip compression
        }

        try:
            # Make the HTTP request
            async with SessionManager._semaphore:
                response: aiohttp.ClientResponse = await self._session.request(
                    method, url, 
                    params=params, 
                    headers=headers
                )

                # Check for 403 and 429 status codes
                if response.status == 403:
                    # Authentication error
                    self._logger.error(f"Authentication error: Invalid API key or credentials (HTTP 403) - URL: {url}, Params: {params}")
                    raise MBTAAuthenticationError(f"Authentication error: Invalid API key or credentials (HTTP 403).")
                
                if response.status == 429:
                    # Rate limiting error
                    self._logger.error(f"Rate limit exceeded: Too many requests (HTTP 429) - URL: {url}, Params: {params}")
                    raise MBTATooManyRequestsError(f"Rate limit exceeded: Too many requests (HTTP 429). Please wait and try again.")
                
                # Raise for all other non-2xx HTTP responses
                response.raise_for_status()

                # Return the successful response if no error occurred
                return response

        except aiohttp.ClientResponseError as error:
            # Log HTTP client errors (non-2xx responses)
            self._logger.error(f"HTTP error on request to {url} with params {params}: {error.status} - {error.message}", exc_info=True)
            raise MBTAClientError(f"HTTP error occurred: {error.status} - {error.message}") from error

        except aiohttp.ClientConnectionError as error:
            # Log connection errors
            self._logger.error(f"Connection error during {method} request to {url} with params {params}: {error}", exc_info=True)
            raise MBTAClientError(f"Connection error occurred: {error}") from error

        except asyncio.TimeoutError as error:
            # Log timeout errors
            self._logger.error(f"Request timed out during {method} request to {url} with params {params}: {error}", exc_info=True)
            raise MBTAClientError(f"Request timed out: {error}") from error

        except Exception as error:
            # Log unexpected errors
            self._logger.error(f"Unexpected error during {method} request to {url} with params {params}: {error}", exc_info=True)
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
        """
        Configure the SessionManager with the maximum number of concurrent requests, 
        optionally an external session, and timeout.
        """
        cls._logger = logger or logging.getLogger(__name__)  # Default to a new logger if none is provided
        cls._max_concurrent_requests = max_concurrent_requests
        cls._semaphore = asyncio.Semaphore(max_concurrent_requests)
        cls._timeout = timeout
        
        if session:
            cls._session = session
            cls._logger.debug(f"Using provided external session: {session}")
        else:
            cls._logger.debug(f"Creating a new session with max concurrent requests: {max_concurrent_requests}")

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """
        Get the shared aiohttp.ClientSession instance, creating it if necessary.
        """
        if cls._session is None or cls._session.closed:
            cls._logger.debug("No active session found, creating a new one.")
            cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cls._timeout))
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
            cls._logger.debug("Session already closed or not initialized.")

    @classmethod
    async def cleanup(cls):
        """Clean up resources when shutting down."""
        cls._logger.debug("Cleaning up resources and closing session.")
        await cls.close_session()
        cls._semaphore = None

    @classmethod
    def get_semaphore(cls) -> asyncio.Semaphore:
        """Return the semaphore instance."""
        return cls._semaphore

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Return the logger instance."""
        return cls._logger

    @classmethod
    def get_max_concurrent_requests(cls) -> int:
        """Return the maximum concurrent requests limit."""
        return cls._max_concurrent_requests

    @classmethod
    def get_timeout(cls) -> int:
        """Return the timeout for requests."""
        return cls._timeout
    
    def __del__(self):
        """Ensure cleanup when the SessionManager object is deleted."""
        if self._session:
            self._logger.debug("SessionManager object is being deleted, closing session.")
            asyncio.create_task(self.cleanup())
