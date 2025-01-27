from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

from ..models.mbta_alert import MBTAAlert

@dataclass
class MBTAAlertsRegistry:
    """A registry to manage and share Route instances."""
    _max_items: int = 100  # Set the maximum number of alerts to store
    _mbta_alerts: OrderedDict[str, MBTAAlert] = OrderedDict()

    def get_mbta_alert(self, id: str) -> Optional[MBTAAlert]:
        """Retrieve a Route instance by its ID."""
        return self._mbta_alerts.get(id)

    def register_mbta_alert(self, mbta_alert: MBTAAlert) -> None:
        """Register a new Route instance."""
        if len(self._mbta_alerts) >= self._max_items:
            self._mbta_alerts.popitem(last=False)  # Remove the oldest item
        self._mbta_alerts[mbta_alert.id] = mbta_alert

    def clear_registry(self) -> None:
        """Clear all Route instances from the registry."""
        self._mbta_alerts.clear()