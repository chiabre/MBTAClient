from typing import Optional

from ..models.mbta_stop import MBTAStop

class MBTAStopsRegistry:
    """A registry to manage and share MBTAStop instances."""
    _mbta_stops = {}

    @classmethod
    def get_mbta_stop(cls, id: str) -> Optional['MBTAStop']:
        return cls._mbta_stops.get(id)

    @classmethod
    def register_mbta_stop(cls, mbta_stop: 'MBTAStop') -> None:
        cls._mbta_stops[mbta_stop.id] = mbta_stop
        
    @classmethod
    def clear_registry(cls) -> None:
        """Clear all Trip instances from the registry."""
        cls._mbta_stops.clear()