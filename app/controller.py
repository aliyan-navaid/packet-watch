from app.modules import Capture, Chatbot, GUI
from app.utils import QueryMessage, CaptureConfig

class Controller:
    def __init__(self, capturer:Capture, chatbot: Chatbot, gui: GUI):
        self.capturer = capturer
        self.chatbot = chatbot
        self.gui = gui

        self.gui.run()

    def process_query(self, query: QueryMessage):
        self.chatbot.processQuery(query)
    
    def start_capture(self, config: CaptureConfig):
        self.capturer.start_capture(config)

    def stop_capture(self):
        self.capturer.stop_capture()