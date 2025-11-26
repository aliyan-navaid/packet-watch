from dataclasses import dataclass

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