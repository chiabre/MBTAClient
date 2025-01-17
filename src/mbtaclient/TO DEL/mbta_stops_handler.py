from typing import Optional, List, Tuple
from mbtaclient.models.mbta_stop import MBTAStop
from ..client.mbta_client import MBTAClient
import logging

class MBTAStopError(Exception):
    pass

class MBTAStopsHandler:
    def __init__(self, stop_name: str, client: MBTAClient, logger: Optional[logging.Logger] = None) -> None:
        self.name = stop_name
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        self.stops: list[MBTAStop] = []
        self.ids: list[str] = []

    def __repr__(self) -> str:
        return f"StopHandler(name={self._name})"
    
    @classmethod
    async def create(cls, stop_name: str, client: MBTAClient, logger: Optional[logging.Logger] = None):
        """Asynchronous factory method to initialize and fetch/process stops."""
        instance = cls(stop_name, client, logger)
        try:
            stops, _ = await instance.__fetch_stops()
            instance.__process_stops(stops)
        except Exception as e:
            instance.logger.error(f"Failed to initialize StopHandler: {e}")
            raise
        return instance
    
    async def update(self):
        """Asynchronous factory method to update/fetch/process stops."""
        try:
            stops, timestamp = await self.__fetch_stops()
            self.logger.debug(f"CACHE!!!! {timestamp}")
            self.__process_stops(stops)
        except Exception as e:
            self.logger.error(f"Failed to initialize StopHandler: {e}")
            raise

    async def __fetch_stops(self, params: dict = None) -> Tuple[list[MBTAStop],bool]:
        """Retrieve stops."""
        self.logger.debug("Fetching MBTA stops")
        base_params = {'filter[location_type]': '0'}
        if params is not None:
            base_params.update(params)
        try:
            stops, from_cache = await self.client.fetch_stops(base_params)
            return stops, from_cache 
        except Exception as e:
            self.logger.error(f"Error fetching MBTA stops: {e}")
            raise

    def __process_stops(self, stops: list[MBTAStop]) -> None:
        """Process and filter stops."""
        self.logger.debug("Processing MBTA stops")
        self.stops = self.get_stops_by_stop_name(stops, self.name)

        if not self.stops:
            self.logger.error(f"Error processing MBTA stop data for {self.name}")
            raise MBTAStopError(f"Invalid stop name: {self.name}")

        self.ids = self.get_stops_ids(self.stops)

    @staticmethod
    def get_stops_by_stop_name(stops: list[MBTAStop], stop_name: str) -> list[MBTAStop]:
        """Get stops matching a specific name."""
        return [stop for stop in stops if stop.name.lower() == stop_name.lower()]

    @staticmethod
    def get_stops_ids(stops: list[MBTAStop]) -> list[str]:
        """Get all stop IDs from a list of stops."""
        return [stop.id for stop in stops]
