from typing import Dict, List, Any, Union
from datetime import datetime
from mbta_route import MBTAroute
from mbta_schedule import MBTAschedule
from mbta_prediction import MBTAprediction
from mbta_journey import MBTAjourney, MBTAjourneyStop
from mbta import MBTA

def add_journey(journeys: Dict[str, MBTAjourney], data: Union[MBTAschedule, MBTAprediction], route: MBTAroute) -> Dict[str, MBTAjourney]:
    trip_id = data.trip_id
    direction_id = data.direction_id
    direction_name = route.route_direction_names[direction_id]
    direction_destination = route.route_direction_destinations[direction_id]
    headsign = getattr(data, 'stop_headsign', None) if isinstance(data, MBTAschedule) else None
    
    if trip_id not in journeys:
        journeys[trip_id] = MBTAjourney(
            direction_name=direction_name,
            direction_destination=direction_destination,
            headsign=headsign
        )
    return journeys


def process_journeys(journeys: Dict[str, MBTAjourney], depart_from: str, arrive_at: str) -> Dict[str, MBTAjourney]:
    processed_journeys = {}

    for trip_id, journey in journeys.items():
        stops_name = journey.get_stops_names()
        stops_count = journey.count_stops()
        # if there are 2 stops the journey has to start yet. If the first stop is not the depart from, the journey is in the wrong direction and has to be removed
        if stops_count == 2 and stops_name[0] != depart_from:
            continue
        # if there is 1 stops the journey already started. If the first/only stop is not the arrive at, the journey is in the wrong direction and has to be removed
        elif stops_count == 1 and stops_name[0] != arrive_at:
            continue
        # all the other journeys are valid
        processed_journeys[trip_id] = journey

    sorted_journeys = dict(
        sorted(
            processed_journeys.items(),
            key=lambda item: get_first_stop_departure_time(item[1])
        )
    )
    return sorted_journeys

def get_first_stop_departure_time(journey: MBTAjourney) -> datetime:
    first_stop = journey.get_stops_list()[0]
    return first_stop.get_time()


async def update_journey_stop_ids(stop_id: str, journey_stop_ids: Dict, depart_from: str, arrive_at: str, mbta_client: MBTA ) -> datetime:

            # if the  stop_id (child_stop_id) is not tracked in the journey_stop_ids
            if stop_id not in journey_stop_ids[depart_from] and stop_id not in journey_stop_ids[arrive_at]:
                # extract the stop that the schedule stop_id (child_stop_id) belongs to
                stop = await mbta_client.get_stop(stop_id)
                # add the schedule stop_id (child_stop_id) to the correct journey_stop_ids[stop_name]
                journey_stop_ids[stop.stop_name].append(stop_id)