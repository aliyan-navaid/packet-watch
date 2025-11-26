from app.utils import PacketData, MetricsSnapshot, AlertInfo
from typing import Union

class Event:
    def __init__(self, name: str, payload: Union[PacketData, MetricsSnapshot, AlertInfo]):
        self.name = name
        self.payload = payload

class PacketCapturedEvent(Event):
    def __init__(self, packet_data: PacketData):
        super().__init__("packet_captured", packet_data)

class MetricsUpdatedEvent(Event):
    def __init__(self, metrics_snapshot: MetricsSnapshot):
        super().__init__("metrics_updated", metrics_snapshot)

class AlertGeneratedEvent(Event):
    def __init__(self, alert_info: AlertInfo):
        super().__init__("alert_generated", alert_info)