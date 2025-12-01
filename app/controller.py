import queue
import threading
import time
from typing import Optional

from app.modules import Capture, Chatbot, GUI
from app.utils import QueryMessage, CaptureConfig
from app.utils.interfaces import Observer
from app.utils.events import Event, StartCaptureEvent, StopCaptureEvent, QueryRaised

class Controller(Observer):
    def __init__(self, capturer:Capture, chatbot: Chatbot, gui: GUI):
        self.capturer = capturer
        self.chatbot = chatbot
        self.gui = gui
        
        self.event_queue = queue.Queue()
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Gracefully stops the controller loop."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def update(self, event: Event):
        self.event_queue.put(event)

    def _run_loop(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.5)
                self.handle_event(event)
            except queue.Empty:
                continue

    def handle_event(self, event: Event):
        try:
            if isinstance(event, StartCaptureEvent):
                self.start_capture(event.payload)
            elif isinstance(event, StopCaptureEvent):
                self.stop_capture()
            elif isinstance(event, QueryRaised):
                self.process_query(event.payload)
        except Exception as e:
            error_msg = f"Controller Error: {e}"
            print(error_msg)
            # Send error to GUI logs
            from app.utils.models import AlertInfo
            from datetime import datetime
            alert = AlertInfo(
                alert_type="error",
                message=str(e),
                severity="ERROR",
                timestamp=datetime.now()
            )
            from app.utils.events import AlertGeneratedEvent
            self.gui.update(AlertGeneratedEvent(alert))

    def process_query(self, query: QueryMessage):
        self.chatbot.processQuery(query)
    
    def start_capture(self, config: CaptureConfig):
        self.capturer.start_capture(config=config)

    def stop_capture(self):
        self.capturer.stop_capture()