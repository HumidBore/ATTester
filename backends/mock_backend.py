import random
from typing import List
from .base_backend import ATBackend

EOL = "\n"

_SAMPLE_RESPONSES = {
    "AT": "OK",
    "ATI": "Manufacturer: DemoCorp" + EOL + "Model: DEMO-01" + EOL + "Revision: 1.2.3" + EOL + "OK",
    "AT+GMR": "DEMO FW 1.2.3" + EOL + "OK",
    "AT+CSQ": "+CSQ: 18,99" + EOL + "OK",
    "AT+CREG?": "+CREG: 0,1" + EOL + "OK",
    "AT+CMEE=2": "OK",
    "AT+CMGF=1": "OK",
    "AT+CMGS=\"+391234567890\"": "> ",  # prompt SMS classico
}

class MockBackend(ATBackend):
    """Backend finto per test senza hardware.

    - Espone una "porta" virtuale "DEMO: Mock Modem".
    - Genera risposte plausibili; se non conosce il comando, restituisce "OK" o un errore casuale.
    - Riconosce comandi che contengono la parola ERROR e risponde con ERROR.
    """

    def __init__(self):
        self.connected = False

    def list_ports(self) -> List[str]:
        return ["DEMO: Mock Modem"]

    def connect(self, port: str, baud: int):
        if not port.startswith("DEMO"):
            raise RuntimeError("In DEMO seleziona la porta 'DEMO: Mock Modem'")
        self.connected = True

    def disconnect(self):
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def send_and_read(self, cmd_text: str) -> str:
        if not self.connected:
            raise RuntimeError("DEMO non connesso")
        cmd = cmd_text.strip()

        # Se l'utente prova un comando di invio SMS con testo dopo il prompt, simula risposta
        if cmd.endswith(""):
            return "+CMGS: 42" + EOL + "OK"

        # Regole semplici
        if "ERROR" in cmd:
            return "ERROR"
        if cmd in _SAMPLE_RESPONSES:
            return _SAMPLE_RESPONSES[cmd]
        if cmd.startswith("AT+CSQ"):
            rssi = random.randint(5, 31)
            return f"+CSQ: {rssi},99" + EOL + "OK"
        if cmd.startswith("AT+GMR"):
            return "DEMO FW 1.2.3" + EOL + "OK"
        if cmd.startswith("AT+CMGS"):
            # Simula prompt '>' per testo SMS; l'app mostrerà solo l'output
            return "> "

        # Default: echo ben formato
        return "OK"