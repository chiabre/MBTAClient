import pytest
from dotenv import load_dotenv
import os

from src.mbtaclient.client.mbta_client import MBTAClient
from src.mbtaclient.client.mbta_cache_manager import MBTACacheManager
from src.mbtaclient.handlers.trains_handler import TrainsHandler


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "departure_stop_name, arrival_stop_name,train",
    [
        ("South Station", "Back Bay", "509"),
    ]
)



async def test_handler(departure_stop_name, arrival_stop_name, train):
    """
    Integration test for TrinHandler.
    Ensures that trips are correctly retrieved and processed for various stops and route types.

    Args:
        departure_stop_name (str): Name of the departure stop.
        arrival_stop_name (str): Name of the arrival stop.
        train (str): Train number
    """
    # Load .env file
    load_dotenv()

    # Access the token
    API_KEY = os.getenv("API_KEY")
    
    # Initialize MBTA Cache Manager and Client
    cache_manager = MBTACacheManager(stats_interval=10)
    async with MBTAClient(cache_manager=cache_manager, api_key=API_KEY) as mbta_client:
        
        print(f"Testing TrinHandler for : {departure_stop_name} {arrival_stop_name} {train}")
        
        # Configure the handler for the given stop
        handler: TrainsHandler = await TrainsHandler.create(
            departure_stop_name=departure_stop_name,
            mbta_client=mbta_client,
            arrival_stop_name=arrival_stop_name,
            trips_names = [train]
        )
        
        # Fetch trips using the handler
        trips = await handler.update()
        
        # Assertions to verify handler functionality
        assert trips is not None, f"No trips returned for stop: {departure_stop_name} or {arrival_stop_name}"
        
        for trip in trips:
            # Validate essential trip properties
            assert trip.mbta_route is not None, f"Trip is missing route information for {departure_stop_name} or {arrival_stop_name}"
            assert trip.mbta_trip is not None, f"Trip is missing trip information for {departure_stop_name} or {arrival_stop_name}"
            assert trip.departure_time is not None, f"Trip is missing departure time for {departure_stop_name} or {arrival_stop_name}"
            
            # Route type-specific validations
            if trip.mbta_route.type in [1, 2]:  # Heavy Rail or Commuter Rail
                assert trip.departure_platform_name is not None, (
                    f"Rail trip at stop {departure_stop_name} must have a platform name."
                )
            
            # Print trip details for debugging
            print(
                f"Route Name: {trip.route_name}, "
                f"Headsign: {trip.headsign}, "
                f"Departure Time: {trip.departure_time.replace(tzinfo=None)}, "
                f"Status: {trip.departure_status}"
            )
