from typing import List, Optional, Iterator, Any, overload, Iterable, Union
from collections.abc import MutableSequence

from app.utils.interfaces import Observer
from app.utils.models import Packet
from app.utils.events import Event, PacketCapturedEvent

class Storage(Observer, MutableSequence):
    """
        NOT THREAD SAFE
    """

    def __init__(self, limit: Optional[int] = None):
        self._packets: List[Packet] = []
        if limit is not None and limit < 0:
            raise ValueError("limit must be greater than 0")
        self._limit: Optional[int] = limit

    def update(self, event: Event):
        if not isinstance(event, PacketCapturedEvent):
            raise TypeError("Storage only accepts PacketCapturedEvent")

        if self._limit is not None and len(self._packets) >= self._limit:
            raise OverflowError("Packet storage capacity reached")

        packet: Packet = event.payload  # type: ignore
        self._packets.append(packet)

    def update_limit(self, limit: int):
        if limit < 0:
            raise ValueError("limit must be greater than 0")
        
        self._limit = limit
        if limit is None:
            return

        if len(self._packets) > limit:
            self._packets = self._packets[:limit]

    def clear(self):
        self._packets.clear()

    @overload
    def __getitem__(self, index: int) -> Packet: 
        ...

    @overload
    def __getitem__(self, index: slice) -> List[Packet]: 
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[Packet, List[Packet]]:
        return self._packets[index]

    @overload
    def __setitem__(self, index: int, value: Packet) -> None: 
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Packet]) -> None: 
        ...

    def __setitem__(self, index: Union[int, slice], value: Union[Packet, Iterable[Packet]]) -> None:
        if isinstance(index, int):
            if not isinstance(value, Packet):
                raise TypeError("Only Packet instances can be assigned to an int index")
            self._packets[index] = value
        else:
            if not isinstance(value, Iterable):
                raise TypeError("Slice assignment requires an iterable of Packet instances")

            vals = list(value)
            for v in vals:
                if not isinstance(v, Packet):
                    raise TypeError("All items assigned to slice must be Packet instances")
            self._packets[index] = vals

    def __delitem__(self, index: Union[int, slice]) -> None:
        del self._packets[index]

    def __len__(self) -> int:
        return len(self._packets)

    def insert(self, index: int, value: Packet) -> None:
        if not isinstance(value, Packet):
            raise TypeError("Only Packet instances can be inserted")
        if self._limit is not None and len(self._packets) >= self._limit:
            raise OverflowError("Packet storage capacity reached")
        self._packets.insert(index, value)

    def __iter__(self) -> Iterator[Packet]:
        return iter(self._packets)

    def __repr__(self):
        return f"Storage(limit={self._limit}, packets={self._packets})"