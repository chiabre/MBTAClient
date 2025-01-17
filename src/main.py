
import logging
from mbtaclient.handlers.train_trip_handler import TrainTripHandler
from mbtaclient.handlers.trips_handler import TripsHandler
from mbtaclient.trip import Trip
from mbtaclient.client.mbta_client import MBTAClient
from mbtaclient.client.mbta_cache_manager import MBTACacheManager

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,  # Set the logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

API_KEY = '65ce8c8a40314c21bab755a7325e2d2f'
MAX_JOURNEYS = 10

# DEPART_FROM = 'South Station'
# ARRIVE_AT = 'Wellesley Square'

# DEPART_FROM = 'Wellesley Square'
# ARRIVE_AT = 'South Station'

# DEPART_FROM = 'South Station'
# ARRIVE_AT = 'Braintree'

# DEPART_FROM = 'Copley'
# ARRIVE_AT = 'Park Street'

# DEPART_FROM = 'North Station'
# ARRIVE_AT = 'Swampscott'

# DEPART_FROM = 'Dorchester Ave @ Valley Rd'
# ARRIVE_AT = 'River St @ Standard St'

# DEPART_FROM = 'Back Bay'
# ARRIVE_AT = 'Huntington Ave @ Opera Pl'

# DEPART_FROM = 'Charlestown Navy Yard'
# ARRIVE_AT = 'Long Wharf (South)'

# DEPART_FROM = 'North Billerica'
# ARRIVE_AT = 'North Station'

# DEPART_FROM = 'Back Bay'
# ARRIVE_AT = 'South Station'

# DEPART_FROM = 'Pemberton Point'
# ARRIVE_AT = 'Summer St from Cushing Way to Water St (FLAG)'

TRIP = '533'
DEPART_FROM = 'South Station'
ARRIVE_AT = 'West Natick'

# DEPART_FROM = 'South Station'
# ARRIVE_AT = 'West Natick'

def print_journey(trip: Trip):
    route_type = trip.route_type

    # if subway, ferry, or similar
    if route_type in [0, 1, 4]:
        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", trip.route_long_name)
        _LOGGER.info("Type: %s", trip.route_description)
        _LOGGER.info("Color: %s", trip.route_color)
        _LOGGER.info("**********")
        _LOGGER.info("Direction: %s to %s", trip.direction, trip.destination)
        _LOGGER.info("Destination: %s", trip.headsign)
        _LOGGER.info("Duration: %s", trip.duration)
        _LOGGER.info("**********")
        _LOGGER.info("Departure Station: %s", trip.departure_stop_name)
        _LOGGER.info("Departure Platform: %s", trip.departure_platform_name)
        _LOGGER.info("Departure Time: %s", trip.departure_time)
        _LOGGER.info("Departure Delay: %s", trip.departure_delay)
        _LOGGER.info("Departure Time To: %s", trip.departure_time_to)
        _LOGGER.info("Departure Status: %s", trip.departure_status)
        _LOGGER.info("**********")
        _LOGGER.info("Arrival Station: %s", trip.arrival_stop_name)
        _LOGGER.info("Arrival Platform: %s", trip.arrival_platform_name)
        _LOGGER.info("Arrival Time: %s", trip.arrival_time)
        _LOGGER.info("Arrival Delay: %s", trip.arrival_delay)
        _LOGGER.info("Arrival Time To: %s", trip.arrival_time_to)
        _LOGGER.info("Arrival Status: %s", trip.arrival_status)
        _LOGGER.info("**********")
        for alert in trip.mbta_alerts:
            _LOGGER.info("$$$$$$$$$$$$$")
            _LOGGER.info("Alert header: %s", alert.header)
            _LOGGER.info("$$$$$$$$$$$$$")
    elif route_type == 2:
        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", trip.route_long_name)
        _LOGGER.info("Type: %s", trip.route_description)
        _LOGGER.info("Color: %s", trip.route_color)
        _LOGGER.info("Train Number: %s", trip.mbta_trip.name)
        _LOGGER.info("**********")
        _LOGGER.info("Direction: %s to %s", trip.direction, trip.destination)
        _LOGGER.info("Destination: %s", trip.headsign)
        _LOGGER.info("Duration: %s", trip.duration)
        _LOGGER.info("**********")
        _LOGGER.info("Departure Station: %s", trip.departure_stop_name)
        _LOGGER.info("Departure Platform: %s", trip.departure_platform_name)
        _LOGGER.info("Departure Time: %s", trip.departure_time)
        _LOGGER.info("Departure Delay: %s", trip.departure_delay)
        _LOGGER.info("Departure Time To: %s", trip.departure_time_to)
        _LOGGER.info("Departure Status: %s", trip.departure_status)
        _LOGGER.info("**********")
        _LOGGER.info("Arrival Station: %s", trip.arrival_stop_name)
        _LOGGER.info("Arrival Platform: %s", trip.arrival_platform_name)
        _LOGGER.info("Arrival Time: %s", trip.arrival_time)
        _LOGGER.info("Arrival Delay: %s", trip.arrival_delay)
        _LOGGER.info("Arrival Time To: %s", trip.arrival_time_to)
        _LOGGER.info("Arrival Status: %s", trip.arrival_status)
        _LOGGER.info("**********")
        for alert in trip.mbta_alerts:
            _LOGGER.info("$$$$$$$$$$$$$")
            _LOGGER.info("Alert header: %s", alert.header)
            _LOGGER.info("$$$$$$$$$$$$$")

    # if bus
    elif route_type == 3:
        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", trip.route_short_name)
        _LOGGER.info("Type: %s", trip.route_description)
        _LOGGER.info("Color: %s", trip.route_color)
        _LOGGER.info("**********")
        _LOGGER.info("Direction: %s to %s", trip.direction, trip.destination)
        _LOGGER.info("Destination: %s", trip.headsign)
        _LOGGER.info("Duration: %s", trip.duration)
        _LOGGER.info("**********")
        _LOGGER.info("Departure Stop: %s", trip.departure_stop_name)
        _LOGGER.info("Departure Time: %s", trip.departure_time)
        _LOGGER.info("Departure Delay: %s", trip.departure_delay)
        _LOGGER.info("Departure Time To: %s", trip.departure_time_to)
        _LOGGER.info("Departure Status: %s", trip.departure_status)
        _LOGGER.info("**********")
        _LOGGER.info("Arrival Stop: %s", trip.arrival_stop_name)
        _LOGGER.info("Arrival Time: %s", trip.arrival_time)
        _LOGGER.info("Arrival Delay: %s", trip.arrival_delay)
        _LOGGER.info("Arrival Time To: %s", trip.arrival_time_to)
        _LOGGER.info("Arrival Status: %s", trip.arrival_status)
        _LOGGER.info("**********")
        for alert in trip.mbta_alerts:
            _LOGGER.info("$$$$$$$$$$$$$")
            _LOGGER.info("Alert header: %s", alert.header)
            _LOGGER.info("$$$$$$$$$$$$$")
    else:
        _LOGGER.error("Unknown route type: %s", route_type)

                
                
async def main():
    #async with aiohttp.ClientSession() as session:
        
        #try:
            # trip_hadler = TripHandler(depart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, trip_name=TRIP, api_key=API_KEY, session=session, logger=_LOGGER)
            
            # await trip_hadler.async_init()
            
            # trips = await trip_hadler.update()
            
            # for trip in trips:
            #    print_journey(trip)
    # async with aiohttp.ClientSession() as session: 
        # async with MBTAClient(session=session) as mbta_client:
        #     stop_handler = await MBTAStopHandler.create(stop_name=ARRIVE_AT, client=mbta_client)
        #     await stop_handler.update()
            
        cache_manger = MBTACacheManager()
        async with MBTAClient(cache_manager=cache_manger,api_key=API_KEY) as mbta_client:
            trips_handler = await TripsHandler.create(depart_from_name="Copley", arrive_at_name="Park Street", max_trips=MAX_JOURNEYS, mbta_client=mbta_client)
            trips3: list[Trip] = await trips_handler.update()
            trips_handler2 = await TripsHandler.create(depart_from_name="South Station", arrive_at_name="West Natick", max_trips=MAX_JOURNEYS, mbta_client=mbta_client)
            trips4: list[Trip] = await trips_handler2.update() 
            train_trip_handler = await TrainTripHandler.create(depart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, train_name=TRIP, mbta_client=mbta_client)               
            trip: list[Trip] = await train_trip_handler.update()
            train_trip_handler2 = await TrainTripHandler.create(depart_from_name=ARRIVE_AT, arrive_at_name=DEPART_FROM, train_name='530', mbta_client=mbta_client)               
            trip2: list[Trip] = await train_trip_handler2.update()
            # for tri1 in trips1:
            #     print_journey(tri1)   
            # for tri2 in trips2:
            #     print_journey(tri2)  
            # for tri in trip:
            #     print_journey(tri)
            # trips1: list[Trip] = await trips_handler.update()
            # trips2: list[Trip] = await trips_handler2.update()      
            # trip: list[Trip] = await train_trip_handler.update()
            # trips1: list[Trip] = await trips_handler.update()
            # trips2: list[Trip] = await trips_handler2.update()      
            # trip: list[Trip] = await train_trip_handler.update()
            # trips1: list[Trip] = await trips_handler.update()
            # trips2: list[Trip] = await trips_handler2.update()      
            # trip: list[Trip] = await train_trip_handler.update()
            # trips1: list[Trip] = await trips_handler.update()
            # trips2: list[Trip] = await trips_handler2.update()      
            # trip: list[Trip] = await train_trip_handler.update()
            # for tri1 in trips1:
            #     print_journey(tri1)   
            # for tri2 in trips2:
            #     print_journey(tri2) 
            # for tri3 in trips3:
            #     print_journey(tri3)
            # for tri4 in trips4:
            #     print_journey(tri4)
            for tri1 in trip:
                print_journey(tri1)
            for tri2 in trip2:
                print_journey(tri2)
            #stops_handler = await MBTAStopsHandler.create(stop_name=DEPART_FROM, client=mbta_client)
            
        cache_manger.cleanup()        
            
    # cache_manger = CacheManager()     
    # async with JourneysHandler(epart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, api_key=API_KEY,session=None, cache_manager=cache_manger,logger=None) as journeys_handler :
    #     try:

    #         journeys  = await journeys_handler.update()
    #         _LOGGER.info("**********")   
    #         journeys  = await journeys_handler.update()
            
    #         for journey in journeys:
    #             print_journey(journey)
    #     except Exception as e:
    #         _LOGGER.error(f"Error : {e}")
    
    # _LOGGER.info("##########")           
    # async with JourneysHandler(depart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, max_journeys=MAX_JOURNEYS, api_key=API_KEY,session=None, cache_manager=cache_manger,logger=None) as journeys_handler :
    #     try:

    #         journeys  = await journeys_handler.update()
    #         _LOGGER.info("**********")   
    #         journeys  = await journeys_handler.update()
            
# Run the main function
import asyncio
asyncio.run(main())
