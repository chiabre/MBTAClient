
import logging
from mbtaclient.handlers.timetable_handler import TimetableHandler
from mbtaclient.handlers.trains_handler import TrainsHandler
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

TRIP = '509'
DEPART_FROM = 'South Station'
ARRIVE_AT = 'West Natick'

# DEPART_FROM = 'South Station'
# ARRIVE_AT = 'West Natick'
              
                
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
            handlerA = await TimetableHandler.create(stop_name="South Station", route_ids=['Red'], mbta_client=mbta_client, departures=True)
            AA = await handlerA.update()
            AA = await handlerA.update()
            AA = await handlerA.update()
            for A in AA:
                print(f"{A.route_name} | {A.headsign} | {A.departure_time} | {A.departure_status} | {A.departure_delay} ")
            print("$$$$$$$$$$$$$$$")
            print("$$$$$$$$$$$$$$$")
            handlerA = await TimetableHandler.create(stop_name="South Station", route_ids=None, mbta_client=mbta_client, departures=False)
            AA = await handlerA.update()
            AA = await handlerA.update()
            AA = await handlerA.update()
            for A in AA:
                print(f"{A.route_name} | {A.headsign} | {A.arrival_time} | {A.arrival_status} | {A.arrival_delay} ")
            print("$$$$$$$$$$$$$$$")
            print("$$$$$$$$$$$$$$$")
            handlerB = await TrainsHandler.create(departure_stop_name=DEPART_FROM, arrival_stop_name=ARRIVE_AT, trips_names=[TRIP], mbta_client=mbta_client)
            BB = await handlerB.update()
            BB = await handlerB.update()
            BB = await handlerB.update()
            for B in BB:
                print(f"{B.name} | {B.route_name} | {B.headsign} | {B.departure_time} | {B.departure_status} | {B.departure_delay} | {B.arrival_time} | {B.arrival_status} | {B.arrival_delay}")
            print("$$$$$$$$$$$$$$$")
            print("$$$$$$$$$$$$$$$")
            handlerC = await TripsHandler.create(departure_stop_name="Back Bay", arrival_stop_name="South Station", max_trips=MAX_JOURNEYS, mbta_client=mbta_client)
            CC = await handlerC.update()
            CC = await handlerC.update()
            CC = await handlerC.update()
            for C in CC:
                print(f"{C.route_name} | {C.headsign} | {C.departure_time} | {C.departure_status} | {C.departure_delay} | {C.arrival_time} | {C.arrival_status} | {C.arrival_delay}")   
 
            # trips = await trips_handler.update()
            # trips = await trips_handler.update()
            # trips_handler = await TripsHandler.create(depart_from_name="Copley", arrive_at_name="Park Street", max_trips=MAX_JOURNEYS, mbta_client=mbta_client)
            # trips3: list[Trip] = await trips_handler.update()
            # trips_handler2 = await TripsHandler.create(depart_from_name="South Station", arrive_at_name="West Natick", max_trips=MAX_JOURNEYS, mbta_client=mbta_client)
            # trips4: list[Trip] = await trips_handler2.update() 
            # train_trip_handler = await TrainTripHandler.create(depart_from_name=DEPART_FROM, arrive_at_name=, train_name=TRIP, mbta_client=mbta_client)               
            # trip: list[Trip] = await train_trip_handler.update()
            # train_trip_handler2 = await TrainTripHandler.create(depart_from_name=ARRIVE_AT, arrive_at_name=DEPART_FROM, train_name='586', mbta_client=mbta_client)               
            # trip2: list[Trip] = await train_trip_handler2.update()
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
            # for tri1 in trips:
            #     print_journey(tri1)
            # for tri2 in trip2:
            #     print_journey(tri2)
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
