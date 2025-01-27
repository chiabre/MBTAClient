import asyncio
import logging
from typing import Optional
import aiohttp

MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 10

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
        max_concurrent_requests: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """Configure the SessionManager."""
        cls._logger = logger or logging.getLogger(__name__)
        cls._max_concurrent_requests = max_concurrent_requests or cls._max_concurrent_requests
        cls._timeout = timeout or cls._timeout
        cls._semaphore = asyncio.Semaphore(cls._max_concurrent_requests)
        if session:
            cls._session = session
            cls._own_session = False
        cls._logger.debug("MBTASessionManager initialized")

    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get the shared aiohttp.ClientSession instance, creating it if necessary."""
        if cls._session is None or cls._session.closed:
            cls._logger.debug("Creating a new aiohttp.ClientSession instance")
            cls._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=cls._timeout))
            cls._own_session = True
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
        cls._semaphore = None

    @classmethod
    async def __aenter__(cls):
        await cls.get_session()
        return cls

    @classmethod
    async def __aexit__(cls, exc_type, exc, tb):
        await cls.cleanup()
