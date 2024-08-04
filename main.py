import aiohttp
from mbta_auth import Auth
from mbta import MBTA
from mbta_schedule import MBTAschedule
from mbta_route import MBTAroute
from mbta_journey import MBTAjourney, MBTAjourneyStop
from mbta_utils import *
from datetime import datetime
from typing import Dict, List, Any

API_KEY = None

# ROUTE = 'Framingham/Worcester Line'
# DEPART_FROM = 'West Natick'
# ARRIVE_AT = 'South Station'

ROUTE = 'Red Line'
DEPART_FROM = 'Andrew'
ARRIVE_AT = 'South Station'

# ROUTE = 'Wakefield Avenue & Truman Parkway - Ashmont Station'
# DEPART_FROM = 'Dorchester Ave @ Valley Rd'
# ARRIVE_AT = 'River St @ Standard St'

# DEPART_FROM = 'Back Bay'
# ARRIVE_AT = 'Huntington Ave @ Opera Pl'
# ROUTE = 'Forest Hills Station - Back Bay Station'

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
                
        # Get stops for route_id
        params = {'filter[route]': route_id}
        route_stops = await mbta_client.list_stops(params)
        
        # Get stops id for DEPART_FROM and ARRIVE_AT
        depart_from_stop_id = next((stop.stop_id for stop in route_stops if stop.stop_name == DEPART_FROM), None)
        arrive_at_stop_id = next((stop.stop_id for stop in route_stops if stop.stop_name == ARRIVE_AT), None)
        
        if not depart_from_stop_id or not arrive_at_stop_id:
            print(f"Stops '{DEPART_FROM}' or '{ARRIVE_AT}' not found.")
            return
        
        # Prepare schedule req param: all the schedules for route_id and DEPART_FROM and ARRIVE_AT stops. schedules of today, from now  
        
        now = datetime.now()
        
        params = {
            'filter[route]': route_id,
            'filter[stop]': f"{depart_from_stop_id},{arrive_at_stop_id}",
            'filter[min_time]': now.strftime('%H:%M'),
            'filter[date]': now.strftime('%Y-%m-%d'),
            'sort': 'departure_time'
        }
        
        # Get schedules 
        schedules = await mbta_client.list_schedules(params)
        
        # Initialize journeys
        journeys = {}
        
        # Initialize journey_stop_ids
        journey_stop_ids = {
            DEPART_FROM: [depart_from_stop_id],
            ARRIVE_AT: [arrive_at_stop_id]
        }

        # Process schedules
        for schedule in schedules:

            # add the current schedule to the journey
            journeys = add_journey(journeys, schedule, route )
            
            # update the journey_stop_ids with the current schedule stop
            await update_journey_stop_ids(schedule.stop_id,journey_stop_ids, DEPART_FROM, ARRIVE_AT, mbta_client)

            # get the stop name corresponding to the schedule.stop_id
            stop_name = DEPART_FROM if schedule.stop_id in journey_stop_ids[DEPART_FROM] else ARRIVE_AT
            
            # add the stop to the current journey
            journeys[schedule.trip_id].add_stop(stop_name, MBTAjourneyStop(
                stop_id=schedule.stop_id,
                arrival_time=schedule.arrival_time,
                departure_time=schedule.departure_time,
                stop_sequence=schedule.stop_sequence
            ))

        # Prepare prediction req param: all the predictions for route_id and DEPART_FROM and ARRIVE_AT stops       
        params = {
            'filter[route]': route_id,
            'filter[stop]': f"{depart_from_stop_id},{arrive_at_stop_id}",
            'sort': 'departure_time'
        }
        
        # Get predictions
        predictions = await mbta_client.list_predictions(params)
        
        for prediction in predictions:
            
            # if the trip update is not of type CANCELLED
            if prediction.schedule_relationship != 'CANCELLED':

                # add the current prediction to the journey
                journeys = add_journey(journeys, prediction, route )
                    
                # update the journey_stop_ids with the current prediction stop
                await update_journey_stop_ids(prediction.stop_id,journey_stop_ids, DEPART_FROM, ARRIVE_AT, mbta_client)

                # get the stop_name corresponding to the schedule.stop_id
                stop_name = DEPART_FROM if prediction.stop_id in journey_stop_ids[DEPART_FROM] else ARRIVE_AT
                
                # get the stop corresponding to the stop_name
                stop = journeys[prediction.trip_id].get_stop_by_name(stop_name)
                
                # if stop is none (= not in the journey)
                if stop == None:
                    # add the stop
                    journeys[prediction.trip_id].add_stop(stop_name, MBTAjourneyStop(
                        stop_id=prediction.stop_id,
                        arrival_time=prediction.arrival_time,
                        departure_time=prediction.departure_time,
                        stop_sequence=prediction.stop_sequence
                    ))
                else:
                    # update the existing stop
                    stop.update_stop(prediction.stop_id, prediction.arrival_time,prediction.arrival_uncertainty, prediction.departure_time,prediction.departure_uncertainty )
            else:
                # if thre trip is in the journeys
                if prediction.trip_id in journeys:
                    # delete it
                    del journeys[prediction.trip_id]
                

        # process the journeys to remove the ones in the wrong direction and sort the journey by departure time
        journeys = process_journeys(journeys, DEPART_FROM, ARRIVE_AT )
        
        print(journeys)


# Run the main function
import asyncio
asyncio.run(main())
