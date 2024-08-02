import typing
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class MBTAschedule:
    """A schedule object to hold information about a schedule."""

    def __init__(self, schedule: Dict[str, Any]) -> None:
        attributes = schedule.get('attributes', {})
        
        self.schedule_id: Optional[str] = schedule.get('id')
        self.arrival_time: Optional[str] = attributes.get('arrival_time')
        self.departure_time: Optional[str] = attributes.get('departure_time')
        self.direction_id: Optional[int] = attributes.get('direction_id')
        self.drop_off_type: Optional[str] = attributes.get('drop_off_type')
        self.pickup_type: Optional[str] = attributes.get('pickup_type')
        self.stop_headsign: Optional[str] = attributes.get('stop_headsign')
        self.stop_sequence: Optional[int] = attributes.get('stop_sequence')
        self.timepoint: Optional[bool] = attributes.get('timepoint')
        
        self.route_id: Optional[str] = schedule.get('relationships', {}).get('route', {}).get('data', {}).get('id')
        self.stop_id: Optional[str] = schedule.get('relationships', {}).get('stop', {}).get('data', {}).get('id')
        self.trip_id: Optional[str] = schedule.get('relationships', {}).get('trip', {}).get('data', {}).get('id')

    def __repr__(self) -> str:
        return (f"MBTAschedule(id={self.schedule_id}, arrival_time={self.arrival_time}, departure_time={self.departure_time}, "
                f"direction_id={self.direction_id}, drop_off_type={self.drop_off_type}, pickup_type={self.pickup_type}, "
                f"stop_headsign={self.stop_headsign}, stop_sequence={self.stop_sequence}, timepoint={self.timepoint}, "
                f"route_id={self.route_id}, stop_id={self.stop_id}, trip_id={self.trip_id})")
    
    def __str__(self) -> str:
        return f"Schedule for trip {self.trip_id} at stop {self.stop_id}"
