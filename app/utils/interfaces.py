from abc import ABC, abstractmethod
from app.utils.events import Event

class Observer(ABC):
    @abstractmethod
    def update(self, event:Event):
        pass

class Subject(ABC):
    @abstractmethod
    def subscribe(self, observer: Observer):
        pass

    @abstractmethod
    def unsubscribe(self, observer:Observer):
        pass

    @abstractmethod
    def notify_observers(self, event: Event):
        pass