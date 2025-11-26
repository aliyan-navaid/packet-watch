class Event:
    def __init__(self, name: str, payload: dict = None):
        self.name = name
        self.payload = payload or {}