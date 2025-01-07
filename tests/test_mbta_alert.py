import pytest
from src.mbtaclient.mbta_alert import MBTAAlert


def test_mbta_alert_init():
    """Test initialization of MBTAAlert object."""
    alert_data = {
        "id": "12345",
        "attributes": {
            "active_period": [
                {
                    "start": "2024-07-04T10:00:00-04:00",
                    "end": "2024-07-04T12:00:00-04:00"
                }
            ],
            "cause": "Accident",
            "effect": "Delays",
            "header": "Green Line Delays",
            "description": "Accident on the tracks near Park Street station.",
            "severity": 1,
            "informed_entity": [
                {
                    "route": "Green",
                    "route_type": 13
                },
                {
                    "stop": "place-park"
                }
            ]
        }
    }

    alert = MBTAAlert(alert_data)

    assert alert.id == "12345"
    assert alert.cause == "Accident"
    assert alert.effect == "Delays"
    assert alert.header_text == "Green Line Delays"
    assert alert.severity == 1
    assert len(alert.informed_entities) == 2


def test_mbta_alert_get_informed_stops():
    """Test get_informed_stops method."""
    alert_data = {
        "id": "12345",
        "attributes": {
            "active_period": [
                {
                    "start": "2024-07-04T10:00:00-04:00",
                    "end": "2024-07-04T12:00:00-04:00"
                }
            ],
            "cause": "Accident",
            "effect": "Delays",
            "header": "Green Line Delays",
            "description": "Accident on the tracks near Park Street station.",
            "severity": 1,
            "informed_entity": [
                {
                    "route": "Green",
                    "route_type": 13
                },
                {
                    "stop": "place-park"
                }
            ]
        }
    }

    alert = MBTAAlert(alert_data)

    assert alert.get_informed_stops() == ["place-park"]


def test_mbta_alert_get_informed_trips():
    """Test get_informed_trips method."""
    alert_data = {
        "id": "12345",
        "attributes": {
            "active_period": [
                {
                    "start": "2024-07-04T10:00:00-04:00",
                    "end": "2024-07-04T12:00:00-04:00"
                }
            ],
            "cause": "Accident",
            "effect": "Delays",
            "header": "Green Line Delays",
            "description": "Accident on the tracks near Park Street station.",
            "severity": 1,
            "informed_entity": [
                {
                    "route": "Green",
                    "route_type": 13
                },
                {
                    "stop": "place-park"
                }
            ]
        }
    }

    alert = MBTAAlert(alert_data)

    assert alert.get_informed_trips() == []


def test_mbta_alert_get_informed_routes():
    """Test get_informed_routes method."""
    alert_data = {
        "id": "12345",
        "attributes": {
            "active_period": [
                {
                    "start": "2024-07-04T10:00:00-04:00",
                    "end": "2024-07-04T12:00:00-04:00"
                }
            ],
            "cause": "Accident",
            "effect": "Delays",
            "header": "Green Line Delays",
            "description": "Accident on the tracks near Park Street station.",
            "severity": 1,
            "informed_entity": [
                {
                    "route": "Green",
                    "route_type": 13
                },
                {
                    "stop": "place-park"
                }
            ]
        }
    }

    alert = MBTAAlert(alert_data)

    assert alert.get_informed_routes() == ["Green"]