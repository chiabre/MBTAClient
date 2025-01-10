import pytest
from datetime import datetime, timedelta
from src.mbtaclient.stop import MBTAStop
from src.mbtaclient.utils import MBTAUtils
from src.mbtaclient.journey_stop import JourneyStop


def test_journey_stop_init():
    """Test initialization of JourneyStop object."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)

    journey_stop = JourneyStop(
        stop,
        arrival_time=future_time.isoformat(),
        departure_time=future_time.isoformat(),
        stop_sequence=1,
        status="Scheduled",
    )

    assert journey_stop.stop == stop
    assert journey_stop.arrival_time == future_time
    assert journey_stop.real_arrival_time is None
    assert journey_stop.arrival_delay is None
    assert journey_stop.departure_time == future_time
    assert journey_stop.real_departure_time is None
    assert journey_stop.departure_delay is None
    assert journey_stop.status == "Scheduled"
    assert journey_stop.stop_sequence == 1


def test_journey_stop_update_stop_with_real_times():
    """Test update_stop with real arrival and departure times."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)
    real_arrival_time_str = (future_time + timedelta(minutes=5)).isoformat()
    real_departure_time_str = (future_time + timedelta(minutes=10)).isoformat()

    journey_stop = JourneyStop(
        stop,
        arrival_time=future_time.isoformat(),
        departure_time=future_time.isoformat(),
        stop_sequence=1,
        status="Scheduled",
    )

    journey_stop.update_stop(
        stop, real_arrival_time_str, real_departure_time_str, 1, "On Time"
    )

    assert journey_stop.real_arrival_time == future_time + timedelta(minutes=5)
    assert journey_stop.arrival_delay == timedelta(minutes=5).total_seconds()
    assert journey_stop.real_departure_time == future_time + timedelta(minutes=10)
    assert journey_stop.departure_delay == timedelta(minutes=10).total_seconds()


def test_journey_stop_update_stop_with_none_times():
    """Test update_stop with None times."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)

    journey_stop = JourneyStop(
        stop,
        arrival_time=future_time.isoformat(),
        departure_time=future_time.isoformat(),
        stop_sequence=1,
        status="Scheduled",
    )

    journey_stop.update_stop(stop, None, None, 1, "Cancelled")

    assert journey_stop.real_arrival_time is None
    assert journey_stop.arrival_delay is None
    assert journey_stop.real_departure_time is None
    assert journey_stop.departure_delay is None


def test_journey_stop_get_time():
    """Test get_time method."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)
    past_time = datetime.now() - timedelta(minutes=10)

    journey_stop = JourneyStop(
        stop, arrival_time=future_time.isoformat(), departure_time=None, stop_sequence=1, status="Scheduled"
    )
    assert journey_stop.get_time() == future_time

    journey_stop.update_stop(stop, None, future_time.isoformat(), 1, "Scheduled")
    assert journey_stop.get_time() == future_time

    journey_stop.update_stop(stop, past_time.isoformat(), None, 1, "Scheduled")
    assert journey_stop.get_time() == past_time

    journey_stop.update_stop(stop, None, None, 1, "Cancelled")
    assert journey_stop.get_time() is None


def test_journey_stop_get_delay():
    """Test get_delay method."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)

    journey_stop = JourneyStop(
        stop,
        arrival_time=future_time.isoformat(),
        departure_time=future_time.isoformat(),
        stop_sequence=1,
        status="Scheduled",
    )

    # First, test with departure time set (arrival time is None)
    journey_stop.update_stop(
        stop,
        None,
        (future_time + timedelta(minutes=5)).isoformat(),  # 5 minutes late departure
        1,
        "Scheduled",
    )
    # Assert that departure delay is returned
    assert journey_stop.get_delay() == timedelta(minutes=5).total_seconds()

    # Now update with arrival time (set arrival delay)
    journey_stop.update_stop(
        stop,
        (future_time + timedelta(minutes=5)).isoformat(),  # 5 minutes late arrival
        None,
        1,
        "Scheduled",
    )
    # Assert that arrival delay is returned (since arrival delay is more relevant)
    assert journey_stop.get_delay() == timedelta(minutes=5).total_seconds()

    # Now update with departure time (set departure delay)
    journey_stop.update_stop(
        stop,
        None,
        (future_time + timedelta(minutes=10)).isoformat(),  # 10 minutes late departure again
        1,
        "Scheduled",
    )
    # Assert that arrival delay is still returned (since arrival delay is more relevant)
    assert journey_stop.get_delay() == timedelta(minutes=5).total_seconds()


def test_journey_stop_get_time_to():
    """Test get_time_to method."""
    stop = MBTAStop(stop={"id": "test_stop_id", "name": "Test Stop"})
    future_time = datetime.now() + timedelta(minutes=30)
    past_time = datetime.now() - timedelta(minutes=10)

    journey_stop = JourneyStop(
        stop, arrival_time=future_time.isoformat(), departure_time=None, stop_sequence=1, status="Scheduled"
    )
    time_to = journey_stop.get_time_to()
    assert time_to >= 0

    journey_stop.update_stop(stop, None, future_time.isoformat(), 1, "Scheduled")
    time_to = journey_stop.get_time_to()
    assert time_to >= 0

    journey_stop.update_stop(stop, past_time.isoformat(), None, 1, "Scheduled")
    time_to = journey_stop.get_time_to()
    assert time_to <= 0

    journey_stop.update_stop(stop, None, None, 1, "Cancelled")
    assert journey_stop.get_time_to() is None