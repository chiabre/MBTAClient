import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.mbtaclient.journey import Journey
from src.mbtaclient.schedule import MBTASchedule
from src.mbtaclient.prediction import MBTAPrediction
from src.mbtaclient.stop import MBTAStop
from src.mbtaclient.route import MBTARoute
from src.mbtaclient.alert import MBTAAlert
from src.mbtaclient.utils import MBTAUtils
from src.mbtaclient.journey_stop import JourneyStop
from tests.mock_data import VALID_ROUTE_RESPONSE_DATA, VALID_SCHEDULE_RESPONSE_DATA, VALID_PREDICTION_RESPONSE_DATA, VALID_STOP_RESPONSE_DATA  # Direct import


@pytest.fixture
def mock_route():
    route = MBTARoute(VALID_ROUTE_RESPONSE_DATA)
    return route

@pytest.fixture
def mock_schedule():
    schedule = MBTASchedule(VALID_SCHEDULE_RESPONSE_DATA)
    return schedule

@pytest.fixture
def mock_prediction():
    prediction = MBTAPrediction(VALID_PREDICTION_RESPONSE_DATA)
    return prediction

@pytest.fixture
def mock_stop():
    stop = MBTAStop(VALID_STOP_RESPONSE_DATA)
    return stop

@pytest.fixture
def journey():
    """Fixture to create a Journey instance."""
    return Journey()


def test_add_stop(journey, mock_schedule, mock_stop):
    """Test the add_stop method."""
    journey.add_stop("departure", mock_schedule, mock_stop, "On time")

    assert journey.stops['departure'] is not None
    assert journey.stops['departure'].stop.name == "South St @ Spalding St"
    assert journey.stops['departure'].arrival_time == None
    assert journey.stops['departure'].departure_time == datetime.fromisoformat("2025-01-07T05:15:00-05:00")
    assert journey.stops['departure'].stop_sequence == 50


def test_get_route_details(journey, mock_route):
    """Test the get_route_details method."""
    journey.route = mock_route
    
    assert journey.get_route_short_name() == ""
    assert journey.get_route_long_name() == "Red Line"
    assert journey.get_route_color() == "DA291C"
    assert journey.get_route_type() == 1
    assert journey.get_route_description() == "Subway"


def test_get_stop_details(journey, mock_schedule, mock_stop):
    """Test the get_stop_details method."""
    journey.add_stop("departure", mock_schedule, mock_stop, "On time")
    journey.add_stop("arrival", mock_schedule, mock_stop, "On time")

    assert journey.get_stop_name("departure") == "South St @ Spalding St"
    assert journey.get_platform_name("departure") == None
    assert journey.get_stop_time("departure") == datetime.fromisoformat("2025-01-07T05:15:00-05:00")
    assert journey.get_stop_delay("departure") is None
    assert journey.get_stop_status("departure") == "On time"


def test_get_stop_id(journey, mock_schedule, mock_stop):
    """Test the get_stop_id method."""
    journey.add_stop("departure", mock_schedule, mock_stop, "On time")
    journey.add_stop("arrival", mock_schedule, mock_stop, "On time")

    assert journey.get_stop_id("departure") == "1936"
    assert journey.get_stop_id("arrival") == "1936"


def test_find_journey_stop_by_id(journey, mock_schedule, mock_stop):
    """Test the find_journey_stop_by_id method."""
    journey.add_stop("departure", mock_schedule, mock_stop, "On time")
    journey.add_stop("arrival", mock_schedule, mock_stop, "On time")

    journey_stop = journey.find_journey_stop_by_id("1936")
    assert journey_stop is not None
    assert journey_stop.stop.id == "1936"

    journey_stop = journey.find_journey_stop_by_id("non-existing-id")
    assert journey_stop is None
