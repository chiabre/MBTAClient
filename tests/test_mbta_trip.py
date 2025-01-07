import pytest
from typing import Dict

from src.mbtaclient.mbta_trip import MBTATrip


@pytest.mark.parametrize(
    "trip_data",
    [
        {
            "id": "1234",
            "attributes": {
                "name": "Green Line B",
                "headsign": "Cleveland Circle",
                "direction_id": 1,
                "block_id": "b123",
                "shape_id": "s456",
                "wheelchair_accessible": True,
                "bikes_allowed": False,
                "schedule_relationship": "weekday",
            },
            "relationships": {
                "route": {"data": {"id": "route_id_1"}},
                "service": {"data": {"id": "service_id_1"}},
            },
        },
        # Test case with missing data
        {
            "id": "5678",
            "attributes": {"name": "Red Line"},
            "relationships": {"route": {"data": {}}},
        },
    ],
)
def test_init(trip_data):
    """Tests that MBTATrip is initialized correctly with or without data."""

    trip = MBTATrip(trip_data)

    # Test expected attributes
    assert trip.id == trip_data["id"]
    assert trip.name == trip_data.get("attributes", {}).get("name", "")
    assert trip.headsign == trip_data.get("attributes", {}).get("headsign", "")
    assert trip.direction_id == trip_data.get("attributes", {}).get("direction_id", 0)
    assert trip.block_id == trip_data.get("attributes", {}).get("block_id", "")
    assert trip.shape_id == trip_data.get("attributes", {}).get("shape_id", "")
    assert trip.wheelchair_accessible is trip_data.get(
        "attributes", {}
    ).get("wheelchair_accessible")
    assert trip.bikes_allowed is trip_data.get("attributes", {}).get("bikes_allowed")
    assert trip.schedule_relationship == trip_data.get(
        "attributes", {}
    ).get("schedule_relationship", "")

    # Test relationships
    assert trip.route_id == (
        trip_data.get("relationships", {}).get("route", {}).get("data", {}).get(
            "id", ""
        )
    )
    assert trip.service_id == (
        trip_data.get("relationships", {}).get("service", {}).get("data", {}).get(
            "id", ""
        )
    )


# Add more test cases for different scenarios (e.g., invalid data types, edge cases)