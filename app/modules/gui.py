import PySimpleGUI as sg
from app.utils import Event, PacketData, MetricsSnapshot, AlertInfo
from app.utils.interfaces import Subject, Observer
from app.utils.events import Event


class GUI(Observer):
    def __init__(self):
        pass

    def run(self):
        pass

    def handleEvents(self, event):
        if isinstance(event, PacketData):
            pass
        elif isinstance(event, MetricsSnapshot):
            pass
        elif isinstance(event, AlertInfo):
            pass

    def update(self, event: Event):
        pass
