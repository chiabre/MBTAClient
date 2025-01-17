import logging
from typing import Optional
from mbtaclient.client.mbta_client import MBTAClient
from mbtaclient.models.mbta_schedule import MBTASchedule

class MBTASchedulesHandler:
    def __init__(self, stop_ids: str, client: MBTAClient, logger: Optional[logging.Logger] = None) -> None:
        self.stop_ids = stop_ids
        self.schedules: list[MBTASchedule] = []
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
        
    @classmethod
    async def create(cls, stop_ids: str, client: MBTAClient, logger: Optional[logging.Logger] = None):
        """Asynchronous factory method to initialize and fetch/process schedules."""
        instance = cls(stop_ids, client, logger)
        try:
            schdules = await instance.__fetch_schedules()
            #instance.__process_stops(stops)
        except Exception as e:
            instance._logger.error(f"Failed to initialize StopHandler: {e}")
            raise
        return instance
    
    async def update(self):
        """Asynchronous factory method to update/fetch/process schedules."""
        try:
            schdules, from_cache = await self.__fetch_schedules()
            if from_cache:
                self.logger.debug("CACHE!!!!")
        except Exception as e:
            self.logger.error(f"Failed to initialize StopHandler: {e}")
            raise

    async def __fetch_schedules(self, params: Optional[dict] = None) -> list[MBTASchedule]:
            """Retrieve MBTA schedules"""
            self.logger.debug("Fetching MBTA schedules")
            base_params = {
                'filter[stop]': ','.join(self.stop_ids),
                'sort': 'departure_time'
            }
            if params is not None:
                base_params.update(params)
            try:
                schedules: list[MBTASchedule] = await self.client.fetch_schedules(base_params)
                return schedules
            except Exception as e:
                self.logger.error("Error retrieving MBTA schedules: {}".format(e))
                return []
            
    def __timetable(self):
        timetable = {}
        for schedule in self.schedules:
            timetable{'route_id'] = schedule.route_id
            timetable[]