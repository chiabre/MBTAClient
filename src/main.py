import aiohttp
from trip_handler import TripHandler
from journeys_handler import JourneysHandler


API_KEY = ''
MAX_JOURNEYS = 5


# DEPART_FROM = 'South Station'
# ARRIVE_AT = 'Wellesley Square'


# DEPART_FROM = 'Wellesley Square'
# ARRIVE_AT = 'South Station'


DEPART_FROM = 'South Station'
ARRIVE_AT = 'Braintree'


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

TRIP = '518'
# DEPART_FROM = 'Wellesley Square'
# ARRIVE_AT = 'South Station'


def print_journey(journey):
    route_type = journey.get_route_type()

    # if subway or ferry
    if route_type == 0 or route_type == 1 or route_type == 4:
        
        print("###########")
        print() 
        print("Line:", journey.get_route_long_name())  
        print("Type:", journey.get_route_description())        
        print("Color:", journey.get_route_color())
        print() 
        print("Direction:", journey.get_trip_direction()+" to "+journey.get_trip_destination())
        print("Destination:", journey.get_trip_headsign())
        print() 
        # Print departure information
        print("Departure Station:", journey.get_stop_name('departure'))
        print("Departure Platform:", journey.get_platform_name('departure'))
        print("Departure Time:", journey.get_stop_time('departure'))
        print("Departure Delay:", journey.get_stop_delay('departure'))
        print("Departure Time To:", journey.get_stop_time_to('departure'))
        print() 
        # Print arrival information
        print("Departure Station:", journey.get_stop_name('arrival'))
        print("Departure Platform:", journey.get_platform_name('arrival'))
        print("Departure Time:", journey.get_stop_time('arrival'))
        print("Departure Delay:", journey.get_stop_delay('arrival'))
        print("Departure Time To:", journey.get_stop_time_to('arrival'))
        print() 
        for j in range(len(journey.alerts)):
            print("Alert:" , journey.get_alert_header(j))
            print() 
    
    # if train
    elif route_type == 2:    
                                            
        print("###########")
        print() 
        print("Line:", journey.get_route_long_name())  
        print("Type:", journey.get_route_description())        
        print("Color:", journey.get_route_color())
        print() 
        print("Train Number:", journey.get_trip_name())
        print("Direction:", journey.get_trip_direction()+" to "+journey.get_trip_destination())
        print("Destination:", journey.get_trip_headsign())
        print() 
        # Print departure information
        print("Departure Station:", journey.get_stop_name('departure'))
        print("Departure Platform:", journey.get_platform_name('departure'))
        print("Departure Time:", journey.get_stop_time('departure'))
        print("Departure Delay:", journey.get_stop_delay('departure'))
        print("Departure Time To:", journey.get_stop_time_to('departure'))
        print() 
        # Print arrival information
        print("Departure Station:", journey.get_stop_name('arrival'))
        print("Departure Platform:", journey.get_platform_name('arrival'))
        print("Departure Time:", journey.get_stop_time('arrival'))
        print("Departure Delay:", journey.get_stop_delay('arrival'))
        print("Departure Time To:", journey.get_stop_time_to('arrival'))
        print() 
            
        for j in range(len(journey.alerts)):
            print("Alert:" , journey.get_alert_header(j))
            print() 
    
    #if bus
    elif route_type == 3:

        print("###########")
        print() 
        print("Line:", journey.get_route_short_name())  
        print("Type:", journey.get_route_description())        
        print("Color:", journey.get_route_color())
        print() 
        print("Direction:", journey.get_trip_direction()+" to "+journey.get_trip_destination())
        print("Destination:", journey.get_trip_headsign())
       # Print departure information
        print("Departure Stop:", journey.get_stop_name('departure'))
        print("Departure Time:", journey.get_stop_time('departure'))
        print("Departure Delay:", journey.get_stop_delay('departure'))
        print("Departure Time To:", journey.get_stop_time_to('departure'))
        print() 
        # Print arrival information
        print("Departure Stop:", journey.get_stop_name('arrival'))
        print("Departure Time:", journey.get_stop_time('arrival'))
        print("Departure Delay:", journey.get_stop_delay('arrival'))
        print("Departure Time To:", journey.get_stop_time_to('arrival'))
        print()  
        for j in range(len(journey.alerts)):
            print("Alert:" , journey.get_alert_header(j))
            print() 
                        
    else:
        
            print('ARGH!') 
                
                
async def main():
    async with aiohttp.ClientSession() as session:
        
        trip_hadler = TripHandler(session, API_KEY, DEPART_FROM, ARRIVE_AT, TRIP)
        
        trip = await trip_hadler.fetch_trip()
        
        print_journey(trip)
        
        journeys_handler = JourneysHandler(session, API_KEY, DEPART_FROM, ARRIVE_AT, MAX_JOURNEYS)
        
        journeys  = await journeys_handler.fetch_journeys()
        
        for journey in journeys:
            print_journey(journey)

            
                                
# Run the main function
import asyncio
asyncio.run(main())
