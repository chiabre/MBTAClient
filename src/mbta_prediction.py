import typing
from typing import Any, Dict, Optional

class MBTAPrediction:
    """A prediction object to hold information about a prediction."""
    
    UNCERTAINTY = {
        '60': 'Trip that has already started',
        '120': 'Trip not started and a vehicle is awaiting departure at the origin',
        '300': 'Vehicle has not yet been assigned to the trip',
        '301': 'Vehicle appears to be stalled or significantly delayed',
        '360': 'Trip not started and a vehicle is completing a previous trip'
    }

    def __init__(self, prediction: Dict[str, Any]) -> None:
        attributes = prediction.get('attributes', {})
        
        self.id: str = prediction.get('id', '')
        self.arrival_time: str = attributes.get('arrival_time', '')
        self.arrival_uncertainty: str = self.get_uncertainty_description(attributes.get('arrival_uncertainty', ''))
        self.departure_time: str = attributes.get('departure_time', '')
        self.departure_uncertainty: str = self.get_uncertainty_description(attributes.get('departure_uncertainty', ''))
        self.direction_id: int = attributes.get('direction_id', 0)
        self.last_trip: Optional[bool] = attributes.get('last_trip')
        self.revenue: Optional[bool] = attributes.get('revenue')
        self.schedule_relationship: str = attributes.get('schedule_relationship', '')
        self.status: str = attributes.get('status', '')
        self.stop_sequence: int = attributes.get('stop_sequence', 0)
        self.update_type: str = attributes.get('update_type', '')

        self.route_id: str = prediction.get('relationships', {}).get('route', {}).get('data', {}).get('id', '')
        self.stop_id: str = prediction.get('relationships', {}).get('stop', {}).get('data', {}).get('id', '')
        self.trip_id: str = prediction.get('relationships', {}).get('trip', {}).get('data', {}).get('id', '')

    def __repr__(self) -> str:
        return (f"MBTAprediction(id={self.id}, route_id={self.route_id}, stop_id={self.stop_id}, trip_id={self.trip_id})")

    @staticmethod
    def get_uncertainty_description(key: str) -> str:
        return MBTAPrediction.UNCERTAINTY.get(key, 'None')