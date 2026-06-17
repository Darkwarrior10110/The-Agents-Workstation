import socket
from typing import Set

class PortManager:
    _reserved_ports: Set[int] = set()

    @classmethod
    def get_free_port(cls, start_port: int = 8000, max_attempts: int = 100) -> int:
        """Finds and reserves a free port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            if cls.is_port_available(port):
                cls.reserve_port(port)
                return port
        raise RuntimeError(f"Could not find a free port between {start_port} and {start_port + max_attempts}")

    @classmethod
    def is_port_available(cls, port: int) -> bool:
        """Checks if a port is currently listening or reserved."""
        if port in cls._reserved_ports:
            return False
            
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # If connect_ex returns 0, the port is open and therefore NOT available for a new server
            return s.connect_ex(('127.0.0.1', port)) != 0

    @classmethod
    def reserve_port(cls, port: int):
        """Marks a port as reserved so other processes in this manager won't take it."""
        cls._reserved_ports.add(port)

    @classmethod
    def release_port(cls, port: int):
        """Releases a previously reserved port."""
        cls._reserved_ports.discard(port)
