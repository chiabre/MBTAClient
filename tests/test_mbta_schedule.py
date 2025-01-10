import pytest
from typing import Dict

from src.mbtaclient.schedule import MBTASchedule
from tests.mock_data import VALID_SCHEDULE_RESPONSE_DATA  # Direct import

def test_init():
    """Tests that MBTASchedule is initialized correctly with or without data."""
    
    schedule = MBTASchedule(VALID_SCHEDULE_RESPONSE_DATA)

    # Test expected attributes
    assert schedule.id == VALID_SCHEDULE_RESPONSE_DATA["id"]
    assert schedule.arrival_time == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("arrival_time", "")
    assert schedule.departure_time == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("departure_time", "")
    assert schedule.direction_id == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("direction_id", 0)
    assert schedule.drop_off_type == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("drop_off_type", "")
    assert schedule.pickup_type == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("pickup_type", "")
    assert schedule.stop_headsign == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("stop_headsign", "")
    assert schedule.stop_sequence == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("stop_sequence", 0)
    assert schedule.timepoint == VALID_SCHEDULE_RESPONSE_DATA.get("attributes", {}).get("timepoint", False)

    # Test relationships
    assert schedule.route_id == VALID_SCHEDULE_RESPONSE_DATA.get("relationships", {}).get("route", {}).get("data", {}).get("id", "")
    assert schedule.stop_id == VALID_SCHEDULE_RESPONSE_DATA.get("relationships", {}).get("stop", {}).get("data", {}).get("id", "")
    assert schedule.trip_id == VALID_SCHEDULE_RESPONSE_DATA.get("relationships", {}).get("trip", {}).get("data", {}).get("id", "")
