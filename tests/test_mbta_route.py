import pytest
from src.mbtaclient.route import MBTARoute
from tests.mock_data import VALID_ROUTE_RESPONSE_DATA  # Direct import

def test_init():
    """Tests that MBTARoute is initialized correctly with the route data."""
    
    # Directly use VALID_ROUTE_RESPONSE_DATA as the route_data
    route = MBTARoute(VALID_ROUTE_RESPONSE_DATA)

    # Test expected attributes using the updated structure
    assert route.id == VALID_ROUTE_RESPONSE_DATA["id"]
    assert route.color == VALID_ROUTE_RESPONSE_DATA["attributes"].get("color", "")
    assert route.description == VALID_ROUTE_RESPONSE_DATA["attributes"].get("description", "")
    assert route.direction_destinations == VALID_ROUTE_RESPONSE_DATA["attributes"].get(
        "direction_destinations", []
    )
    assert route.direction_names == VALID_ROUTE_RESPONSE_DATA["attributes"].get(
        "direction_names", []
    )
    assert route.fare_class == VALID_ROUTE_RESPONSE_DATA["attributes"].get("fare_class", "")
    assert route.long_name == VALID_ROUTE_RESPONSE_DATA["attributes"].get("long_name", "")
    assert route.short_name == VALID_ROUTE_RESPONSE_DATA["attributes"].get("short_name", "")
    assert route.sort_order == VALID_ROUTE_RESPONSE_DATA["attributes"].get("sort_order", 0)
    assert route.text_color == VALID_ROUTE_RESPONSE_DATA["attributes"].get("text_color", "")
    assert route.type == VALID_ROUTE_RESPONSE_DATA["attributes"].get("type", "")

