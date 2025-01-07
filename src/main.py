import aiohttp
import logging
from mbtaclient.trip_handler import TripHandler
from mbtaclient.journeys_handler import JourneysHandler
from mbtaclient.journey import Journey

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,  # Set the logging level to INFO
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

API_KEY = ''
MAX_JOURNEYS = 1

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

# TRIP = '536'
# DEPART_FROM = 'Wellesley Square'
# ARRIVE_AT = 'South Station'

DEPART_FROM = 'South Station'
ARRIVE_AT = 'West Natick'

def print_journey(journey: Journey):
    route_type = journey.get_route_type()

    # if subway or ferry
    if route_type in [0, 1, 4]:
        
        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", journey.get_route_long_name())  
        _LOGGER.info("Type: %s", journey.get_route_description())        
        _LOGGER.info("Color: %s", journey.get_route_color())
        _LOGGER.info("**********")       
        _LOGGER.info("Direction: %s to %s", journey.get_trip_direction(), journey.get_trip_destination())
        _LOGGER.info("Destination: %s", journey.get_trip_headsign())
        _LOGGER.info("Duration: %s", journey.get_trip_duration())
        _LOGGER.info("**********")   
        _LOGGER.info("Departure Station: %s", journey.get_stop_name('departure'))
        _LOGGER.info("Departure Platform: %s", journey.get_platform_name('departure'))
        _LOGGER.info("Departure Time: %s", journey.get_stop_time('departure'))
        _LOGGER.info("Departure Delay: %s", journey.get_stop_delay('departure'))
        _LOGGER.info("Departure Time To: %s", journey.get_stop_time_to('departure'))
        _LOGGER.info("%s", journey.get_stop_status('departure'))
        _LOGGER.info("**********")   
        _LOGGER.info("Arrival Station: %s", journey.get_stop_name('arrival'))
        _LOGGER.info("Arrival Platform: %s", journey.get_platform_name('arrival'))
        _LOGGER.info("Arrival Time: %s", journey.get_stop_time('arrival'))
        _LOGGER.info("Arrival Delay: %s", journey.get_stop_delay('arrival'))
        _LOGGER.info("Arrival Time To: %s", journey.get_stop_time_to('arrival'))
        _LOGGER.info("%s", journey.get_stop_status('arrival'))
        _LOGGER.info("**********")   
        for j in range(len(journey.alerts)):
            _LOGGER.info("Alert: %s", journey.get_alert_header(j))
        
    # if train
    elif route_type == 2:    
        
        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", journey.get_route_long_name())  
        _LOGGER.info("Type: %s", journey.get_route_description())        
        _LOGGER.info("Color: %s", journey.get_route_color())
        _LOGGER.info("Train Number: %s", journey.get_trip_name())
        _LOGGER.info("**********")   
        _LOGGER.info("Direction: %s to %s", journey.get_trip_direction(), journey.get_trip_destination())
        _LOGGER.info("Destination: %s", journey.get_trip_headsign())
        _LOGGER.info("Duration: %s", journey.get_trip_duration())
        _LOGGER.info("**********")   
        _LOGGER.info("Departure Station: %s", journey.get_stop_name('departure'))
        _LOGGER.info("Departure Platform: %s", journey.get_platform_name('departure'))
        _LOGGER.info("Departure Time: %s", journey.get_stop_time('departure'))
        _LOGGER.info("Departure Delay: %s", journey.get_stop_delay('departure'))
        _LOGGER.info("Departure Time To: %s", journey.get_stop_time_to('departure'))
        _LOGGER.info("%s", journey.get_stop_status('departure'))
        _LOGGER.info("**********")   
        _LOGGER.info("Arrival Station: %s", journey.get_stop_name('arrival'))
        _LOGGER.info("Arrival Platform: %s", journey.get_platform_name('arrival'))
        _LOGGER.info("Arrival Time: %s", journey.get_stop_time('arrival'))
        _LOGGER.info("Arrival Delay: %s", journey.get_stop_delay('arrival'))
        _LOGGER.info("Arrival Time To: %s", journey.get_stop_time_to('arrival'))
        _LOGGER.info("%s", journey.get_stop_status('arrival'))
        _LOGGER.info("**********")   
        for j in range(len(journey.alerts)):
            _LOGGER.info("Alert: %s", journey.get_alert_header(j))
        
    # if bus
    elif route_type == 3:

        _LOGGER.info("###########")
        _LOGGER.info("Line: %s", journey.get_route_short_name())  
        _LOGGER.info("Type: %s", journey.get_route_description())        
        _LOGGER.info("Color: %s", journey.get_route_color())
        _LOGGER.info("**********")   
        _LOGGER.info("Direction: %s to %s", journey.get_trip_direction(), journey.get_trip_destination())
        _LOGGER.info("Destination: %s", journey.get_trip_headsign())
        _LOGGER.info("Duration: %s", journey.get_trip_duration())
        _LOGGER.info("**********")   
        _LOGGER.info("Departure Stop: %s", journey.get_stop_name('departure'))
        _LOGGER.info("Departure Time: %s", journey.get_stop_time('departure'))
        _LOGGER.info("Departure Delay: %s", journey.get_stop_delay('departure'))
        _LOGGER.info("Departure Time To: %s", journey.get_stop_time_to('departure'))
        _LOGGER.info("%s", journey.get_stop_status('departure'))
        _LOGGER.info("**********")   
        _LOGGER.info("Arrival Stop: %s", journey.get_stop_name('arrival'))
        _LOGGER.info("Arrival Time: %s", journey.get_stop_time('arrival'))
        _LOGGER.info("Arrival Delay: %s", journey.get_stop_delay('arrival'))
        _LOGGER.info("Arrival Time To: %s", journey.get_stop_time_to('arrival'))
        _LOGGER.info("%s", journey.get_stop_status('arrival'))
        _LOGGER.info("**********")   
        for j in range(len(journey.alerts)):
            _LOGGER.info("Alert: %s", journey.get_alert_header(j))

    else:
        _LOGGER.error('ARGH!')
                
                
async def main():
    async with aiohttp.ClientSession() as session:
        
        try:
            # trip_hadler = TripHandler(depart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, trip_name=TRIP, api_key=API_KEY, session=session, logger=_LOGGER)
            
            # await trip_hadler.async_init()
            
            # trips = await trip_hadler.update()
            
            # for trip in trips:
            #    print_journey(trip)
            
            journeys_handler = JourneysHandler(depart_from_name=DEPART_FROM, arrive_at_name=ARRIVE_AT, max_journeys=MAX_JOURNEYS, api_key=API_KEY,session=session, logger=_LOGGER)
            
            await journeys_handler.async_init()
            
            journeys  = await journeys_handler.update()
            journeys  = await journeys_handler.update()
            
            for journey in journeys:
                print_journey(journey)
            
        except Exception as e:
            _LOGGER.error(f"Error : {e}")
                                
# Run the main function
import asyncio
asyncio.run(main())
