import queue
from typing import List, Optional, Dict

import customtkinter as ctk
import psutil

from app.utils.events import Event, QueryRaised, StartCaptureEvent, StopCaptureEvent
from app.utils.interfaces import Observer, Subject
from app.utils.models import AlertInfo, CaptureConfig, MetricsSnapshot, QueryMessage

class GUI(Observer, Subject):
    def __init__(self):
        self.event_queue = queue.Queue()
        self.observers: List[Observer] = []
        self.window: Optional[ctk.CTk] = None

        # Fonts
        self.font_sans = "Open Sans"
        self.font_sans_alt = "Noto Sans"
        self.font_mono = "Roboto Mono"

        self.font_title = (self.font_sans, 18, "bold")
        self.font_section = (self.font_sans, 14, "bold")
        self.font_label = (self.font_sans, 12)
        self.font_label_mono = (self.font_mono, 12)
        self.font_value_big = (self.font_mono, 28, "bold")
        self.font_value = (self.font_mono, 14)
        self.font_log = (self.font_mono, 11)
        self.font_chat = (self.font_sans, 11)
        self.font_chat_input = (self.font_sans, 12)
        self.font_button = (self.font_sans, 12, "bold")
        
        # UI Elements
        self.lbl_latency: Optional[ctk.CTkLabel] = None
        self.lbl_packet_rate: Optional[ctk.CTkLabel] = None
        self.lbl_total_packets: Optional[ctk.CTkLabel] = None
        self.txt_alerts: Optional[ctk.CTkTextbox] = None
        self.txt_chat_history: Optional[ctk.CTkTextbox] = None
        self.entry_chat: Optional[ctk.CTkEntry] = None
        
        # Capture Controls
        self.option_protocol: Optional[ctk.CTkOptionMenu] = None
        self.entry_port: Optional[ctk.CTkEntry] = None
        self.option_interface: Optional[ctk.CTkOptionMenu] = None
        self.btn_start: Optional[ctk.CTkButton] = None
        self.btn_stop: Optional[ctk.CTkButton] = None

        # Map pretty interface labels -> real device names
        self.interface_map: Dict[str, str] = self._probe_interfaces()

    def _probe_interfaces(self) -> Dict[str, str]:
        """Return mapping: human label -> real interface name (active only)."""
        labels: Dict[str, str] = {}
        try:
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
        except Exception:
            return labels

        for name, st in stats.items():
            if not st.isup:
                continue

            ip_list = [a.address for a in addrs.get(name, []) if a.family.name == "AF_INET"] if addrs else []
            ip_part = f" ({', '.join(ip_list)})" if ip_list else ""

            if "wi-fi" in name.lower() or "wlan" in name.lower():
                pretty = f"Wi-Fi{name.replace('Wi-Fi', '').replace('wi-fi', '')}{ip_part}"
            elif "ethernet" in name.lower() or "eth" in name.lower():
                pretty = f"Ethernet{name.replace('Ethernet', '').replace('ethernet', '')}{ip_part}"
            elif "loopback" in name.lower():
                pretty = f"Loopback{ip_part}"
            else:
                pretty = f"{name}{ip_part}"

            labels[pretty] = name

        return labels

    def subscribe(self, observer: Observer):
        if observer not in self.observers:
            self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_observers(self, event: Event):
        for observer in self.observers:
            observer.update(event)

    def update(self, event: Event):
        # Thread-safe: Put event in queue
        self.event_queue.put(event)

    def process_queue(self):
        """ Poll the queue every 100ms to update UI """
        try:
            while True:
                event = self.event_queue.get_nowait()
                self.handle_event(event)
        except queue.Empty:
            pass
        
        # Schedule next check if window is still running
        if self.window and self.window.winfo_exists():
            self.window.after(100, self.process_queue)

    def handle_event(self, event: Event):
        if event.name == "metrics_updated" and isinstance(event.payload, MetricsSnapshot):
            self.update_metrics(event.payload)
        elif event.name == "alert_generated" and isinstance(event.payload, AlertInfo):
            self.add_alert(event.payload)

    def update_metrics(self, metrics: MetricsSnapshot):
        if self.lbl_latency:
            self.lbl_latency.configure(text=f"{metrics.average_latency:.2f} ms")
        if self.lbl_packet_rate:
            self.lbl_packet_rate.configure(text=f"{metrics.packet_rate:.2f} pkts/s")
        if self.lbl_total_packets:
            self.lbl_total_packets.configure(text=f"{metrics.total_packets_captured}")

    def add_alert(self, alert: AlertInfo):
        if self.txt_alerts:
            log_msg = f"[{alert.severity}] {alert.message}\n"
            self.txt_alerts.insert("end", log_msg)
            self.txt_alerts.see("end")

    def on_start_capture(self):
        proto = self.option_protocol.get().lower()  # BPF filters require lowercase
        port_str = self.entry_port.get()
        try:
            port = int(port_str)

            display_iface = self.option_interface.get() if self.option_interface else None
            interface = self.interface_map.get(display_iface, None)

            config = CaptureConfig(protocol=proto, port=port, interface=interface)
            self.notify_observers(StartCaptureEvent(config))
            self.add_log(f"Requested capture on {proto}:{port} @ {display_iface or interface or 'auto'}")
        except ValueError:
            self.add_log("Invalid port number")

    def on_stop_capture(self):
        self.notify_observers(StopCaptureEvent())
        self.add_log("Requested stop capture")

    def on_send_query(self):
        if self.entry_chat:
            query_text = self.entry_chat.get()
            if query_text:
                self.add_chat_message(f"You: {query_text}")
                query = QueryMessage(message=query_text)
                self.notify_observers(QueryRaised(query))
                self.entry_chat.delete(0, "end")

    def display_chat_response(self, response: str):
        self.add_chat_message(f"Bot: {response}")

    def add_chat_message(self, message: str):
        if self.txt_chat_history:
            self.txt_chat_history.insert("end", message + "\n")
            self.txt_chat_history.see("end")

    def add_log(self, message: str):
        # Reusing alerts box for system logs for now
        if self.txt_alerts:
            self.txt_alerts.insert("end", f"[System] {message}\n")
            self.txt_alerts.see("end")

    def run(self):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.window = ctk.CTk()
        self.window.title("Packet Watch - Network Traffic Monitor")
        self.window.geometry("1400x800")

        # Grid Layout - 3 columns
        self.window.grid_columnconfigure(0, weight=2)  # Left: Metrics
        self.window.grid_columnconfigure(1, weight=3)  # Middle: Alerts/Logs
        self.window.grid_columnconfigure(2, weight=2)  # Right: Chat
        self.window.grid_rowconfigure(0, weight=0)     # Controls bar
        self.window.grid_rowconfigure(1, weight=1)     # Main content

        # --- 1. Controls Frame (Top Bar) ---
        frame_controls = ctk.CTkFrame(self.window, corner_radius=10)
        frame_controls.grid(row=0, column=0, columnspan=3, padx=15, pady=15, sticky="ew")
        
        # Configure control frame grid
        for i in range(6):
            frame_controls.grid_columnconfigure(i, weight=0)
        frame_controls.grid_columnconfigure(6, weight=1)  # Spacer
        
        ctk.CTkLabel(frame_controls, text="Protocol:", font=self.font_label).grid(row=0, column=0, padx=(15, 5), pady=12, sticky="w")
        self.option_protocol = ctk.CTkOptionMenu(frame_controls, values=["TCP", "UDP", "ICMP"], width=100)
        self.option_protocol.grid(row=0, column=1, padx=5, pady=12)
        
        ctk.CTkLabel(frame_controls, text="Port:", font=self.font_label).grid(row=0, column=2, padx=(15, 5), pady=12, sticky="w")
        self.entry_port = ctk.CTkEntry(frame_controls, width=80, placeholder_text="0 = all")
        self.entry_port.insert(0, "0")
        self.entry_port.grid(row=0, column=3, padx=5, pady=12)

        ctk.CTkLabel(frame_controls, text="Interface:", font=self.font_label).grid(row=0, column=4, padx=(15, 5), pady=12, sticky="w")
        interface_values = list(self.interface_map.keys()) or ["Auto-detect"]
        self.option_interface = ctk.CTkOptionMenu(frame_controls, values=interface_values, width=220)
        self.option_interface.set(interface_values[0])
        self.option_interface.grid(row=0, column=5, padx=5, pady=12)
        
        # Spacer
        ctk.CTkLabel(frame_controls, text="").grid(row=0, column=6, padx=5)
        
        self.btn_start = ctk.CTkButton(frame_controls, text="Start", command=self.on_start_capture, 
                           fg_color="#22c55e", hover_color="#16a34a", width=110, height=32, font=self.font_button)
        self.btn_start.grid(row=0, column=7, padx=8, pady=12)
        
        self.btn_stop = ctk.CTkButton(frame_controls, text="Stop", command=self.on_stop_capture, 
                          fg_color="#ef4444", hover_color="#b91c1c", width=110, height=32, font=self.font_button)
        self.btn_stop.grid(row=0, column=8, padx=(0, 15), pady=12)

        # --- 2. Metrics Frame (Left Column) ---
        frame_metrics = ctk.CTkFrame(self.window, corner_radius=10)
        frame_metrics.grid(row=1, column=0, padx=(15, 7), pady=(0, 15), sticky="nsew")
        frame_metrics.grid_columnconfigure(0, weight=1)
        frame_metrics.grid_rowconfigure(1, weight=1)
        
        # Header
        header_metrics = ctk.CTkFrame(frame_metrics, fg_color="#1f2933", corner_radius=8)
        header_metrics.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        ctk.CTkLabel(header_metrics, text="Metrics", font=self.font_title, 
                text_color="white").pack(pady=10)
        
        # Metrics content
        metrics_content = ctk.CTkFrame(frame_metrics, fg_color="transparent")
        metrics_content.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        metrics_content.grid_columnconfigure(0, weight=1)
        
        # Metric cards
        metric_card_packets = ctk.CTkFrame(metrics_content, corner_radius=8, fg_color="#111827")
        metric_card_packets.grid(row=0, column=0, sticky="ew", pady=8)
        ctk.CTkLabel(metric_card_packets, text="Total Packets", font=self.font_label, 
                text_color="gray").pack(pady=(12, 2))
        self.lbl_total_packets = ctk.CTkLabel(metric_card_packets, text="0", font=self.font_value_big)
        self.lbl_total_packets.pack(pady=(0, 12))
        
        metric_card_rate = ctk.CTkFrame(metrics_content, corner_radius=8, fg_color="#111827")
        metric_card_rate.grid(row=1, column=0, sticky="ew", pady=8)
        ctk.CTkLabel(metric_card_rate, text="Packet Rate", font=self.font_label, 
                text_color="gray").pack(pady=(12, 2))
        self.lbl_packet_rate = ctk.CTkLabel(metric_card_rate, text="0.00 pkts/s", font=self.font_value)
        self.lbl_packet_rate.pack(pady=(0, 12))
        
        metric_card_latency = ctk.CTkFrame(metrics_content, corner_radius=8, fg_color="#111827")
        metric_card_latency.grid(row=2, column=0, sticky="ew", pady=8)
        ctk.CTkLabel(metric_card_latency, text="Avg Latency", font=self.font_label, 
                text_color="gray").pack(pady=(12, 2))
        self.lbl_latency = ctk.CTkLabel(metric_card_latency, text="0.00 ms", font=self.font_value)
        self.lbl_latency.pack(pady=(0, 12))

        # --- 3. Alerts Frame (Middle Column) ---
        frame_alerts = ctk.CTkFrame(self.window, corner_radius=10)
        frame_alerts.grid(row=1, column=1, padx=7, pady=(0, 15), sticky="nsew")
        frame_alerts.grid_rowconfigure(1, weight=1)
        frame_alerts.grid_columnconfigure(0, weight=1)
        
        # Header
        header_alerts = ctk.CTkFrame(frame_alerts, fg_color="#111827", corner_radius=8)
        header_alerts.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        ctk.CTkLabel(header_alerts, text="Alerts & Logs", font=self.font_title, 
                text_color="white").pack(pady=10)
        
        self.txt_alerts = ctk.CTkTextbox(frame_alerts, font=self.font_log, wrap="word")
        self.txt_alerts.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        # --- 4. Chatbot Frame (Right Column) ---
        frame_chat = ctk.CTkFrame(self.window, corner_radius=10)
        frame_chat.grid(row=1, column=2, padx=(7, 15), pady=(0, 15), sticky="nsew")
        frame_chat.grid_rowconfigure(1, weight=1)
        frame_chat.grid_columnconfigure(0, weight=1)
        
        # Header
        header_chat = ctk.CTkFrame(frame_chat, fg_color="#111827", corner_radius=8)
        header_chat.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        ctk.CTkLabel(header_chat, text="Assistant", font=self.font_title, 
                text_color="white").pack(pady=10)
        
        self.txt_chat_history = ctk.CTkTextbox(frame_chat, font=(self.font_sans, 14), wrap="word")
        self.txt_chat_history.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        
        # Chat input
        frame_chat_input = ctk.CTkFrame(frame_chat, fg_color="transparent")
        frame_chat_input.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        frame_chat_input.grid_columnconfigure(0, weight=1)
        
        self.entry_chat = ctk.CTkEntry(
            frame_chat_input,
            placeholder_text="Ask me anything about the network...",
            height=44,
            font=(self.font_sans, 16)
        )
        self.entry_chat.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry_chat.bind("<Return>", lambda e: self.on_send_query())
        
        btn_send = ctk.CTkButton(frame_chat_input, text="Send", width=80, height=40, 
                    font=self.font_button, command=self.on_send_query)
        btn_send.grid(row=0, column=1)

        # Start Queue Processing
        self.process_queue()
        
        # Start Main Loop
        self.window.mainloop()
