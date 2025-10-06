from abc import ABC, abstractmethod
from typing import List

class ATBackend(ABC):
    """Interfaccia comune per backend (seriale reale o demo)."""

    @abstractmethod
    def list_ports(self) -> List[str]:
        pass

    @abstractmethod
    def connect(self, port: str, baud: int):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def send_and_read(self, cmd_text: str) -> str:
        pass
