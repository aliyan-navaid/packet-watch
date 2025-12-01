from app.utils import QueryMessage
from app.modules.metrics import Metrics
from app.modules.alert import Alerts
from app.modules.gui import GUI
from app.modules.storage import Storage
import re

class Chatbot:
    def __init__(self, metrics: Metrics, alerts: Alerts, gui: GUI, storage: Storage):
        self.metrics = metrics
        self.alerts = alerts
        self.gui = gui
        self.storage = storage

    def processQuery(self, query: QueryMessage):
        text = query.message.lower()
        response = "I'm not sure how to answer that."

        if "latency" in text:
            snapshot = self.metrics.get()
            response = f"The average latency is {snapshot.average_latency:.2f} ms."
        elif "alert" in text:
            snapshot = self.metrics.get()
            anomalies = [k for k, v in snapshot.anomaly_indicators.items() if v]
            if anomalies:
                response = f"Yes, there are active anomalies: {', '.join(anomalies)}."
            else:
                response = "No active alerts at the moment."
        elif "packet" in text and "rate" in text:
            snapshot = self.metrics.get()
            response = f"Current packet rate is {snapshot.packet_rate:.2f} packets/sec."
        elif "total" in text and "packet" in text:
            snapshot = self.metrics.get()
            response = f"Total packets captured: {snapshot.total_packets_captured}."
        elif "throughput" in text:
            snapshot = self.metrics.get()
            response = f"Current throughput is {snapshot.throughput_bps/1_000_000:.2f} Mbps."
        elif "show packet" in text or "get packet" in text:
            match = re.search(r"packet\s+(\d+)", text)
            if match:
                try:
                    idx = int(match.group(1))

                    if 0 <= idx < len(self.storage):
                        pkt = self.storage[idx]
                        response = (f"Packet #{idx}:\n"
                                    f"Time: {pkt.timestamp}\n"
                                    f"Src: {pkt.src_ip}:{pkt.src_port} -> Dst: {pkt.dst_ip}:{pkt.dst_port}\n"
                                    f"Proto: {pkt.highest_layer} | Len: {pkt.captured_length}\n"
                                    f"Summary: {pkt.summary}")
                    else:
                        response = f"Packet #{idx} not found. Storage has {len(self.storage)} packets."
                except Exception as e:
                    response = f"Error retrieving packet: {e}"
            else:
                response = "Please specify a packet number, e.g., 'show packet 5'."
        
        self.gui.display_chat_response(response)
