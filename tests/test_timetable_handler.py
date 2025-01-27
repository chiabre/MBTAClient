from inspect import isdatadescriptor
import pytest
from dotenv import load_dotenv
import os

from src.mbtaclient.trip import Trip
from src.mbtaclient.client.mbta_client import MBTAClient
from src.mbtaclient.client.mbta_cache_manager import MBTACacheManager
from src.mbtaclient.handlers.timetable_handler import TimetableHandler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stop_name, route_type",
    [
        ("West Natick", "Commuter Rail"),
        ("Wollaston", "Heavy Rail"),
        ("Copley", "Light Rail"),
        ("Huntington Ave @ Opera Pl", "Bus"),
        ("Long Wharf (South)", "Ferry"),
        ("South Station", "Commuter Rail + Heavy Rail + Bus"),
        ("North Station", "Commuter Rail + Heavy Rail + Light Rail"),
        ("Park Street", "Heavy Rail + Light Rail"),
    ]
)
async def test_handler(stop_name, route_type):
    """
    Integration test for TimetableHandler for different route types.
    Ensures that trips are correctly retrieved and processed for various stops and route types.

    Args:
        stop_name (str): Name of the stop to test.
        route_type (str): Type of the route (e.g., train, ferry, bus).
    """
    # Load .env file
    load_dotenv()

    # Access the token
    API_KEY = os.getenv("API_KEY")

    # Initialize MBTA Cache Manager and Client
    cache_manager = MBTACacheManager(stats_interval=10)
    async with MBTAClient(cache_manager=cache_manager, api_key=API_KEY) as mbta_client:
        
        print(f"Testing TimetableHandler for stop: {stop_name} ({route_type})")
        
        # Configure the handler for the given stop
        max_trips = 5  # Limit the number of trips to process
        handler: TimetableHandler = await TimetableHandler.create(
            stop_name=stop_name,
            mbta_client=mbta_client,
            max_trips=max_trips,
            departures=True
        )
        
        # Fetch trips using the handler
        trips = await handler.update()
        
        # Assertions to verify handler functionality
        assert trips is not None, f"No trips returned for stop: {stop_name}"
        assert len(trips) <= max_trips, f"More trips than expected for stop: {stop_name}"
        
        for trip in trips:
            # Validate essential trip properties
            assert trip.mbta_route is not None, f"Trip is missing route information for {stop_name}"
            assert trip.mbta_trip is not None, f"Trip is missing trip information for {stop_name}"
            assert trip.departure_time is not None, f"Trip is missing departure time for {stop_name}"
            
            # Route type-specific validations
            if trip.mbta_route.type in [1, 2]:  # Heavy Rail or Commuter Rail
                assert trip.departure_platform_name is not None, (
                    f"Rail trip at stop {stop_name} must have a platform name."
                )
            
            # Ensure trips belong to the expected route type
            assert any(route_type_part in trip.route_description for route_type_part in route_type.split(" + ")), (
                f"Route type mismatch for stop: {stop_name}. "
                f"Expected one of {route_type}, but got {trip.route_description}."
            )
            
            # Print trip details for debugging
            properties = [attr for attr in dir(Trip) if isdatadescriptor(getattr(Trip, attr))]
            for property_name in properties:
                print(f"trip.{property_name}: {getattr(trip, property_name)}")  
            print("##############") 