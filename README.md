# MBTAclient

**MBTAclient** is a Python client library for interacting with the Massachusetts Bay Transportation Authority (MBTA) API. This library provides access to MBTA data, including routes, predictions, schedules, and more.

## Features

- Structured objects to retrieve and access information about:
    - MBTA Routes
    - MBTA Stops
    - MBTA Trips
    - MBTA Schedules
    - MBTA Predictions
    - MBTA Alerts
- Two handlers to simplify the retrieval and access to journey information, including near-live scheduling, stops, and alerts:
    - **`journeys_handler`**: Provides a list of the next N (N=`max_journeys`) journeys from a departure stop (`depart_from_name`) to an arrival stop (`arrive_at_name`).
    - **`trip_handler`**: Provides a single journey on a given commuter rail trip (`trip`) from a departure stop (`depart_from_name`) to an arrival stop (`arrive_at_name`).
- Easily integrates with Home Assistant or other Python-based systems.


## Contributing

Contributions are welcome! If you would like to contribute to this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
