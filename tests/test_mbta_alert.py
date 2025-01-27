from src.mbtaclient.models.mbta_alert import MBTAAlert, MBTAAlertsInformedEntity
from tests.mock_data import VALID_ALERT_RESPONSE_DATA  # Direct import from mock data


def test_mbta_alert_init():
    """Test initialization of MBTAAlert object."""
    alert = MBTAAlert(VALID_ALERT_RESPONSE_DATA)

    # Verify primary attributes
    assert alert.id == "382310"
    assert alert.header == (
        "The Quincy Adams parking garage has re-opened with most parking spaces available. "
        "Customers can access the garage via the Route 3 off ramp exit as well as the Burgin Parkway entrance."
    )
    assert alert.severity == 1

    # Verify informed entities
    assert len(alert.informed_entities) == 3
    informed_entity: MBTAAlertsInformedEntity = alert.informed_entities[0]
    assert informed_entity.stop_id == "70103"
    assert informed_entity.route_id == "Red"

