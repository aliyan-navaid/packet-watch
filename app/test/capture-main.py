from app.modules import Capture, Metrics
from app.utils.models import CaptureConfig

if __name__ == '__main__':
    protocol: str = 'ip'
    port: int = 0
    interface: str = 'Wi-Fi'

    config: CaptureConfig = CaptureConfig('tcp', port, interface, "./app/test/output.pcap")

    capture = Capture(config)
    metrics = Metrics()

    capture.subscribe(metrics)
    capture.start_capture()
    capture.stop_capture(10)