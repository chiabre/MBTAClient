import pytest
from typing import Dict

from src.mbtaclient.mbta_stop import MBTAStop


@pytest.mark.parametrize(
    "stop_data",
    [
        {
            "id": "place-dit9",
            "attributes": {
                "address": "100 Mystic Ave, Medford, MA 02155",
                "at_street": "Mystic Ave",
                "description": "Sullivan Square",
                "latitude": 42.408733,
                "location_type": 1,
                "longitude": -71.060088,
                "municipality": "Medford",
                "name": "Sullivan Square",
                "on_street": "Mystic Ave",
                "platform_code": "",
                "platform_name": "",
                "vehicle_type": 0,
                "wheelchair_boarding": 1,
            },
        },
        # Test case with missing data
        {"id": "place-dit9"},
    ],
)
def test_init(stop_data):
    """Tests that MBTAStop is initialized correctly with or without data."""

    stop = MBTAStop(stop_data)

    # Test expected attributes
    assert stop.id == stop_data["id"]
    assert stop.address == stop_data.get("attributes", {}).get("address", "")
    assert stop.at_street == stop_data.get("attributes", {}).get("at_street", "")
    assert stop.description == stop_data.get("attributes", {}).get("description", "")
    assert stop.location_type == stop_data.get("attributes", {}).get("location_type", 0)
    assert stop.municipality == stop_data.get("attributes", {}).get("municipality", "")
    assert stop.name == stop_data.get("attributes", {}).get("name", "")
    assert stop.on_street == stop_data.get("attributes", {}).get("on_street", "")
    assert stop.platform_code == stop_data.get("attributes", {}).get("platform_code", "")
    assert stop.platform_name == stop_data.get("attributes", {}).get("platform_name", "")
    assert stop.vehicle_type == stop_data.get("attributes", {}).get("vehicle_type", 0)
    assert stop.wheelchair_boarding == stop_data.get("attributes", {}).get(
        "wheelchair_boarding", 0
    )

    # Use pytest.approx for floating-point comparisons
    assert pytest.approx(stop.latitude) == stop_data.get("attributes", {}).get(
        "latitude", 0.0
    )
    assert pytest.approx(stop.longitude) == stop_data.get("attributes", {}).get(
        "longitude", 0.0
    )


def test_repr():
    """Tests that the __repr__ method returns a string representation."""

    stop_data = {"id": "place-dit9"}
    stop = MBTAStop(stop_data)

    assert repr(stop) == "MBTAstop(id=place-dit9)"