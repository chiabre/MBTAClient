from datetime import datetime, timedelta
from typing import Optional
import logging

from ..client.mbta_client import MBTAClient
from ..handlers.base_handler import MBTABaseHandler
from ..trip_stop import StopType
from ..trip import Trip


class TimetableHandler(MBTABaseHandler):
    """Handler for managing timetable."""

    def __repr__(self) -> str:
        if self._departures:
            # Access the first trip safely and fetch the departure stop
            first_trip = next(iter(self._trips.values()), None)
            departure_stop = first_trip.get_stop_by_type(StopType.DEPARTURE) if first_trip else "Unknown"
            return f"TimetableHandler(departures from {departure_stop})"
        else:
            # Access the first trip safely and fetch the arrival stop
            first_trip = next(iter(self._trips.values()), None)
            arrival_stop = first_trip.get_stop_by_type(StopType.ARRIVAL) if first_trip else "Unknown"
            return f"TimetableHandler(arrivals to {arrival_stop})"
    
    @classmethod
    async def create(
        cls, 
        stop_name: str ,
        mbta_client: MBTAClient, 
        max_trips: Optional[int] = 5,
        departures: Optional[bool] = True,
        logger: Optional[logging.Logger] = None)-> "TimetableHandler":
        
        """Asynchronous factory method to initialize TimetableHandler."""
        if departures:
            departure_stop_name = stop_name
            arrival_stop_name = None
        else :
            departure_stop_name = None
            arrival_stop_name = stop_name
        instance = await super()._create(mbta_client=mbta_client, departure_stop_name=departure_stop_name, arrival_stop_name=arrival_stop_name,max_trips=max_trips,logger=logger)
        
        instance._departures  = departures
        instance._logger = logger or logging.getLogger(__name__)  # Logger instance
        
        return instance

    async def update(self) -> list[Trip]:
        self._logger.debug("Updating Trips")
        try:
            
            # Initialize trips
            trips: dict[str, Trip] = {}

            # Update trip scheduling
            updated_trips = await super()._update_scheduling(trips=trips)
            
            #sorted_trips = super()._sort_trips(updated_trips, StopType.DEPARTURE)
 
            # Filter out departed trips'
            filtered_trips = self.filter_trips(trips=updated_trips, remove_departed=True)

            # Update trip details
            detailed_trips = await super()._update_details(trips=filtered_trips)

            # Filter out departed trips again
            filtered_detailed_trips = self.filter_trips(trips=detailed_trips, remove_departed=True)

            # Limit trips to the maximum allowed
            limited_trips = dict(list(filtered_detailed_trips.items())[:self._max_trips])

            # Sort trips by departure time
            #sorted_trips = super()._sort_trips(limited_trips, StopType.DEPARTURE)           
            
            # self._trips = await self.create_timetable()
            
            # if self._departures:
            #     self._trips = super()._sort_trips(StopType.DEPARTURE)
            # else:
            #     self._trips = super()._sort_trips(StopType.ARRIVAL)   
        
            return list(limited_trips.values())
            
        except Exception as e:
            self._logger.error(f"Error updating trips: {e}")
            raise
   
    def filter_trips(self, trips: dict[str, Trip], remove_departed: bool = False) -> dict[str, Trip]:
        """Filter trips based on conditions like direction, departure, and arrival times."""
        self._logger.debug("Filtering Trips")
        now = datetime.now().astimezone()
        filtered_trips: dict[str, Trip] = {}
        try:
            trips = super()._sort_trips(trips)
            for trip_id, trip in trips.items():
                departure_stop = trip.get_stop_by_type(StopType.DEPARTURE)
                arrival_stop = trip.get_stop_by_type(StopType.ARRIVAL)
                
                if arrival_stop:
                    continue
                
                if departure_stop.arrival_time and not departure_stop.departure_time:
                    continue

                vehicle_current_stop_sequence = trip.vehicle_current_stop_sequence

                # If vehicle_current_stop_sequence exists, use it for validation
                if vehicle_current_stop_sequence is not None:
                    # Check if the trip has departed and filter it out if remove_departed is true and trip has departed more than 1 min ago
                    if remove_departed and vehicle_current_stop_sequence > departure_stop.stop_sequence and departure_stop.time < now - timedelta(minutes=1):
                        continue

                else:  # Fallback to time-based logic

                    # Filter out trips based on departure time if required
                    if remove_departed and departure_stop.time < now - timedelta(minutes=10):
                        continue

                # Add the valid trip to the processed trips
                filtered_trips[trip_id] = trip

            return dict(list(filtered_trips.items())[:100])
        
        except Exception as e:
            self._logger.error(f"Error filtering trips: {e}")
            raise   