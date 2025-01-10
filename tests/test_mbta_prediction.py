import pytest
from src.mbtaclient.prediction import MBTAPrediction
from src.mbtaclient.utils import MBTAUtils
from tests.mock_data import VALID_PREDICTION_RESPONSE_DATA  # Direct import

def test_init():
    """Tests that MBTAPrediction is initialized correctly with the prediction data."""
    
    # Directly use VALID_PREDICTION_RESPONSE_DATA as the prediction_data
    prediction = MBTAPrediction(VALID_PREDICTION_RESPONSE_DATA)

    # Test expected attributes using the updated structure
    assert prediction.id == VALID_PREDICTION_RESPONSE_DATA["id"]
    assert prediction.arrival_time == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("arrival_time", "")
    assert prediction.arrival_uncertainty == MBTAUtils.get_uncertainty_description(
        VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("arrival_uncertainty", "")
    )
    assert prediction.departure_time == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("departure_time", "")
    assert prediction.departure_uncertainty == MBTAUtils.get_uncertainty_description(
        VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("departure_uncertainty", "")
    )
    assert prediction.direction_id == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("direction_id", 0)
    assert prediction.last_trip is VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("last_trip")
    assert prediction.revenue is VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("revenue")
    assert prediction.schedule_relationship == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("schedule_relationship", "")
    assert prediction.status == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("status", "")
    assert prediction.stop_sequence == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("stop_sequence", 0)
    assert prediction.update_type == VALID_PREDICTION_RESPONSE_DATA.get("attributes", {}).get("update_type", "")

    # Test relationships
    assert prediction.route_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("route", {}).get("data", {}).get("id", "")
    )
    assert prediction.stop_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("stop", {}).get("data", {}).get("id", "")
    )
    assert prediction.trip_id == (
        VALID_PREDICTION_RESPONSE_DATA.get("relationships", {}).get("trip", {}).get("data", {}).get("id", "")
    )

