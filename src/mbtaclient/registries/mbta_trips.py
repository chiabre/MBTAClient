from typing import Optional

from ..models.mbta_trip import MBTATrip

class MBTATripsRegistry:
    """A registry to manage and share Trip instances."""
    _mbta_trips = {}

    @classmethod
    def get_mbta_trip(cls, id: str) -> Optional[MBTATrip]:
        """Retrieve a Trip instance by its ID."""
        return cls._mbta_trips.get(id)

    @classmethod
    def register_mbta_trip(cls, mbta_trip: MBTATrip) -> None:
        """Register a new Trip instance."""
        cls._mbta_trips[mbta_trip.id] = mbta_trip

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all Trip instances from the registry."""
        cls._mbta_trips.clear()
