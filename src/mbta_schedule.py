from typing import Any

class MBTASchedule:
    """A schedule object to hold information about a schedule."""

    def __init__(self, schedule: dict[str, Any]) -> None:
        attributes = schedule.get('attributes', {})

        self.id: str = schedule.get('id', '')
        self.arrival_time: str = attributes.get('arrival_time', '')
        self.departure_time: str = attributes.get('departure_time', '')
        self.direction_id: int = attributes.get('direction_id', 0)
        self.drop_off_type: str = attributes.get('drop_off_type', '')
        self.pickup_type: str = attributes.get('pickup_type', '')
        self.stop_headsign: str = attributes.get('stop_headsign', '')
        self.stop_sequence: int = attributes.get('stop_sequence', 0)
        self.timepoint: bool = attributes.get('timepoint', False)

        relationships = schedule.get('relationships', {})
        self.route_id: str = relationships.get('route', {}).get('data', {}).get('id', '')
        self.stop_id: str = relationships.get('stop', {}).get('data', {}).get('id', '')
        self.trip_id: str = relationships.get('trip', {}).get('data', {}).get('id', '')

    def __repr__(self) -> str:
        return (f"MBTAschedule(id={self.id})")

