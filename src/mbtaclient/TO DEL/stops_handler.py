from typing import Optional, List
from mbtaclient.models.mbta_schedule import MBTASchedule
from mbtaclient.models.mbta_stop import MBTAStop
from .client.mbta_client import MBTAClient
import logging

class MBTAStopError(Exception):
    pass

class StopHandler:
    def __init__(self, stop_name: str, client: MBTAClient, logger: Optional[logging.Logger] = None) -> None:
        self._name = stop_name
        self._stops: list[MBTAStop] = []
        self._ids: list[str] = []
        self._client = client
        self._logger = logger or logging.getLogger(__name__)

    def __repr__(self) -> str:
        return f"StopHandler(name={self._name})"
    
    @classmethod
    async def create(cls, stop_name: str, client: MBTAClient, logger: Optional[logging.Logger] = None):
        """Asynchronous factory method to initialize and fetch/process stops."""
        instance = cls(stop_name, client, logger)
        try:
            stops = await instance.__fetch_stops()
            instance.__process_stops(stops)
        except Exception as e:
            instance._logger.error(f"Failed to initialize StopHandler: {e}")
            raise
        return instance

    async def __fetch_stops(self, params: dict = None) -> list[MBTAStop]:
        """Retrieve stops."""
        self._logger.debug("Fetching MBTA stops")
        base_params = {'filter[location_type]': '0'}
        if params is not None:
            base_params.update(params)
        try:
            stops: list[MBTAStop] = await self._client.fetch_stops(base_params)
            return stops
        except Exception as e:
            self._logger.error(f"Error fetching MBTA stops: {e}")
            raise

    def __process_stops(self, stops: list[MBTAStop]) -> None:
        """Process and filter stops."""
        self._logger.debug("Processing MBTA stops")
        self._stops = self.get_stops_by_stop_name(stops, self._name)

        if not self._stops:
            self._logger.error(f"Error processing MBTA stop data for {self._name}")
            raise MBTAStopError(f"Invalid stop name: {self._name}")

        self._ids = self.get_stops_ids(self._stops)

    @staticmethod
    def get_stops_by_stop_name(stops: List[MBTAStop], stop_name: str) -> List[MBTAStop]:
        """Get stops matching a specific name."""
        return [stop for stop in stops if stop.name.lower() == stop_name.lower()]

    @staticmethod
    def get_stops_ids(stops: List[MBTAStop]) -> List[str]:
        """Get all stop IDs from a list of stops."""
        return [stop.id for stop in stops]
