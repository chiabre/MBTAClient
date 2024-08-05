import aiohttp
from mbta_auth import Auth
from mbta import MBTA
from mbta_route import MBTAroute
from mbta_journeys import MBTAjourneys

from datetime import datetime
from typing import Dict, List, Any

API_KEY = None

# ROUTE = 'Framingham/Worcester Line'
# DEPART_FROM = 'West Natick'
# ARRIVE_AT = 'South Station'

# ROUTE = 'Red Line'
# DEPART_FROM = 'Andrew'
# ARRIVE_AT = 'South Station'

# ROUTE = 'Wakefield Avenue & Truman Parkway - Ashmont Station'
# DEPART_FROM = 'Dorchester Ave @ Valley Rd'
# ARRIVE_AT = 'River St @ Standard St'

DEPART_FROM = 'Back Bay'
ARRIVE_AT = 'Huntington Ave @ Opera Pl'
ROUTE = 'Forest Hills Station - Back Bay Station'

# DEPART_FROM = 'Charlestown Navy Yard'
# ARRIVE_AT = 'Long Wharf (South)'
# ROUTE = 'Charlestown Ferry'

async def main():
    async with aiohttp.ClientSession() as session:
        
        if API_KEY:
            auth = Auth(session, api_key=API_KEY)
        else:
            auth = Auth(session)
            
        mbta_client = MBTA(auth)

        # Get all routes
        routes = await mbta_client.list_routes()

        # Get route_id from ROUTE
        route_id = next((route.route_id for route in routes if route.route_long_name == ROUTE), None)
        
        if not route_id:
            print(f"Route '{ROUTE}' not found.")
            return
        
        # Get route details for route_id
        route = await mbta_client.get_route(route_id)
        
        # init journey
        journeys = MBTAjourneys(mbta_client=mbta_client, route=route, depart_from=DEPART_FROM, arrive_at=ARRIVE_AT)
        
        # populate journey
        await journeys.populate()
                  
        print(journeys)


# Run the main function
import asyncio
asyncio.run(main())
