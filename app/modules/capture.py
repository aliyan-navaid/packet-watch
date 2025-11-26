import time
import pyshark
import threading
import asyncio

from app.utils.interfaces import Subject, Observer
from app.utils.events import Event

from pyshark.tshark.tshark import get_all_tshark_interfaces_names
from pyshark.packet.packet import Packet

from typing import List, Optional
from pprint import pprint

class Capture:
    @staticmethod
    def _get_active_interface(timeout: int = 3, bpf_filter: str = 'ip') -> str:
        pyshark_ifaces = get_all_tshark_interfaces_names()
        for iface in pyshark_ifaces:
            if 'Device' in iface: # avoiding windows GUIDs
                continue
            try:
                capture = pyshark.LiveCapture(interface=iface, bpf_filter=bpf_filter)
                capture.sniff(timeout=timeout)
                if len(capture) > 0:
                    return iface
            except Exception:
                continue
     
        raise RuntimeError("No active interface found.")   

    @staticmethod
    def _handle_packet(packet: Packet) -> None:
        print(packet)
    
    def _sniff(self, timeout: int | None = None, total: int = 0) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        bpf = self.protocol
        if self.port:
            bpf = f"{self.protocol} port {self.port}"

        self._capture = pyshark.LiveCapture(interface=self.interface, bpf_filter=bpf)

        start_time = time.time()
        try:
            count = 0
            for packet in self._capture.sniff_continuously():
                if not self._running:
                    break  # stop requested
                self._handle_packet(packet)
                self.packets.append(packet)
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
    def __init__(self, protocol: str, port: int, interface: Optional[str] = None) -> None:
        if port not in range(0, 65536):
            raise AttributeError("Capture.__init__: invalid port")

        self.protocol: str = protocol
        self.port: int = port
        self.interface = interface or self._get_active_interface()
        self.packets: List[Packet] = []

        self._capture: Optional[pyshark.LiveCapture] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self.observers: list[Observer] = [] # not handled yet
        
    def start_capture(self, timeout: int | None = None, total: int = 0) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._sniff, args=(timeout, total), daemon=False)
        self._thread.start()

    def stop_capture(self, timeout: int = 0) -> None:
        """
        Docstring for stop_capture
        
        :param timeout: stop capture after given amount of seconds
        :type timeout: int
        """
        
        if not self._running:
            return
        
        time.sleep(timeout)
        
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def clear(self) -> None:
        self.packets.clear()

    def subscribe(self, observer: Observer):
        self.observers.append(observer)

    def unsubscribe(self, observer:Observer):
        self.observers.remove(observer)

    def notifyObservers(self, event: Event):
        for observer in self.observers:
            pass

if __name__ == '__main__':
    print('Start')
    capture_tcp = Capture('ip', 0, 'Wi-Fi')
    print('Created Capture')
    capture_tcp.start_capture(10)
    print('Capturing')
    capture_tcp.stop_capture(5)
    print('Done')