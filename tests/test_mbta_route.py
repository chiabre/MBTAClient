import pytest
from typing import Dict

from src.mbtaclient.mbta_route import MBTARoute


@pytest.mark.parametrize(
    "route_data",
    [
        {
            "id": "route-123",
            "attributes": {
                "color": "#0099CC",
                "description": "Green Line B",
                "direction_destinations": ["Bowdoin", "Cleaveland Circle"],
                "direction_names": ["Outbound", "Inbound"],
                "fare_class": "1",
                "long_name": "Green Line B",
                "short_name": "B",
                "sort_order": 3,
                "text_color": "#FFFFFF",
                "type": "light_rail",
            },
        },
        # Test case with missing data
        {"id": "route-123"},
    ],
)
def test_init(route_data):
    """Tests that MBTARoute is initialized correctly with or without data."""

    route = MBTARoute(route_data)

    # Test expected attributes
    assert route.id == route_data["id"]
    assert route.color == route_data.get("attributes", {}).get("color", "")
    assert route.description == route_data.get("attributes", {}).get("description", "")
    assert route.direction_destinations == route_data.get(
        "attributes", {}
    ).get("direction_destinations", [])
    assert route.direction_names == route_data.get("attributes", {}).get(
        "direction_names", []
    )
    assert route.fare_class == route_data.get("attributes", {}).get("fare_class", "")
    assert route.long_name == route_data.get("attributes", {}).get("long_name", "")
    assert route.short_name == route_data.get("attributes", {}).get("short_name", "")
    assert route.sort_order == route_data.get("attributes", {}).get("sort_order", 0)
    assert route.text_color == route_data.get("attributes", {}).get("text_color", "")
    assert route.type == route_data.get("attributes", {}).get("type", "")


def test_repr():
    """Tests that the __repr__ method returns a string representation."""

    route_data = {"id": "route-123"}
    route = MBTARoute(route_data)

    assert repr(route) == "MBTAroute(id=route-123)"