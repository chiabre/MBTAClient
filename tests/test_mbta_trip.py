import pytest
from src.mbtaclient.models.mbta_trip import MBTATrip
from tests.mock_data import VALID_TRIP_RESPONSE_DATA  # Direct import

def test_mbta_trip_init():
    """Tests that MBTATrip is initialized correctly with the trip data."""
    
    # Create an MBTATrip instance with mock data
    trip = MBTATrip(VALID_TRIP_RESPONSE_DATA)
    
    # Test expected attributes
    assert trip.id == VALID_TRIP_RESPONSE_DATA.get("id", "")
    assert trip.name == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("name", None)
    assert trip.headsign == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("headsign", None)
    assert trip.direction_id == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("direction_id", None)
    assert trip.block_id == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("block_id", None)
    assert trip.shape_id == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("shape_id", None)
    assert trip.wheelchair_accessible == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("wheelchair_accessible", None)
    assert trip.bikes_allowed == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("bikes_allowed", None)
    assert trip.schedule_relationship == VALID_TRIP_RESPONSE_DATA.get("attributes", {}).get("schedule_relationship", None)

    # Test relationships
    assert trip.route_id == VALID_TRIP_RESPONSE_DATA.get("relationships", {}).get("route", {}).get("data", {}).get("id", None)

    # Confirm the __repr__ method includes key identifying attributes
    repr_string = repr(trip)
    assert f"MBTATrip(id={trip.id}, headsign={trip.headsign})" in repr_string
