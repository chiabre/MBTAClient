from aiohttp import ClientConnectorError, ClientResponse, ClientSession
import logging
from typing import Optional, Dict, Any

MBTA_DEFAULT_HOST = "api-v3.mbta.com"

class Auth:
    """Class to make authenticated requests to the MBTA v3 API."""
    
    def __init__(self, websession: ClientSession, api_key: Optional[str] = None, host: str = MBTA_DEFAULT_HOST) -> None:
        """Initialize the auth."""
        self.websession = websession
        self._api_key = api_key
        self._host = host
        
    async def request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None
    ) -> ClientResponse:
        """Make an HTTP request with optional query parameters and JSON body."""
        
        if params is None:
            params = {}
        if self._api_key:
            params['api_key'] = self._api_key
        
        try:
            response = await self.websession.request(
                method,
                f'https://{self._host}/{path}',
                params=params,
                json=json
            )
            
            # Ensure response has a valid status code
            response.raise_for_status()
            
            return response
            
        except ClientConnectorError as error:
            logging.error(f"Connection error: {error}")
            raise CannotConnect(error)
        except Exception as error:
            logging.error(f"An error occurred: {error}")
            raise

class CannotConnect(Exception):
    """Exception to indicate connection problems."""
    
    def __init__(self, error: Exception) -> None:
        super().__init__(f"Cannot connect to the API: {error}")
        self.error = error
