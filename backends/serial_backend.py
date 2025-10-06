import time
from typing import List

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

READ_TIMEOUT_S = 0.2
IDLE_GAP_S = 0.35
EOL = "\n"

from .base_backend import ATBackend

class SerialBackend(ATBackend):
    def __init__(self):
        self.ser = None

    def list_ports(self) -> List[str]:
        if list_ports is None:
            return []
        return [p.device for p in list_ports.comports()]

    def connect(self, port: str, baud: int):
        if serial is None:
            raise RuntimeError("pyserial non installato. Esegui: pip install pyserial")
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.ser = serial.Serial(port=port, baudrate=baud, timeout=READ_TIMEOUT_S)

    def disconnect(self):
        if self.ser:
            try:
                self.ser.close()
            finally:
                self.ser = None

    def is_connected(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def send_and_read(self, cmd_text: str) -> str:
        if not self.is_connected():
            raise RuntimeError("Seriale non connessa")
        data = (cmd_text + EOL).encode("utf-8", errors="ignore")
        self.ser.reset_input_buffer()
        self.ser.write(data)
        self.ser.flush()

        start = time.time()
        buf = bytearray()
        last_rx = time.time()
        while True:
            chunk = self.ser.read(1024)
            if chunk:
                buf.extend(chunk)
                last_rx = time.time()
                # terminatori tipici
                txt = buf.decode(errors="ignore")
                if "OK" in txt or "ERROR" in txt or "+CME ERROR" in txt or "+CMS ERROR" in txt:
                    break
            else:
                if time.time() - last_rx > IDLE_GAP_S:
                    break
            if time.time() - start > 10:
                break
        return buf.decode("utf-8", errors="ignore")