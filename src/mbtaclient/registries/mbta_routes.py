from typing import Optional

from ..models.mbta_route import MBTARoute

class MBTARoutesRegistry:
    """A registry to manage and share Route instances."""
    _mbta_routes = {}

    @classmethod
    def get_mbta_route(cls, id: str) -> Optional[MBTARoute]:
        """Retrieve a Route instance by its ID."""
        return cls._mbta_routes.get(id)

    @classmethod
    def register_mbta_route(cls, mbta_route: MBTARoute) -> None:
        """Register a new Route instance."""
        cls._mbta_routes[mbta_route.id] = mbta_route

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all Route instances from the registry."""
        cls._mbta_routes.clear()