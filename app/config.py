from dataclasses import dataclass, field
import os

@dataclass
class SystemConfig:
    # Update this path if Wireshark in different location
    TSHARK_PATH = r"C:\Applications\Wireshark\tshark.exe"

@dataclass
class MetricConfig:
    WINDOW_SECONDS = 10.0
    TOP_N_TALKERS = 5
    HIGH_PACKET_RATE_THRESHOLD = 500.0            # packets/sec
    HIGH_THROUGHPUT_BPS = 5 * 1024 * 1024         # 5 Mbps
    HIGH_SYN_RATE_THRESHOLD = 150.0               # syn packets/sec
    HIGH_RST_RATE_THRESHOLD = 100.0               # rst packets/sec