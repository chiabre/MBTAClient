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
    """Base class for object stores without size limits."""
    _lock: RLock = RLock()  # Thread-safe lock

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
        """Add an object to the registry."""
        with cls._lock:
            # Use the object's `id` attribute for storage
            obj_id = getattr(obj, 'id', None)
            if not obj_id:
                raise ValueError("Object must have an 'id' attribute.")

            # Move existing item to the end or add a new one
            cls._registry[obj_id] = obj
            cls._registry.move_to_end(obj_id)

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


class MBTASizedObjStore(MBTABaseObjStore[T]):
    """Subclass of MBTABaseObjStore with a limit on the number of objects."""
    _max_items: int = 512  # Default maximum size of the registry

    @classmethod
    def configure_max_items(cls, max_items: int) -> None:
        """Configure the maximum size of the registry."""
        with cls._lock:
            cls._max_items = max_items

    @classmethod
    def store(cls, obj: T) -> None:
        """Add an object to the registry, enforcing size limits."""
        with cls._lock:
            obj_id = getattr(obj, 'id', None)
            if not obj_id:
                raise ValueError("Object must have an 'id' attribute.")

            if obj_id in cls._registry:
                # Move existing item to the end
                cls._registry.move_to_end(obj_id)
            elif len(cls._registry) >= cls._max_items:
                # Evict the oldest item if size limit is reached
                cls._registry.popitem(last=False)

            # Add or update the item
            cls._registry[obj_id] = obj


# Object Stores (choose base class based on the need)
class MBTARouteObjStore(MBTABaseObjStore[MBTARoute]):
    """Uncapped registry for MBTA Route objects."""
    _registry: OrderedDict[str, MBTARoute] = OrderedDict()


class MBTAStopObjStore(MBTABaseObjStore[MBTAStop]):
    """Uncapped registry for MBTA Stop objects."""
    _registry: OrderedDict[str, MBTAStop] = OrderedDict()


class MBTATripObjStore(MBTASizedObjStore[MBTATrip]):
    """Capped registry for MBTA Trip objects."""
    _registry: OrderedDict[str, MBTATrip] = OrderedDict()


class MBTAVehicleObjStore(MBTASizedObjStore[MBTAVehicle]):
    """Capped registry for MBTA Vehicle objects."""
    _registry: OrderedDict[str, MBTAVehicle] = OrderedDict()


class MBTAAlertObjStore(MBTASizedObjStore[MBTAAlert]):
    """Capped registry for MBTA Alert objects."""
    _registry: OrderedDict[str, MBTAAlert] = OrderedDict()
