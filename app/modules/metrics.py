import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from app.utils import MetricsSnapshot
from app.utils.interfaces import Subject, Observer
from app.utils.events import Event, PacketCapturedEvent, MetricsUpdatedEvent
from app.utils.models import Packet

from app.config import MetricConfig


@dataclass
class _WindowEntry:
    timestamp: float
    length: int
    is_syn: bool
    is_rst: bool


@dataclass
class _PacketFeatures:
    timestamp: float
    length: int
    protocol: str
    src_ip: Optional[str]
    dst_ip: Optional[str]
    src_port: Optional[int]
    dst_port: Optional[int]
    is_syn: bool
    is_rst: bool
    is_error: bool
    tcp_flags: Dict[str, bool]


class Metrics(Subject, Observer):
    def __init__(self) -> None:
        self._metrics: MetricsSnapshot = MetricsSnapshot()
        self.observers: List[Observer] = []

        # recent window bookkeeping
        self._recent_packets: Deque[_WindowEntry] = deque()
        self._window_packet_count: int = 0
        self._window_byte_count: int = 0
        self._window_syn_count: int = 0
        self._window_rst_count: int = 0

        # distribution maps
        self._protocol_counts: Dict[str, int] = defaultdict(int)
        self._dst_port_counts: Dict[int, int] = defaultdict(int)
        self._src_ip_bytes: Dict[str, int] = defaultdict(int)
        self._dst_ip_bytes: Dict[str, int] = defaultdict(int)
        self._tcp_flag_counts: Dict[str, int] = defaultdict(int)

    def update(self, event: Event) -> None:
        if not isinstance(event, PacketCapturedEvent):
            raise TypeError("Metrics only accepts PacketCapturedEvent")

        packet: Packet = event.payload  # type: ignore[assignment]
        features = self._extract_packet_features(packet)
        self._ingest_packet(features)
        self._refresh_snapshot_views()

        self.notify_observers(MetricsUpdatedEvent(self.get()))
        #print(self._metrics)

    def subscribe(self, observer: Observer):
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self, event: Event):
        for observer in list(self.observers):
            observer.update(event)

    def get(self) -> MetricsSnapshot:
        """
        Get Metrics
        """
        return self._metrics

    def _ingest_packet(self, features: _PacketFeatures) -> None:
        length = max(features.length, 0)
        self._metrics.total_packets_captured += 1
        self._metrics.total_data_transfered += length

        # running avg packet size
        self._metrics.average_packet_size += (
            length - self._metrics.average_packet_size
        ) / max(self._metrics.total_packets_captured, 1)

        # min/max packet length
        if length > self._metrics.max_packet_size:
            self._metrics.max_packet_size = length
        if self._metrics.min_packet_size is None or (
            length and length < self._metrics.min_packet_size
        ):
            self._metrics.min_packet_size = length

        # latency based on sniff timestamp
        self._update_latency(features.timestamp)

        # distributions for alerting/analytics
        self._protocol_counts[features.protocol] += 1
        if features.dst_port is not None:
            self._dst_port_counts[features.dst_port] += 1
        if features.src_ip:
            self._src_ip_bytes[features.src_ip] += length
        if features.dst_ip:
            self._dst_ip_bytes[features.dst_ip] += length

        # tcp flags breakdown for anomalies
        self._update_tcp_flag_counts(features.tcp_flags)

        # sliding window for rates
        self._update_window(features)

        if features.is_error:
            self._metrics.error_packets += 1

    def _update_latency(self, timestamp: float) -> None:
        if timestamp is None:
            timestamp = time.time()

        if self._metrics.last_timestamp is not None:
            delta_ms = (timestamp - self._metrics.last_timestamp) * 1000.0
            self._metrics.latency_count += 1
            self._metrics.average_latency += (
                delta_ms - self._metrics.average_latency
            ) / max(self._metrics.latency_count, 1)

        self._metrics.last_timestamp = timestamp

    def _update_tcp_flag_counts(self, tcp_flags: Dict[str, bool]) -> None:
        for flag_name, is_set in tcp_flags.items():
            if is_set:
                self._tcp_flag_counts[flag_name] += 1

    def _update_window(self, features: _PacketFeatures) -> None:
        entry = _WindowEntry(
            timestamp=features.timestamp,
            length=features.length,
            is_syn=features.is_syn,
            is_rst=features.is_rst,
        )

        self._recent_packets.append(entry)
        self._window_packet_count += 1
        self._window_byte_count += features.length
        if features.is_syn:
            self._window_syn_count += 1
        if features.is_rst:
            self._window_rst_count += 1

        cutoff = features.timestamp - MetricConfig.WINDOW_SECONDS
        while self._recent_packets and self._recent_packets[0].timestamp < cutoff:
            old = self._recent_packets.popleft()
            self._window_packet_count -= 1
            self._window_byte_count -= old.length
            if old.is_syn:
                self._window_syn_count -= 1
            if old.is_rst:
                self._window_rst_count -= 1

        window_duration = MetricConfig.WINDOW_SECONDS
        self._metrics.packet_rate = self._window_packet_count / window_duration
        self._metrics.peak_packet_rate = max(
            self._metrics.peak_packet_rate, self._metrics.packet_rate
        )

        throughput_bytes_per_sec = self._window_byte_count / window_duration
        self._metrics.throughput = throughput_bytes_per_sec
        self._metrics.throughput_bps = throughput_bytes_per_sec * 8

        self._metrics.syn_rate = self._window_syn_count / window_duration
        self._metrics.rst_rate = self._window_rst_count / window_duration

    def _refresh_snapshot_views(self) -> None:
        self._metrics.protocol_breakdown = dict(
            sorted(
                self._protocol_counts.items(), key=lambda item: item[1], reverse=True
            )
        )
        self._metrics.top_source_ips = self._top_items(
            self._src_ip_bytes.items(), MetricConfig.TOP_N_TALKERS
        )
        self._metrics.top_destination_ips = self._top_items(
            self._dst_ip_bytes.items(), MetricConfig.TOP_N_TALKERS
        )
        self._metrics.top_destination_ports = self._top_items(
            self._dst_port_counts.items(), MetricConfig.TOP_N_TALKERS
        )

        self._metrics.unique_source_ips = len(self._src_ip_bytes)
        self._metrics.unique_destination_ips = len(self._dst_ip_bytes)
        self._metrics.tcp_flag_counts = dict(self._tcp_flag_counts)

        self._metrics.anomaly_indicators = {
            "high_packet_rate": self._metrics.packet_rate
            > MetricConfig.HIGH_PACKET_RATE_THRESHOLD,
            "high_throughput": self._metrics.throughput_bps
            > MetricConfig.HIGH_THROUGHPUT_BPS,
            "syn_flood_suspected": self._metrics.syn_rate
            > MetricConfig.HIGH_SYN_RATE_THRESHOLD,
            "rst_spike": self._metrics.rst_rate > MetricConfig.HIGH_RST_RATE_THRESHOLD,
        }

    @staticmethod
    def _top_items(items: Iterable[Tuple], top_n: int) -> List[Tuple]:
        return sorted(items, key=lambda item: item[1], reverse=True)[:top_n]

    def _extract_packet_features(self, packet: Packet) -> _PacketFeatures:
        timestamp = self._extract_timestamp(packet)
        length = self._safe_int(
            getattr(packet, "captured_length", None) or getattr(packet, "length", None)
        )

        if length is None or length == 0:
            frame = getattr(packet, "frame_info", None)
            if frame is not None:
                length = self._safe_int(getattr(frame, "len", None))

        if length is None:
            length = 0

        protocol = (
            getattr(packet, "highest_layer", None)
            or getattr(packet, "transport_layer", None)
            or "UNKNOWN"
        )

        protocol = protocol.upper()

        src_ip = self._extract_ip(packet, "src")
        dst_ip = self._extract_ip(packet, "dst")
        src_port, dst_port = self._extract_ports(packet)
        tcp_flags = self._extract_tcp_flags(packet)
        is_syn = tcp_flags.get("SYN", False)
        is_rst = tcp_flags.get("RST", False)
        is_error = self._is_error_packet(packet, protocol)

        return _PacketFeatures(
            timestamp=timestamp,
            length=length,
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=src_port,
            dst_port=dst_port,
            is_syn=is_syn,
            is_rst=is_rst,
            is_error=is_error,
            tcp_flags=tcp_flags,
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
        return time.time()

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

    def _extract_ports(self, packet: Packet) -> Tuple[Optional[int], Optional[int]]:
        for layer_name in ("tcp", "udp"):
            layer = getattr(packet, layer_name, None)

            if layer is None:
                continue

            src = self._safe_int(
                getattr(layer, "srcport", None)
                or getattr(layer, "sport", None)
                or getattr(layer, "src_port", None),
                default=None,
            )

            dst = self._safe_int(
                getattr(layer, "dstport", None)
                or getattr(layer, "dport", None)
                or getattr(layer, "dst_port", None),
                default=None,
            )

            return src, dst

        return None, None

    @staticmethod
    def _extract_tcp_flags(packet: Packet) -> Dict[str, bool]:
        flags: Dict[str, bool] = {}
        tcp_layer = getattr(packet, "tcp", None)

        if tcp_layer is None:
            return flags

        for flag in ("syn", "ack", "fin", "rst", "psh", "urg"):
            attr = f"flags_{flag}"
            value = getattr(tcp_layer, attr, None)
            flags[flag.upper()] = str(value) == "1"

        return flags

    @staticmethod
    def _is_error_packet(packet: Packet, protocol: str) -> bool:
        if protocol == "MALFORMED":
            return True

        if getattr(packet, "malformed", None) is not None:
            return True

        if getattr(packet, "expert_message", None):
            return True

        return False

    @staticmethod
    def _safe_int(value, default: Optional[int] = 0) -> Optional[int]:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def __str__(self) -> str:
        return (
            "Metrics("
            f"packets={self._metrics.total_packets_captured}, "
            f"bytes={self._metrics.total_data_transfered}, "
            f"avg_size={self._metrics.average_packet_size:.2f} bytes, "
            f"pps={self._metrics.packet_rate:.2f}, "
            f"throughput={self._metrics.throughput_bps/1_000_000:.2f} Mbps, "
            f"syn_rate={self._metrics.syn_rate:.2f} pps, "
            f"alerts={self._metrics.anomaly_indicators}"
            ")"
        )
