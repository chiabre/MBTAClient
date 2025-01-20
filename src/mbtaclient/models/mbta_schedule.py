from typing import Any, Optional

class MBTASchedule:
    """A schedule object to hold information about a schedule."""

    def __init__(self, schedule: dict[str, Any]) -> None:
        # ID
        self.id: Optional[str] = schedule.get('id', None)
        
        # Attributes
        attributes = schedule.get('attributes', {})
        self.arrival_time: Optional[str] = attributes.get('arrival_time', None)
        self.departure_time: Optional[str] = attributes.get('departure_time', None)
        self.direction_id: Optional[int] = attributes.get('direction_id', None)
        self.drop_off_type: Optional[str] = attributes.get('drop_off_type', None)
        self.pickup_type: Optional[str] = attributes.get('pickup_type', None)
        self.stop_headsign: Optional[str] = attributes.get('stop_headsign', None)
        self.stop_sequence: Optional[int] = attributes.get('stop_sequence', None)
        self.timepoint: Optional[bool] = attributes.get('timepoint', None)

        # Relationships
        relationships = schedule.get('relationships', {})
        self.route_id: Optional[str] = relationships.get('route', {}).get('data', {}).get('id', None)
        self.stop_id: Optional[str] = relationships.get('stop', {}).get('data', {}).get('id', None)
        self.trip_id: Optional[str] = relationships.get('trip', {}).get('data', {}).get('id', None)
        self.prediction_id: Optional[str] = relationships.get('prediction', {}).get('data', {}).get('id', None)

    def __repr__(self) -> str:
        return (f"MBTASchedule(id={self.id}, route_id={self.route_id}, stop_id={self.stop_id})")


