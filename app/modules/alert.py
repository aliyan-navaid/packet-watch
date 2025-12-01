from typing import List
from datetime import datetime

from app.utils.interfaces import Subject, Observer
from app.utils.events import Event, AlertGeneratedEvent
from app.utils.models import MetricsSnapshot, AlertInfo

class Alerts(Subject, Observer):
    def __init__(self):
        self.observers: List[Observer] = []
        # Define thresholds for alerts
        self.thresholds = {
            'high_latency': 100.0,      # milliseconds
            'high_packet_rate': 1000.0, # packets per second
            'high_error_rate': 50.0     # error packets count
        }

    def update(self, event: Event):
        if event.name == "metrics_updated" and isinstance(event.payload, MetricsSnapshot):
            self.check_anomalies(event.payload)

    def check_anomalies(self, metrics: MetricsSnapshot):
        # Check Latency
        if metrics.average_latency > self.thresholds['high_latency']:
            self.create_alert(
                alert_type="High Latency",
                message=f"Average latency is high: {metrics.average_latency:.2f} ms",
                severity="Warning"
            )

        # Check Packet Rate
        if metrics.packet_rate > self.thresholds['high_packet_rate']:
            self.create_alert(
                alert_type="High Traffic",
                message=f"Packet rate spike detected: {metrics.packet_rate:.2f} pkts/sec",
                severity="Critical"
            )
            
        # Check Error Packets
        if metrics.error_packets > self.thresholds['high_error_rate']:
             self.create_alert(
                alert_type="Network Errors",
                message=f"High number of error packets detected: {metrics.error_packets}",
                severity="High"
            )

    def create_alert(self, alert_type: str, message: str, severity: str):
        alert_info = AlertInfo(
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=datetime.now()
        )
        event = AlertGeneratedEvent(alert_info)
        self.notify_observers(event)

    def subscribe(self, observer: Observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self, event: Event):
        for observer in self.observers:
            observer.update(event)
