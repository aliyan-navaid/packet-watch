from app.utils.models import MetricsSnapshot, AlertInfo, QueryMessage
from pyshark.packet.packet import Packet
from typing import Union

class Event:
    def __init__(self, name: str, payload: Union[Packet, QueryMessage, MetricsSnapshot, AlertInfo]):
        self.name = name
        self.payload = payload

class PacketCapturedEvent(Event):
    def __init__(self, packet_data: Packet):
        super().__init__("packet_captured", packet_data)

class MetricsUpdatedEvent(Event):
    def __init__(self, metrics_snapshot: MetricsSnapshot):
        super().__init__("metrics_updated", metrics_snapshot)

class AlertGeneratedEvent(Event):
    def __init__(self, alert_info: AlertInfo):
        super().__init__("alert_generated", alert_info)

class QueryRaised(Event):
    def __init__(self, query: QueryMessage):
        super().__init__("query_raised", query)

class StartCaptureEvent(Event):
    def __init__(self, config):
        super().__init__("start_capture", config)

class StopCaptureEvent(Event):
    def __init__(self):
        super().__init__("stop_capture", None)