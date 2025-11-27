from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

from pyshark.packet.packet import Packet

@dataclass
class PacketData:
    # use pyshark.packet.packet
    pass
@dataclass
class MetricsSnapshot:
    total_packets_captured: int = 0
    total_data_transfered: int = 0
    average_packet_size: float = 0.0
    max_packet_size: int = 0
    min_packet_size: Optional[int] = None

    # latency bookkeeping (milliseconds)
    average_latency: float = 0.0
    latency_count: int = 0
    last_timestamp: Optional[float] = None

    packet_rate: float = 0.0  # current packets/sec window
    peak_packet_rate: float = 0.0
    throughput: float = 0.0  # (bytes/sec)
    throughput_bps: float = 0.0

    protocol_breakdown: Dict[str, int] = field(default_factory=dict)
    top_source_ips: List[Tuple[str, int]] = field(default_factory=list)
    top_destination_ips: List[Tuple[str, int]] = field(default_factory=list)
    top_destination_ports: List[Tuple[str, int]] = field(default_factory=list)
    unique_source_ips: int = 0
    unique_destination_ips: int = 0

    tcp_flag_counts: Dict[str, int] = field(default_factory=dict)
    syn_rate: float = 0.0
    rst_rate: float = 0.0
    error_packets: int = 0
    anomaly_indicators: Dict[str, bool] = field(default_factory=dict)

@dataclass
class AlertInfo:
    alert_type: str
    message: str
    severity: str
    timestamp: float

@dataclass
class QueryMessage:
    message: str

@dataclass
class CaptureConfig:
    protocol: str
    port: int
    interface: Optional[str] = None