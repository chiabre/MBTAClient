from asyncio import sleep
from datetime import datetime
from inspect import isdatadescriptor
import pytest
from dotenv import load_dotenv
import os

from src.mbtaclient.trip import Trip
from src.mbtaclient.client.mbta_client import MBTAClient
from src.mbtaclient.client.mbta_cache_manager import MBTACacheManager
from src.mbtaclient.handlers.trips_handler import TripsHandler

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "departure_stop_name, arrival_stop_name,route_type",
    [
        ("West Natick", "South Station", "Commuter Rail"),
        ("South Station", "Andrew", "Heavy Rail"),
        ("Copley", "Park Street", "Light Rail"),
        ("Ruggles", "Warren St @ Dabney Pl", "Bus"),
        ("Long Wharf (South)", "Charlestown Navy Yard", "Ferry"),
        ("Congress St @ World Trade Center Sta", "South Station", "Bus"),
    ]
)
async def test_handler(departure_stop_name, arrival_stop_name, route_type):
    """
    Integration test for TripsHandler for different route types.
    Ensures that trips are correctly retrieved and processed for various stops and route types.

    Args:
        departure_stop_name (str): Name of the departure stop.
        arrival_stop_name (str): Name of the arrival stop.
        route_type (str): Type of the route (e.g., train, ferry, bus).
    """
    # Load .env file
    load_dotenv()

    # Access the token
    API_KEY = os.getenv("API_KEY")
    
    # Initialize MBTA Cache Manager and Client
    cache_manager = MBTACacheManager(requests_per_stats_report=10)
    async with MBTAClient(cache_manager=cache_manager, api_key=API_KEY) as mbta_client:
        
        print(f"Testing TripsHandelr for: {departure_stop_name} {arrival_stop_name} {route_type}")
        
        # Configure the handler for the given stop
        max_trips = 1  # Limit the number of trips to process
        handler: TripsHandler = await TripsHandler.create(
            departure_stop_name=departure_stop_name,
            mbta_client=mbta_client,
            arrival_stop_name=arrival_stop_name,
            max_trips=max_trips,
        )
        
        # Fetch trips using the handler
        trips = await handler.update()
        trips = await handler.update()
        # Assertions to verify handler functionality
        assert trips is not None, f"No trips returned for stop: {departure_stop_name} or {arrival_stop_name}"
        assert len(trips) <= max_trips, f"More trips than expected for stop: {departure_stop_name} or {arrival_stop_name}"
        
        for trip in trips:
            # Validate essential trip properties
            assert trip.mbta_route is not None, f"Trip is missing route information for {departure_stop_name} or {arrival_stop_name}"
            assert trip.mbta_trip is not None, f"Trip is missing trip information for {departure_stop_name} or {arrival_stop_name}"
            assert trip.departure_time is not None, f"Trip is missing departure time for {departure_stop_name} or {arrival_stop_name}"
            
            # Route type-specific validations
            if trip.mbta_route.type in [1, 2]:  # Heavy Rail or Commuter Rail
                assert trip.departure_platform is not None, (
                    f"Rail trip at stop {departure_stop_name} must have a platform name."
                )
            
            # Ensure trips belong to the expected route type
            assert any(route_type_part in trip.route_description for route_type_part in route_type.split(" + ")), (
                f"Route type mismatch for stop: {departure_stop_name} or {arrival_stop_name}. "
                f"Expected one of {route_type}, but got {trip.route_description}."
            )
            
            # Print trip details for debugging
            properties = [attr for attr in dir(Trip) if isdatadescriptor(getattr(Trip, attr))]
            for property_name in properties:
                print(f"trip.{property_name}: {getattr(trip, property_name)}")  
                
            now = datetime.now().astimezone()

            # Calculate time deltas
            arrival_time = trip._departure_stop.arrival_time or trip._departure_stop.time
            departure_time = trip._departure_stop.departure_time or trip._departure_stop.time

            arrival_delta = arrival_time.astimezone() - now
            departure_delta = departure_time.astimezone() - now

            seconds_arrival = int(arrival_delta.total_seconds())
            seconds_departure = int(departure_delta.total_seconds())
            
            print(f"seconds_arrival: {seconds_arrival}")
            print(f"seconds_departure: {seconds_departure}")
         
            print("##############") 
