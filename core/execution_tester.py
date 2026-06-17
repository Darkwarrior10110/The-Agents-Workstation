import subprocess
import os
import time
import signal
from core.schema import ExecutionReport
from core.traceback_analyzer import TracebackAnalyzer
from core.logger import system_logger
from core.runtime.health_validator import HealthValidator, FailureCategory

class ExecutionTester:
    """
    Safe execution sandbox for running generated code.
    Enforces timeout, isolates processes, and captures detailed tracebacks.
    """
    
    @staticmethod
    def run_safe(command: str, cwd: str, timeout: int = 15) -> ExecutionReport:
        from core.platform_utils import PlatformUtils
        command = PlatformUtils.resolve_command(command, cwd)
        system_logger.info(f"[SANDBOX] Executing command: {command} in {cwd} with {timeout}s timeout")
        start_time = time.time()
        
        try:
            headless_env = os.environ.copy()
            headless_env["CI"] = "true"
            headless_env["npm_config_yes"] = "true"
            
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=headless_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                **PlatformUtils.get_popen_kwargs()
            )
            
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                # Timeout is not necessarily a crash for long-running processes
                system_logger.info(f"[SANDBOX] Process reached timeout ({timeout}s). Terminating gracefully.")
                PlatformUtils.kill_process_group(process)
                try:
                    stdout_bytes, stderr_bytes = process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    PlatformUtils.force_kill_process_group(process)
                    stdout_bytes, stderr_bytes = process.communicate()
                
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                exit_code = 0
                
        except Exception as e:
            system_logger.error(f"[SANDBOX] Execution setup failed: {str(e)}")
            return ExecutionReport(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=round(time.time() - start_time, 3),
                is_stable=False
            )

        duration = round(time.time() - start_time, 3)
        
        traceback_analysis = None
        is_stable = (exit_code == 0)
        
        if exit_code != 0:
            traceback_analysis = TracebackAnalyzer.analyze(stderr, stdout)
            if traceback_analysis.is_syntax_error or "Traceback" in stderr:
                is_stable = False
                system_logger.warning(f"[SANDBOX] Execution crashed: {traceback_analysis.root_cause}")
                
        return ExecutionReport(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            traceback_analysis=traceback_analysis,
            is_stable=is_stable
        )

    @staticmethod
    def run_server_safe(command: str, cwd: str, port: int, max_timeout: int = 20) -> ExecutionReport:
        from core.platform_utils import PlatformUtils
        command = PlatformUtils.resolve_command(command, cwd)
        system_logger.info(f"[SANDBOX] Starting server: {command} on port {port} in {cwd}")
        start_time = time.time()
        
        try:
            headless_env = os.environ.copy()
            headless_env["CI"] = "true"
            headless_env["npm_config_yes"] = "true"
            headless_env["PORT"] = str(port)
            
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=headless_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **PlatformUtils.get_popen_kwargs()
            )
            
            # Use HealthValidator to check status progressively
            health_status = HealthValidator.wait_and_validate(process, port, max_timeout)
            
            # Regardless of outcome, terminate safely
            PlatformUtils.kill_process_group(process)
            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                PlatformUtils.force_kill_process_group(process)
                stdout_bytes, stderr_bytes = process.communicate()
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            duration = round(time.time() - start_time, 3)
            
            if health_status.is_healthy:
                system_logger.info(f"[SANDBOX] Server healthy on port {port}.")
                return ExecutionReport(
                    command=command,
                    exit_code=0,
                    stdout=stdout,
                    stderr=stderr,
                    duration=duration,
                    is_stable=True
                )
            else:
                system_logger.warning(f"[SANDBOX] Server unhealthy: {health_status.category.value} - {health_status.details}")
                # Treat validation failure as non-zero exit for analyzer
                traceback_analysis = TracebackAnalyzer.analyze(stderr, stdout)
                if not traceback_analysis.is_syntax_error and health_status.category != FailureCategory.PROCESS_CRASH:
                     traceback_analysis.root_cause = health_status.category.value
                
                return ExecutionReport(
                    command=command,
                    exit_code=1,
                    stdout=stdout,
                    stderr=stderr,
                    duration=duration,
                    traceback_analysis=traceback_analysis,
                    is_stable=False
                )
                
        except Exception as e:
            system_logger.error(f"[SANDBOX] Server setup failed: {str(e)}")
            return ExecutionReport(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=round(time.time() - start_time, 3),
                is_stable=False
            )
