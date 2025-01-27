from collections import OrderedDict
from threading import RLock
from typing import Generic, TypeVar, Optional

from .models.mbta_alert import MBTAAlert
from .models.mbta_route import MBTARoute
from .models.mbta_stop import MBTAStop
from .models.mbta_trip import MBTATrip
from .models.mbta_vehicle import MBTAVehicle

T = TypeVar("T")  # Generic type for objects stored in the object store


class MBTABaseObjStore(Generic[T]):
    """Class-based base object store to manage and cache MBTA objects."""
    _max_items: int = 512  # Maximum size of the registry
    _lock: RLock = RLock()  # Thread-safe lock

    @classmethod
    def configure_max_items(cls, max_items: int) -> None:
        """Configure the maximum size of the registry."""
        with cls._lock:
            cls._max_items = max_items

    @classmethod
    def get_by_id(cls, id: str) -> Optional[T]:
        """Retrieve an object by its ID and mark it as recently used."""
        with cls._lock:
            obj = cls._registry.get(id)
            if obj is not None:
                # Mark the object as recently used
                cls._registry.move_to_end(id)
            return obj

    @classmethod
    def store(cls, obj: T) -> None:
        """Add an object to the registry, with size management."""
        with cls._lock:
            # Use the object's `id` attribute for storage
            obj_id = getattr(obj, 'id', None)
            if not obj_id:
                raise ValueError(f"Object must have an 'id' attribute.")

            if obj_id in cls._registry:
                # Move the existing item to the end to mark it as recently used
                cls._registry.move_to_end(obj_id)
            elif len(cls._registry) >= cls._max_items:
                # Evict the oldest item
                cls._registry.popitem(last=False)
            # Add or update the item
            cls._registry[obj_id] = obj

    @classmethod
    def clear_store(cls) -> None:
        """Clear all objects from the registry."""
        with cls._lock:
            cls._registry.clear()

    @classmethod
    def __len__(cls) -> int:
        """Return the current number of items in the registry."""
        with cls._lock:
            return len(cls._registry)


class MBTARouteObjStore(MBTABaseObjStore[MBTARoute]):
    """Class-based registry specifically for MBTA Route objects."""
    _registry: OrderedDict[str, MBTARoute] = OrderedDict()


class MBTAStopObjStore(MBTABaseObjStore[MBTAStop]):
    """Class-based registry specifically for MBTA Stop objects."""
    _registry: OrderedDict[str, MBTAStop] = OrderedDict()


class MBTATripObjStore(MBTABaseObjStore[MBTATrip]):
    """Class-based registry specifically for MBTA Trip objects."""
    _registry: OrderedDict[str, MBTATrip] = OrderedDict()


class MBTAVehicleObjStore(MBTABaseObjStore[MBTAVehicle]):
    """Class-based registry specifically for MBTA Vehicle objects."""
    _registry: OrderedDict[str, MBTAVehicle] = OrderedDict()


class MBTAAlertObjStore(MBTABaseObjStore[MBTAAlert]):
    """Class-based registry specifically for MBTA Alert objects."""
    _registry: OrderedDict[str, MBTAAlert] = OrderedDict()
