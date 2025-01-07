# mock_data.py

VALID_ROUTE_RESPONSE_DATA = {
    "id": "Red",
    "type": "route",
    "attributes": {
        "color": "DA291C",
        "description": "Rapid Transit",
        "direction_destinations": ["Ashmont/Braintree", "Alewife"],
        "direction_names": ["South", "North"],
        "fare_class": "Rapid Transit",
        "long_name": "Red Line",
        "short_name": "",
        "sort_order": 10010,
        "text_color": "FFFFFF",
        "type": 1
    },
    "relationships": {
        "agency": {"data": {"id": "1", "type": "agency"}},
        "line": {"data": {"id": "line-Red", "type": "line"}}
    },
    "links": {"self": "/routes/Red"}
}

VALID_TRIP_RESPONSE_DATA = {
    "id": "66715083",
    "type": "trip",
    "attributes": {
        "bikes_allowed": 0,
        "block_id": "S931_-1",
        "direction_id": 1,
        "headsign": "Alewife",
        "name": "",
        "revenue": "REVENUE",
        "wheelchair_accessible": 1
    },
    "relationships": {
        "route": {"data": {"id": "Red", "type": "route"}},
        "route_pattern": {"data": {"id": "route-pattern-1", "type": "route_pattern"}},
        "service": {"data": {"id": "RTL12025-hms15011-Weekday-01", "type": "service"}},
        "shape": {"data": {"id": "931_0010", "type": "shape"}}
    },
    "links": {"self": "/trips/66715083"}
}

VALID_STOP_RESPONSE_DATA = {
    "attributes": {
        "address": None,
        "at_street": "Spalding Street",
        "description": None,
        "latitude": 42.303741,
        "location_type": 0,
        "longitude": -71.114635,
        "municipality": "Boston",
        "name": "South St @ Spalding St",
        "on_street": "South Street",
        "platform_code": None,
        "platform_name": None,
        "vehicle_type": 3,
        "wheelchair_boarding": 1
    },
    "id": "1936",
    "links": {
        "self": "/stops/1936"
    },
    "relationships": {
        "facilities": {
            "links": {
                "related": "/facilities/?filter[stop]=1936"
            }
        },
        "parent_station": {
            "data": None
        },
        "zone": {
            "data": {
                "id": "LocalBus",
                "type": "zone"
            }
        }
    },
    "type": "stop"
}

VALID_SCHEDULE_RESPONSE_DATA = {
    "attributes": {
        "arrival_time": None,
        "departure_time": "2025-01-07T05:15:00-05:00",
        "direction_id": 1,
        "drop_off_type": 1,
        "pickup_type": 0,
        "stop_headsign": None,
        "stop_sequence": 50,
        "timepoint": False
    },
    "id": "schedule-66715083-70094-50",
    "relationships": {
        "route": {
            "data": {
                "id": "Red",
                "type": "route"
            }
        },
        "stop": {
            "data": {
                "id": "70094",
                "type": "stop"
            }
        },
        "trip": {
            "data": {
                "id": "66715083",
                "type": "trip"
            }
        }
    },
    "type": "schedule"
}

VALID_PREDICTION_RESPONSE_DATA = {
    "attributes": {
        "arrival_time": None,
        "arrival_uncertainty": None,
        "departure_time": "2025-01-07T16:43:00-05:00",
        "departure_uncertainty": 360,
        "direction_id": 1,
        "last_trip": False,
        "revenue": "REVENUE",
        "schedule_relationship": None,
        "status": None,
        "stop_sequence": 1,
        "update_type": "REVERSE_TRIP"
    },
    "id": "prediction-66715348-70105-1-Red",
    "relationships": {
        "route": {
            "data": {
                "id": "Red",
                "type": "route"
            }
        },
        "stop": {
            "data": {
                "id": "70105",
                "type": "stop"
            }
        },
        "trip": {
            "data": {
                "id": "66715348",
                "type": "trip"
            }
        },
        "vehicle": {
            "data": {
                "id": "R-5480A18A",
                "type": "vehicle"
            }
        }
    },
    "type": "prediction"
}

VALID_ALERT_RESPONSE_DATA = {
    "attributes": {
        "active_period": [
            {
                "end": None,
                "start": "2021-01-31T13:29:00-05:00"
            }
        ],
        "cause": "CONSTRUCTION",
        "created_at": "2021-01-31T13:29:21-05:00",
        "description": (
            "Beginning November 29, the parking lot across from the station will close. "
            "Please use the garage or adjacent surface lot as an alternative. The Quincy Adams Garage "
            "drop-off and pick-up location will remain at its location within Level 1B. The garage will be "
            "PayByPhone / PayByPlate with no need to pay to exit. More information on how to pay for parking "
            "is available at mbta.com/parking. Affected routes: Red Line"
        ),
        "duration_certainty": "UNKNOWN",
        "effect": "STATION_ISSUE",
        "header": (
            "The Quincy Adams parking garage has re-opened with most parking spaces available. "
            "Customers can access the garage via the Route 3 off ramp exit as well as the Burgin Parkway entrance."
        ),
        "image": None,
        "image_alternative_text": None,
        "informed_entity": [
            {
                "stop": "70103",
                "route_type": 1,
                "route": "Red",
                "activities": ["BOARD"]
            },
            {
                "stop": "70104",
                "route_type": 1,
                "route": "Red",
                "activities": ["BOARD"]
            },
            {
                "stop": "place-qamnl",
                "route_type": 1,
                "route": "Red",
                "activities": ["BOARD"]
            }
        ],
        "lifecycle": "ONGOING",
        "service_effect": "Change at Quincy Adams",
        "severity": 1,
        "short_header": "The Quincy Adams parking garage has re-opened with most parking spaces available.",
        "timeframe": "ongoing",
        "updated_at": "2023-10-18T15:09:21-04:00",
        "url": None
    },
    "id": "382310",
    "links": {
        "self": "/alerts/382310"
    },
    "type": "alert"
}


