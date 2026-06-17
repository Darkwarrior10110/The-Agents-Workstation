import urllib.request
import urllib.error
import socket
import time
import subprocess
from enum import Enum
from pydantic import BaseModel
from core.runtime.port_manager import PortManager

class FailureCategory(str, Enum):
    NONE = "none"
    BOOT_TIMEOUT = "boot_timeout"
    IMPORT_ERROR = "import_error"
    PORT_CONFLICT = "port_conflict"
    HEALTHCHECK_FAILED = "healthcheck_failed"
    PROCESS_CRASH = "process_crash"
    INVALID_RESPONSE = "invalid_response"
    DEPENDENCY_FAILURE = "dependency_failure"

class HealthStatus(BaseModel):
    is_healthy: bool
    category: FailureCategory
    details: str

class HealthValidator:
    @staticmethod
    def check_process_alive(process: subprocess.Popen) -> bool:
        """Checks if the subprocess is still running."""
        return process.poll() is None

    @staticmethod
    def wait_and_validate(process: subprocess.Popen, port: int, max_timeout: int = 20) -> HealthStatus:
        """
        Progressively waits for the server to bootstrap and validates its health.
        Wait steps: 1s, 2s, 3s, 5s, etc.
        """
        start_time = time.time()
        
        while time.time() - start_time < max_timeout:
            # 1. Check if process crashed
            if not HealthValidator.check_process_alive(process):
                return HealthStatus(
                    is_healthy=False,
                    category=FailureCategory.PROCESS_CRASH,
                    details="The process terminated unexpectedly during startup."
                )

            # 2. Check if port is open
            if not PortManager.is_port_available(port):
                # This means the port is actively listening!
                # Now try an HTTP ping.
                try:
                    req = urllib.request.Request(f"http://127.0.0.1:{port}/")
                    with urllib.request.urlopen(req, timeout=2) as response:
                        if response.status in [200, 401, 403, 404]:
                            return HealthStatus(
                                is_healthy=True,
                                category=FailureCategory.NONE,
                                details="Server is healthy and responding to HTTP requests."
                            )
                except urllib.error.URLError as e:
                    # Connection refused or timeout, but port was seen as open? 
                    # Might still be booting. Give it a moment.
                    pass
                except Exception:
                    pass

            time.sleep(1) # simple 1s interval is often better than complex backoff for 20s

        # If we reach here, it timed out
        return HealthStatus(
            is_healthy=False,
            category=FailureCategory.BOOT_TIMEOUT,
            details=f"Server failed to become responsive on port {port} within {max_timeout} seconds."
        )
