import os
import signal
import subprocess
from typing import Dict, Any

class PlatformUtils:
    """
    Lightweight OS-aware execution helper to handle platform-specific behavior 
    (Windows vs POSIX) without leaking complexity into the orchestration pipeline.
    """

    @staticmethod
    def get_venv_executable(project_path: str, executable_name: str) -> str:
        """Resolves absolute path to venv executables dynamically based on OS."""
        if os.name == 'nt':
            venv_bin = os.path.join(project_path, "venv", "Scripts")
            exe_path = os.path.join(venv_bin, f"{executable_name}.exe")
        else:
            venv_bin = os.path.join(project_path, "venv", "bin")
            exe_path = os.path.join(venv_bin, executable_name)
            
        if os.path.exists(exe_path):
            return exe_path
        return executable_name  # fallback to system PATH if venv is missing

    @staticmethod
    def resolve_command(command: str, project_path: str) -> str:
        """Replaces ecosystem base commands with venv-specific absolute paths safely."""
        new_command = command.strip()
        # Common ecosystem commands that should execute inside the isolated project venv
        for base_cmd in ["python3", "python", "pip3", "pip", "uvicorn", "pytest", "npm", "node"]:
            resolved = PlatformUtils.get_venv_executable(project_path, base_cmd)
            
            # Quote the resolved path if it contains spaces (crucial for Windows)
            if " " in resolved and not resolved.startswith('"'):
                resolved = f'"{resolved}"'
            
            # Match strictly at the start to avoid replacing mid-string arguments maliciously
            if new_command.startswith(f"{base_cmd} "):
                new_command = resolved + new_command[len(base_cmd):]
                break
            elif new_command == base_cmd:
                new_command = resolved
                break
                
        return new_command

    @staticmethod
    def get_popen_kwargs() -> Dict[str, Any]:
        """Returns OS-specific kwargs for subprocess.Popen to enable safe process group isolation."""
        kwargs = {}
        if os.name == 'nt':
            # Windows: Create a new process group to allow safe CTRL_BREAK signal
            kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            # POSIX: Start process in a new session for safe SIGTERM isolation
            kwargs['preexec_fn'] = os.setsid
        return kwargs

    @staticmethod
    def kill_process_group(process: subprocess.Popen):
        """Safely terminates the process group across platforms."""
        try:
            if os.name == 'nt':
                # Windows graceful kill
                os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            else:
                # POSIX graceful kill
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception:
            pass # Process or group may already be dead
            
    @staticmethod
    def force_kill_process_group(process: subprocess.Popen):
        """Force kills the process group across platforms if graceful kill failed."""
        try:
            if os.name == 'nt':
                process.kill()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            pass
