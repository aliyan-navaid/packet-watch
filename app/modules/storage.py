import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from app.utils.interfaces import Observer
from app.utils.models import Packet
from app.utils.events import Event, PacketCapturedEvent


@dataclass
class StoredPacket:
    timestamp: float
    captured_length: int
    highest_layer: str
    summary: str
    src_ip: Optional[str]
    dst_ip: Optional[str]
    src_port: Optional[int]
    dst_port: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredPacket":
        return cls(
            timestamp=float(data.get("timestamp", 0.0)),
            captured_length=int(data.get("captured_length", 0)),
            highest_layer=str(data.get("highest_layer", "")),
            summary=str(data.get("summary", "")),
            src_ip=data.get("src_ip"),
            dst_ip=data.get("dst_ip"),
            src_port=data.get("src_port"),
            dst_port=data.get("dst_port"),
        )

    @classmethod
    def from_packet(cls, packet: Packet) -> "StoredPacket":
        timestamp = cls._extract_timestamp(packet)
        captured_length = cls._extract_length(packet)
        highest_layer = getattr(packet, "highest_layer", "") or ""
        summary = getattr(packet, "summary", None)
        if not summary:
            summary = str(packet)
        src_ip = cls._extract_ip(packet, "src")
        dst_ip = cls._extract_ip(packet, "dst")
        src_port, dst_port = cls._extract_ports(packet)
        return cls(
            timestamp=timestamp,
            captured_length=captured_length,
            highest_layer=highest_layer,
            summary=str(summary),
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
        )

    @staticmethod
    def _extract_timestamp(packet: Packet) -> float:
        for attr in ("sniff_timestamp", "sniff_time", "timestamp"):
            value = getattr(packet, attr, None)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return 0.0

    @staticmethod
    def _extract_length(packet: Packet) -> int:
        for attr in ("captured_length", "length"):
            value = getattr(packet, attr, None)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        frame = getattr(packet, "frame_info", None)
        if frame is not None:
            value = getattr(frame, "len", None)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    pass
        return 0

    @staticmethod
    def _extract_ip(packet: Packet, direction: str) -> Optional[str]:
        attr = "src" if direction == "src" else "dst"
        for layer_name in ("ip", "ipv6"):
            layer = getattr(packet, layer_name, None)
            if layer is None:
                continue
            value = getattr(layer, attr, None)
            if value:
                return value
        return None

    @staticmethod
    def _extract_ports(packet: Packet) -> Tuple[Optional[int], Optional[int]]:
        for layer_name in ("tcp", "udp"):
            layer = getattr(packet, layer_name, None)
            if layer is None:
                continue
            src = StoredPacket._to_int(
                getattr(layer, "srcport", None)
                or getattr(layer, "sport", None)
                or getattr(layer, "src_port", None)
            )
            dst = StoredPacket._to_int(
                getattr(layer, "dstport", None)
                or getattr(layer, "dport", None)
                or getattr(layer, "dst_port", None)
            )
            return src, dst
        return None, None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class Storage(Observer):
    """
    NOT THREAD SAFE
    """

    def __init__(self, file_path: Optional[str] = None, capacity: Optional[int] = None):
        """
        :param file_path: provide a path to load packets from - default to empty list
        :param capacity: total capacity of the storage
        """
        self._packets: List[StoredPacket] = []
        if capacity is not None and capacity < 0:
            raise ValueError("limit must be greater than 0")
        self._capacity: Optional[int] = capacity
        self._file_path: Optional[Path] = Path(file_path) if file_path else None
        if file_path:
            self._load_from_file(file_path)

    def update(self, event: Event):
        if not isinstance(event, PacketCapturedEvent):
            raise TypeError("Storage only accepts PacketCapturedEvent")

        if self._capacity is not None and len(self._packets) >= self._capacity:
            raise OverflowError("Packet storage capacity reached")

        packet: Packet = event.payload  # type: ignore
        self._packets.append(StoredPacket.from_packet(packet))

    def update_limit(self, capacity: int):
        """
        Modify the capacity of storage
        :param capacity: new capacity
        """
        if capacity < 0:
            raise ValueError("capacity must be greater than 0")

        self._capacity = capacity
        if capacity is None:
            return

        if len(self._packets) > capacity:
            self._packets = self._packets[:capacity]

    def materialize(self, file_path: Optional[str] = None) -> None:
        """Write stored packets to disk as JSON.
        :param file_path: file path to save the materialized storage to
        """
        target = Path(file_path) if file_path else self._file_path
        if target is None:
            raise ValueError("materialize requires a file path")
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = [packet.to_dict() for packet in self._packets]
        target.write_text(json.dumps(encoded, indent=2), encoding="utf-8")
        self._file_path = target

    def _load_from_file(self, file_path: str) -> None:
        target = Path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"storage file not found: {file_path}")
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("storage file must contain a JSON array")
        for record in data:
            stored = StoredPacket.from_dict(record)
            if self._capacity is not None and len(self._packets) >= self._capacity:
                break
            self._packets.append(stored)

    def clear(self):
        """
        Clears the storage, in-memory only, doesn't clear from disk
        """
        self._packets.clear()

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[StoredPacket, List[StoredPacket]]:
        return self._packets[index]

    def __setitem__(
        self,
        index: Union[int, slice],
        value: Union[StoredPacket, Iterable[StoredPacket]],
    ) -> None:
        if isinstance(index, int):
            if not isinstance(value, StoredPacket):
                raise TypeError("Only Packet instances can be assigned to an int index")
            self._packets[index] = value
            return

        if not isinstance(value, Iterable):
            raise TypeError("Slice assignment requires an iterable of Packet instances")

        iterable_values = list(value)
        for v in iterable_values:
            if not isinstance(v, StoredPacket):
                raise TypeError("All items assigned to slice must be Packet instances")
        self._packets[index] = iterable_values

    def __delitem__(self, index: Union[int, slice]) -> None:
        del self._packets[index]

    def __len__(self) -> int:
        return len(self._packets)

    def insert(self, index: int, value: StoredPacket) -> None:
        if not isinstance(value, StoredPacket):
            raise TypeError("Only Packet instances can be inserted")
        if self._capacity is not None and len(self._packets) >= self._capacity:
            raise OverflowError("Packet storage capacity reached")
        self._packets.insert(index, value)

    def __iter__(self) -> Iterator[StoredPacket]:
        return iter(self._packets)

    def __repr__(self):
        return f"Storage(limit={self._capacity}, packets={self._packets})"
