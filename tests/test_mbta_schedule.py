import pytest
from typing import Dict

from src.mbtaclient.mbta_schedule import MBTASchedule


@pytest.mark.parametrize(
    "schedule_data",
    [
        {
            "id": "sched_1234",
            "attributes": {
                "arrival_time": "2023-01-08T09:00:00-05:00",
                "departure_time": "2023-01-08T09:01:00-05:00",
                "direction_id": 1,
                "drop_off_type": "2",
                "pickup_type": "1",
                "stop_headsign": "Riverside",
                "stop_sequence": 3,
                "timepoint": True,
            },
            "relationships": {
                "route": {"data": {"id": "route-xyz"}},
                "stop": {"data": {"id": "stop-abc"}},
                "trip": {"data": {"id": "trip-def"}},
            },
        },
        # Test case with missing data
        {"id": "sched_1234"},
    ],
)
def test_init(schedule_data):
    """Tests that MBTASchedule is initialized correctly with or without data."""

    schedule = MBTASchedule(schedule_data)

    # Test expected attributes
    assert schedule.id == schedule_data["id"]
    assert schedule.arrival_time == schedule_data.get("attributes", {}).get(
        "arrival_time", ""
    )
    assert schedule.departure_time == schedule_data.get("attributes", {}).get(
        "departure_time", ""
    )
    assert schedule.direction_id == schedule_data.get("attributes", {}).get(
        "direction_id", 0
    )
    assert schedule.drop_off_type == schedule_data.get("attributes", {}).get(
        "drop_off_type", ""
    )
    assert schedule.pickup_type == schedule_data.get("attributes", {}).get(
        "pickup_type", ""
    )
    assert schedule.stop_headsign == schedule_data.get("attributes", {}).get(
        "stop_headsign", ""
    )
    assert schedule.stop_sequence == schedule_data.get("attributes", {}).get(
        "stop_sequence", 0
    )
    assert schedule.timepoint is schedule_data.get("attributes", {}).get(
        "timepoint", False
    )

    # Test relationships
    assert schedule.route_id == (
        schedule_data.get("relationships", {}).get("route", {}).get("data", {}).get(
            "id", ""
        )
    )
    assert schedule.stop_id == (
        schedule_data.get("relationships", {}).get("stop", {}).get("data", {}).get(
            "id", ""
        )
    )
    assert schedule.trip_id == (
        schedule_data.get("relationships", {}).get("trip", {}).get("data", {}).get(
            "id", ""
        )
    )


def test_repr():
    """Tests that the __repr__ method returns a string representation."""

    schedule_data = {"id": "sched_1234"}
    schedule = MBTASchedule(schedule_data)

    assert repr(schedule) == "MBTAschedule(id=sched_1234)"