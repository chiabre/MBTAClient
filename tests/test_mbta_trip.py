import pytest
from src.mbtaclient.trip import MBTATrip
from tests.mock_data import VALID_TRIP_RESPONSE_DATA  # Direct import

def test_init():
    """Tests that MBTATrip is initialized correctly with the trip data."""
    
    trip = MBTATrip(VALID_TRIP_RESPONSE_DATA)
    
    assert trip.id == VALID_TRIP_RESPONSE_DATA["id"]
    assert trip.name == VALID_TRIP_RESPONSE_DATA["attributes"].get("name", "")
    assert trip.headsign == VALID_TRIP_RESPONSE_DATA["attributes"].get("headsign", "")
    assert trip.direction_id == VALID_TRIP_RESPONSE_DATA["attributes"].get("direction_id", 0)
    assert trip.block_id == VALID_TRIP_RESPONSE_DATA["attributes"].get("block_id", "")
    assert trip.shape_id == VALID_TRIP_RESPONSE_DATA["attributes"].get("shape_id", "")
    assert trip.wheelchair_accessible == VALID_TRIP_RESPONSE_DATA["attributes"].get("wheelchair_accessible", False)
    assert trip.bikes_allowed == VALID_TRIP_RESPONSE_DATA["attributes"].get("bikes_allowed", False)
    assert trip.schedule_relationship == VALID_TRIP_RESPONSE_DATA["attributes"].get("schedule_relationship", "")

    # Test relationships
    assert trip.route_id == VALID_TRIP_RESPONSE_DATA["relationships"].get("route", {}).get("data", {}).get("id", "")
    assert trip.service_id == VALID_TRIP_RESPONSE_DATA["relationships"].get("service", {}).get("data", {}).get("id", "")

