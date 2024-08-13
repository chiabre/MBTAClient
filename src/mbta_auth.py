import logging

from aiohttp import ClientConnectionError, ClientResponse, ClientResponseError, ClientSession
from typing import Optional, Dict, Any

class MBTAAuth:
    """Class to make authenticated requests"""
    
    def __init__(self, session: ClientSession,  host: str , api_key: Optional[str] = None) -> None:
        """Initialize the auth."""
        self._session = session
        self._api_key = api_key
        self._host = host
        
    async def request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> ClientResponse:
        """Make an HTTP request with optional query parameters and JSON body."""
        
        if params is None:
            params = {}
        if self._api_key:
            params['api_key'] = self._api_key
        
        try:
            response = await self._session.request(
                method,
                f'https://{self._host}/{path}',
                params=params
            )
            
            # Ensure response has a valid status code
            response.raise_for_status()
            
            return response
            
        except ClientConnectionError as error:
            logging.error(f"Connection error: {error}")
            raise
        except ClientResponseError as error:
            logging.error(f"Client response error: {error.status} - {str(error)}")
            raise
        except Exception as error:
            logging.error(f"An unexpected error occurred: {error}")
            raise

