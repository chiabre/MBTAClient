import pytest
from src.mbtaclient.stop import MBTAStop
from tests.mock_data import VALID_STOP_RESPONSE_DATA  # Direct import

def test_init():
    """Tests that MBTAStop is initialized correctly with the stop data."""
    
    # Directly use VALID_STOP_RESPONSE_DATA as the stop_data
    stop = MBTAStop(VALID_STOP_RESPONSE_DATA)

    # Test expected attributes using the updated structure
    assert stop.id == VALID_STOP_RESPONSE_DATA["id"]
    assert stop.address == VALID_STOP_RESPONSE_DATA["attributes"].get("address", "")
    assert stop.at_street == VALID_STOP_RESPONSE_DATA["attributes"].get("at_street", "")
    assert stop.description == VALID_STOP_RESPONSE_DATA["attributes"].get("description", "")
    assert stop.location_type == VALID_STOP_RESPONSE_DATA["attributes"].get("location_type", 0)
    assert stop.municipality == VALID_STOP_RESPONSE_DATA["attributes"].get("municipality", "")
    assert stop.name == VALID_STOP_RESPONSE_DATA["attributes"].get("name", "")
    assert stop.on_street == VALID_STOP_RESPONSE_DATA["attributes"].get("on_street", "")
    assert stop.platform_code == VALID_STOP_RESPONSE_DATA["attributes"].get("platform_code", "")
    assert stop.platform_name == VALID_STOP_RESPONSE_DATA["attributes"].get("platform_name", "")
    assert stop.vehicle_type == VALID_STOP_RESPONSE_DATA["attributes"].get("vehicle_type", 0)
    assert stop.wheelchair_boarding == VALID_STOP_RESPONSE_DATA["attributes"].get(
        "wheelchair_boarding", 0
    )

    # Use pytest.approx for floating-point comparisons
    assert pytest.approx(stop.latitude) == VALID_STOP_RESPONSE_DATA["attributes"].get("latitude", 0.0)
    assert pytest.approx(stop.longitude) == VALID_STOP_RESPONSE_DATA["attributes"].get("longitude", 0.0)

