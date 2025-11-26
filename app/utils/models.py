from dataclasses import dataclass
from typing import Optional

@dataclass
class PacketData:
    src_ip: str
    dst_ip: str
    protocol: str
    size: int
    timestamp: float

@dataclass
class MetricsSnapshot:
    total_packets: int
    avg_packet_size: float
    throughput: float

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