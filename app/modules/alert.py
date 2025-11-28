from app.utils import AlertInfo
from app.utils.interfaces import Subject, Observer
from app.utils.events import Event


class Alerts(Subject, Observer):
    def __init__(self):
        pass

    def update(self, event: Event):
        pass

    def subscribe(self, observer: Observer):
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        self.observers.remove(observer)

    def notify_observers(self, event: Event):
        for observer in self.observers:
            observer.update(event)
