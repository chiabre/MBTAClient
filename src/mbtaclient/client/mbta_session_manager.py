import asyncio
import logging
import random
from typing import Optional
import aiohttp

MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
INITIAL_BACKOFF = 1
BACKOFF_MULTIPLIER = 2

class MBTASessionManager:
    """Singleton class to manage a shared aiohttp.ClientSession."""
    
    _session: Optional[aiohttp.ClientSession] = None
    _semaphore: Optional[asyncio.Semaphore] = None
    _logger: Optional[logging.Logger] = None
    _max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS
    _timeout: int = REQUEST_TIMEOUT
    _own_session: bool = True

    @classmethod
    def configure(
        cls,
        session: Optional[aiohttp.ClientSession] = None,
        logger: Optional[logging.Logger] = None,
        max_concurrent_requests: Optional[int] = MAX_CONCURRENT_REQUESTS,
        timeout: Optional[int] = REQUEST_TIMEOUT,
    ):
        """Configure the SessionManager."""
        cls._logger = logger or logging.getLogger(__name__)
        cls._max_concurrent_requests = (
            max_concurrent_requests if max_concurrent_requests is not None else MAX_CONCURRENT_REQUESTS
        )
        cls._timeout = timeout if timeout is not None else REQUEST_TIMEOUT
        # Always initialize the semaphore here.
        cls._semaphore = asyncio.Semaphore(cls._max_concurrent_requests)
        if session:
            cls._session = session
            cls._own_session = False
        cls._logger.debug("MBTASessionManager initialized")

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get (or create) the shared aiohttp.ClientSession instance."""
        if cls._session is None or cls._session.closed:
            cls._logger.debug("Creating a new aiohttp.ClientSession instance")
            cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cls._timeout))
            cls._own_session = True
        # Ensure the semaphore is available.
        if cls._semaphore is None:
            raise RuntimeError("Semaphore not initialized. Please call MBTASessionManager.configure() first.")
        return cls._session

    @classmethod
    async def close_session(cls):
        """Close the shared aiohttp.ClientSession."""
        if cls._own_session and cls._session and not cls._session.closed:
            try:
                cls._logger.debug("Closing the aiohttp.ClientSession instance")
                await cls._session.close()
            except Exception as e:
                if cls._logger:
                    cls._logger.error(f"Error closing session: {e}")
            finally:
                cls._session = None

    @classmethod
    async def cleanup(cls):
        """Clean up resources when shutting down."""
        cls._logger.debug("Cleaning up MBTASessionManager resources")
        await cls.close_session()
        # Do not set _semaphore to None here—in case you need to reuse the manager later.

    @classmethod
    async def request_with_retries(cls, method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Make an HTTP request with retries and exponential backoff."""
        session = await cls.get_session()
        retries = 0
        backoff = INITIAL_BACKOFF

        # Ensure the semaphore is initialized.
        if cls._semaphore is None:
            raise RuntimeError("Semaphore not initialized. Please call MBTASessionManager.configure() first.")

        async with cls._semaphore:
            while retries <= MAX_RETRIES:
                try:
                    cls._logger.debug("Request: %s %s (try %d)", method, url, retries + 1)
                    # Directly await the request so that the response remains open
                    response = await session.request(method, url, **kwargs)
                    
                    if response.status < 400:
                        # Successful response or a client error that we don't retry
                        return response
                    elif response.status in (502, 503, 504):
                        cls._logger.warning(
                            "Request failed with status %d. Retrying in %d seconds...", response.status, backoff
                        )
                        # Release connection resources before retrying.
                        await response.release()
                    else:
                        cls._logger.error("Request failed with status %d. Not retrying.", response.status)
                        return response  # Return the error response without retrying

                except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.ServerDisconnectedError) as e:
                    cls._logger.warning("Request error: %s. Retrying in %d seconds...", e, backoff)
                    if isinstance(e, aiohttp.ClientConnectionError):
                        cls._logger.error("Client connection error occurred: %s", e)
                    elif isinstance(e, asyncio.TimeoutError):
                        cls._logger.error("Request timed out: %s", e)
                    elif isinstance(e, aiohttp.ClientError):
                        cls._logger.error("A client error occurred: %s", e)

                retries += 1
                # Add jitter to the backoff
                await asyncio.sleep(backoff + random.uniform(0, 0.2))
                backoff *= BACKOFF_MULTIPLIER

        cls._logger.error("Max retries reached for request: %s %s", method, url)
        return None  # Return None if all retries fail.


class MBTASessionManagerContext:
    async def __aenter__(self):
        await MBTASessionManager.get_session()
        return MBTASessionManager

    async def __aexit__(self, exc_type, exc, tb):
        await MBTASessionManager.cleanup()
