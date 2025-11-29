import queue
import customtkinter as ctk
from typing import Optional, List

from app.utils.interfaces import Observer, Subject
from app.utils.events import Event, StartCaptureEvent, StopCaptureEvent, QueryRaised
from app.utils.models import MetricsSnapshot, AlertInfo, CaptureConfig, QueryMessage

class GUI(Observer, Subject):
    def __init__(self):
        self.event_queue = queue.Queue()
        self.observers: List[Observer] = []
        self.window: Optional[ctk.CTk] = None
        
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
        self.btn_start: Optional[ctk.CTkButton] = None
        self.btn_stop: Optional[ctk.CTkButton] = None

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
        proto = self.option_protocol.get()
        port_str = self.entry_port.get()
        try:
            port = int(port_str)
            config = CaptureConfig(protocol=proto, port=port)
            self.notify_observers(StartCaptureEvent(config))
            self.add_log(f"Requested capture on {proto}:{port}")
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
        self.window.title("Packet Watch")
        self.window.geometry("1000x700")

        # Grid Layout
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=2)
        self.window.grid_rowconfigure(0, weight=0) # Controls
        self.window.grid_rowconfigure(1, weight=1) # Metrics & Alerts
        self.window.grid_rowconfigure(2, weight=1) # Chat

        # --- 1. Controls Frame ---
        frame_controls = ctk.CTkFrame(self.window)
        frame_controls.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(frame_controls, text="Protocol:").grid(row=0, column=0, padx=5, pady=5)
        self.option_protocol = ctk.CTkOptionMenu(frame_controls, values=["TCP", "UDP", "ICMP"])
        self.option_protocol.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(frame_controls, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.entry_port = ctk.CTkEntry(frame_controls, width=60)
        self.entry_port.insert(0, "80")
        self.entry_port.grid(row=0, column=3, padx=5, pady=5)
        
        self.btn_start = ctk.CTkButton(frame_controls, text="Start Capture", command=self.on_start_capture, fg_color="green")
        self.btn_start.grid(row=0, column=4, padx=10, pady=5)
        
        self.btn_stop = ctk.CTkButton(frame_controls, text="Stop Capture", command=self.on_stop_capture, fg_color="red")
        self.btn_stop.grid(row=0, column=5, padx=10, pady=5)

        # --- 2. Metrics Frame ---
        frame_metrics = ctk.CTkFrame(self.window)
        frame_metrics.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        frame_metrics.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_metrics, text="Metrics Dashboard", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        ctk.CTkLabel(frame_metrics, text="Total Packets:").grid(row=1, column=0, sticky="w", padx=10)
        self.lbl_total_packets = ctk.CTkLabel(frame_metrics, text="0", font=("Arial", 14))
        self.lbl_total_packets.grid(row=1, column=1, sticky="e", padx=10)
        
        ctk.CTkLabel(frame_metrics, text="Packet Rate:").grid(row=2, column=0, sticky="w", padx=10)
        self.lbl_packet_rate = ctk.CTkLabel(frame_metrics, text="0.00 pkts/s", font=("Arial", 14))
        self.lbl_packet_rate.grid(row=2, column=1, sticky="e", padx=10)
        
        ctk.CTkLabel(frame_metrics, text="Avg Latency:").grid(row=3, column=0, sticky="w", padx=10)
        self.lbl_latency = ctk.CTkLabel(frame_metrics, text="0.00 ms", font=("Arial", 14))
        self.lbl_latency.grid(row=3, column=1, sticky="e", padx=10)

        # --- 3. Alerts Frame ---
        frame_alerts = ctk.CTkFrame(self.window)
        frame_alerts.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        frame_alerts.grid_rowconfigure(1, weight=1)
        frame_alerts.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame_alerts, text="System Alerts & Logs", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=5)
        self.txt_alerts = ctk.CTkTextbox(frame_alerts)
        self.txt_alerts.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # --- 4. Chatbot Frame ---
        frame_chat = ctk.CTkFrame(self.window)
        frame_chat.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        frame_chat.grid_rowconfigure(1, weight=1)
        frame_chat.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame_chat, text="Assistant", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=5)
        self.txt_chat_history = ctk.CTkTextbox(frame_chat, height=100)
        self.txt_chat_history.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        frame_chat_input = ctk.CTkFrame(frame_chat, fg_color="transparent")
        frame_chat_input.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        frame_chat_input.grid_columnconfigure(0, weight=1)
        
        self.entry_chat = ctk.CTkEntry(frame_chat_input, placeholder_text="Ask something...")
        self.entry_chat.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.entry_chat.bind("<Return>", lambda e: self.on_send_query())
        
        btn_send = ctk.CTkButton(frame_chat_input, text="Send", width=60, command=self.on_send_query)
        btn_send.grid(row=0, column=1)

        # Start Queue Processing
        self.process_queue()
        
        # Start Main Loop
        self.window.mainloop()
