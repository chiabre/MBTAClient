import pytest
from typing import Dict, Optional

from src.mbtaclient.mbta_prediction import MBTAPrediction
from src.mbtaclient.mbta_utils import MBTAUtils


@pytest.mark.parametrize(
    "prediction_data",
    [
        {
            "id": "prediction-456",
            "attributes": {
                "arrival_time": "2023-01-08T10:00:00-05:00",
                "arrival_uncertainty": "120",
                "departure_time": "2023-01-08T10:01:00-05:00",
                "departure_uncertainty": "300",
                "direction_id": 1,
                "last_trip": True,
                "revenue": True,
                "schedule_relationship": "SCHEDULED",
                "status": "ACTIVE",
                "stop_sequence": 5,
                "update_type": "PREDICTED",
            },
            "relationships": {
                "route": {"data": {"id": "route-xyz"}},
                "stop": {"data": {"id": "stop-abc"}},
                "trip": {"data": {"id": "trip-def"}},
            },
        },
        # Test case with missing data
        {"id": "prediction-456"},
    ],
)
def test_init(prediction_data):
    """Tests that MBTAPrediction is initialized correctly with or without data."""

    prediction = MBTAPrediction(prediction_data)

    # Test expected attributes
    assert prediction.id == prediction_data["id"]
    assert prediction.arrival_time == prediction_data.get("attributes", {}).get(
        "arrival_time", ""
    )
    assert prediction.arrival_uncertainty == MBTAUtils.get_uncertainty_description(
        prediction_data.get("attributes", {}).get("arrival_uncertainty", "")
    )
    assert prediction.departure_time == prediction_data.get("attributes", {}).get(
        "departure_time", ""
    )
    assert prediction.departure_uncertainty == MBTAUtils.get_uncertainty_description(
        prediction_data.get("attributes", {}).get("departure_uncertainty", "")
    )
    assert prediction.direction_id == prediction_data.get("attributes", {}).get(
        "direction_id", 0
    )
    assert prediction.last_trip is prediction_data.get("attributes", {}).get(
        "last_trip"
    )
    assert prediction.revenue is prediction_data.get("attributes", {}).get("revenue")
    assert prediction.schedule_relationship == prediction_data.get("attributes", {}).get(
        "schedule_relationship", ""
    )
    assert prediction.status == prediction_data.get("attributes", {}).get("status", "")
    assert prediction.stop_sequence == prediction_data.get("attributes", {}).get(
        "stop_sequence", 0
    )
    assert prediction.update_type == prediction_data.get("attributes", {}).get(
        "update_type", ""
    )

    # Test relationships
    assert prediction.route_id == (
        prediction_data.get("relationships", {}).get("route", {}).get("data", {}).get(
            "id", ""
        )
    )
    assert prediction.stop_id == (
        prediction_data.get("relationships", {}).get("stop", {}).get("data", {}).get(
            "id", ""
        )
    )
    assert prediction.trip_id == (
        prediction_data.get("relationships", {}).get("trip", {}).get("data", {}).get(
            "id", ""
        )
    )


def test_repr():
    """Tests that the __repr__ method returns a string representation."""

    prediction_data = {"id": "prediction-456"}
    prediction = MBTAPrediction(prediction_data)

    assert repr(prediction) == "MBTAprediction(id=prediction-456)"