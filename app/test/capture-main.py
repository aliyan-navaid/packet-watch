from app.modules import Capture, Metrics, Storage
from app.utils.models import CaptureConfig

if __name__ == '__main__':
    protocol: str = 'ip'
    port: int = 0
    interface: str = 'Wi-Fi'

    config: CaptureConfig = CaptureConfig(protocol, port, interface)

    capture = Capture(config)
    metrics = Metrics()
    storage = Storage()

    capture.subscribe(metrics)
    capture.subscribe(storage)
    capture.start_capture()
    capture.stop_capture(10)
    storage.materialize('./output.json')