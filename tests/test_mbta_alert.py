import pytest
from src.mbtaclient.alert import MBTAAlert
from tests.mock_data import VALID_ALERT_RESPONSE_DATA  # Direct import from mock data

def test_mbta_alert_init():
    """Test initialization of MBTAAlert object."""
    alert = MBTAAlert(VALID_ALERT_RESPONSE_DATA)

    assert alert.id == "382310"
    assert alert.cause == "CONSTRUCTION"
    assert alert.effect == "STATION_ISSUE"
    assert alert.header_text == (
        "The Quincy Adams parking garage has re-opened with most parking spaces available. "
        "Customers can access the garage via the Route 3 off ramp exit as well as the Burgin Parkway entrance."
    )
    assert alert.severity == 1
    assert len(alert.informed_entities) == 3
    assert alert.informed_entities[0]["stop"] == "70103"
    assert alert.informed_entities[0]["route"] == "Red"

def test_mbta_alert_get_informed_stops():
    """Test get_informed_stops method."""
    alert = MBTAAlert(VALID_ALERT_RESPONSE_DATA)

    # Test for informed stops
    informed_stops = alert.get_informed_stops()
    assert set(informed_stops) == {"70103", "70104", "place-qamnl"}

def test_mbta_alert_get_informed_trips():
    """Test get_informed_trips method."""
    alert = MBTAAlert(VALID_ALERT_RESPONSE_DATA)

    # Test for informed trips (should be empty)
    informed_trips = alert.get_informed_trips()
    assert informed_trips == []

def test_mbta_alert_get_informed_routes():
    """Test get_informed_routes method."""
    alert = MBTAAlert(VALID_ALERT_RESPONSE_DATA)

    # Test for informed routes
    informed_routes = alert.get_informed_routes()
    assert set(informed_routes) == {"Red"}
