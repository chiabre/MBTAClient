from datetime import datetime
from src.mbtaclient.models.mbta_prediction import MBTAPrediction  # Adjust import path as per your project structure
from tests.mock_data import VALID_PREDICTION_RESPONSE_DATA  # Mock data import

def test_mbta_prediction_init():
    """Tests that MBTAPrediction is initialized correctly with the prediction data."""
    
    # Create an MBTAPrediction instance with mock data
    prediction = MBTAPrediction(VALID_PREDICTION_RESPONSE_DATA)

    # Test expected attributes
    assert prediction.id == VALID_PREDICTION_RESPONSE_DATA.get("id")
    arrival_time = VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("arrival_time")
    departure_time = VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("departure_time")
    if arrival_time:
        assert prediction.arrival_time == datetime.fromisoformat(arrival_time)
    else:
        assert prediction.arrival_time is None
    if departure_time:
        assert prediction.departure_time == datetime.fromisoformat(departure_time)
    else:
        assert prediction.departure_time is None 
    assert prediction.direction_id == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("direction_id")
    assert prediction.status == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("status")
    assert prediction.revenue_status == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("revenue_status")
    assert prediction.schedule_relationship == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("schedule_relationship")
    assert prediction.stop_sequence == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("stop_sequence")
    assert prediction.update_type == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("update_type")
    assert prediction.departure_uncertainty == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("departure_uncertainty")
    assert prediction.arrival_uncertainty == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("arrival_uncertainty")

    # Test relationships
    assert prediction.vehicle_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("vehicle", {}).get("data", {}).get("id")
    )
    assert prediction.trip_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("trip", {}).get("data", {}).get("id")
    )
    assert prediction.stop_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("stop", {}).get("data", {}).get("id")
    )
    assert prediction.route_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("route", {}).get("data", {}).get("id")
    )


    # Confirm the __repr__ method includes key identifying attributes
    repr_string = repr(prediction)
    assert f"MBTAPrediction:{prediction.id}" in repr_string
