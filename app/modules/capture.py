from app.utils import PacketData, CaptureConfig
from app.utils.interfaces import Subject, Observer
from app.utils.events import Event

class Capture(Subject):
    def __init__(self):
        self.observers: list[Observer] = []

    def start_capture(self, config:CaptureConfig):
        pass
    
    def stop_capture(self):
        pass

    def subscribe(self, observer: Observer):
        self.observers.append(observer)

    def unsubscribe(self, observer:Observer):
        self.observers.remove(observer)

    def notifyObservers(self, event: Event):
        for observer in self.observers:
            observer.update(event)