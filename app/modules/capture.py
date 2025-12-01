import time
import pyshark
import asyncio
import threading

from app.utils.interfaces import Subject, Observer
from app.utils.events import Event, PacketCapturedEvent
from app.utils.models import CaptureConfig

from pyshark.tshark.tshark import get_all_tshark_interfaces_names
from pyshark.packet.packet import Packet

from typing import Optional


class Capture(Subject):
    @staticmethod
    def _get_active_interface(timeout: int = 3, bpf_filter: str = "ip") -> str:
        pyshark_ifaces = get_all_tshark_interfaces_names()
        for iface in pyshark_ifaces:
            # Removed "Device" check to support Windows NPF interfaces
            try:
                capture = pyshark.LiveCapture(interface=iface, bpf_filter=bpf_filter)
                capture.sniff(timeout=timeout)
                if len(capture) > 0:
                    return iface
            except Exception:
                continue

        raise RuntimeError("No active interface found.")

    def _handle_packet(self, packet: Packet) -> None:
        self.notify_observers(PacketCapturedEvent(packet))
        # print(packet)

    def _sniff(self, timeout: int | None = None, total: int = 0) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        bpf = self.config.protocol
        if self.config.port and self.config.port > 0:
            bpf = f"{self.config.protocol} port {self.config.port}"

        self._capture = pyshark.LiveCapture(
            interface=self.config.interface,
            bpf_filter=bpf,
        )

        start_time = time.time()
        try:
            count = 0
            for packet in self._capture.sniff_continuously():
                if not self._running:
                    break  # stop requested
                self._handle_packet(packet)
                count += 1
                if total > 0 and count >= total:
                    break
                if timeout and (time.time() - start_time) >= timeout:
                    break
        finally:
            if self._capture is not None:
                self._capture.close()
                self._capture = None

            self._running = False

    # bonus - provide interface to save time
    def __init__(self, config: Optional[CaptureConfig] = None) -> None:
        self.config: Optional[CaptureConfig] = config

        self._capture: Optional[pyshark.LiveCapture] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self.observers: list[Observer] = []
        self._obs_lock: threading.Lock = threading.Lock()

    def start_capture(self, config: Optional[CaptureConfig] = None, timeout: Optional[int] = None, total: int = 0) -> None:
        """
        :param config: Capture configuration (protocol, port, interface)
        :param timeout: run capture for given amount of seconds - default; run until `stop_capture()` is called
        :param total: number of packets to capture - default; infinite
        """
        if self._running:
            return

        if config:
            self.config = config
        
        if not self.config:
            raise ValueError("No configuration provided for capture.")

        if self.config.port not in range(0, 65536):
            raise AttributeError("Capture: invalid port")

        if not self.config.interface:
            self.config.interface = self._get_active_interface()

        self._running = True
        self._thread = threading.Thread(
            target=self._sniff, args=(timeout, total), daemon=True
        )
        self._thread.start()

    def stop_capture(self, timeout: int = 0) -> None:
        """
        Docstring for stop_capture

        :param timeout: stop capture after given amount of seconds - default; stop immediately
        :type timeout: int
        """

        if not self._running:
            return

        time.sleep(timeout)

        self._running = False

        if self._capture:
            try:
                self._capture.close()
            except Exception:
                pass

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def subscribe(self, observer: Observer):
        if not isinstance(observer, Observer):
            raise TypeError("expected Observer, got", type(observer))

        with self._obs_lock:
            self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        with self._obs_lock:
            self.observers.remove(observer)

    def notify_observers(self, event: Event):
        with self._obs_lock:
            observer_copy = self.observers

        for observer in observer_copy:
            observer.update(event)
