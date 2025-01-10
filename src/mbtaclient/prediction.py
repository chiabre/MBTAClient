
from typing import Any, Optional
from .utils import MBTAUtils

class MBTAPrediction:
    """A prediction object to hold information about a prediction."""
    

    def __init__(self, prediction: dict[str, Any]) -> None:
        attributes = prediction.get('attributes', {})
        
        self.id: str = prediction.get('id', '')
        self.arrival_time: str = attributes.get('arrival_time', '')
        self.arrival_uncertainty: str = MBTAUtils.get_uncertainty_description(attributes.get('arrival_uncertainty', ''))
        self.departure_time: str = attributes.get('departure_time', '')
        self.departure_uncertainty: str = MBTAUtils.get_uncertainty_description(attributes.get('departure_uncertainty', ''))
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
        return (f"MBTAprediction(id={self.id})")

   