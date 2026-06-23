from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse
from core.schema import Task, TaskStatus, ExecutionReport
from core.validation_schema import ExecutionResult
import subprocess
import os
import time
import re
import signal
import socket

import urllib.request
import urllib.error

class TerminalAgent(BaseAgent):
    def __init__(self, name: str = "Terminal", role: str = "DevOps & Execution Engineer"):
        super().__init__(name, role)
        
        # LAYER 1: Dangerous Pattern Blocking
        self.dangerous_patterns = [
            r"rm\s+-rf\s+/", r"sudo\s", r"mkfs", r"dd\s+if=", 
            r"shutdown", r"reboot", r"chmod\s+777",
            r":\(\)\{\s*:\|:&\s*\};:"  # Fork bomb
        ]
        
        # LAYER 2: Allowlist of base commands
        self.allowlist = [
            "python", "python3", "pip", "pip3", "uvicorn", "pytest",
            "npm", "node", "mkdir", "touch", "echo", "ls", "test", 
            "sleep", "kill", "curl", "source", "export", "bash", "sh", "cat", "grep", "git",
            "cd", "pwd", "rm", "cp", "mv", "find", "xargs", "chmod"
        ]
        
        # LAYER 3: Malicious redirects/pipes
        self.malicious_regex = [
            r">\s*/dev/(?!null).*",  # allow /dev/null, block others
            r"&\s*/dev/.*",
            r"/dev/tcp",
            r"/dev/udp"
        ]

    def _is_safe(self, command: str) -> tuple[bool, str]:
        for pattern in self.dangerous_patterns:
            if re.search(pattern, command):
                return False, f"Dangerous pattern matched: {pattern}"
                
        # Split by shell operators to validate components individually
        parts = re.split(r'&&|\|\||\||;', command)
        for part in parts:
            part = part.strip()
            if not part: continue
            part = part.replace('&', '').strip()
            
            base_cmd = part.split()[0]
            base_cmd_name = os.path.basename(base_cmd)
            
            if "=" in base_cmd_name:
                 continue # Environment variable assignment
                 
            if base_cmd_name not in self.allowlist and base_cmd_name != "":
                return False, f"Command not in allowlist: {base_cmd_name}"

        for mal in self.malicious_regex:
            if re.search(mal, command):
                return False, f"Malicious regex matched: {mal}"

        return True, "Safe"

    def _check_port_open(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def _wait_for_server(self, port: int, timeout: int = 15) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                # Try HTTP ping first
                req = urllib.request.Request(f"http://127.0.0.1:{port}/")
                with urllib.request.urlopen(req, timeout=1) as response:
                    # Any valid HTTP response means the server is up
                    if response.status in [200, 401, 403, 404]:
                        return True
            except urllib.error.URLError:
                pass
            except Exception:
                pass
                
            # Fallback to simple socket check if HTTP isn't responding normally yet
            if self._check_port_open(port):
                return True
                
            time.sleep(1)
        return False

    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        from core.execution_tester import ExecutionTester
        from core.runtime.port_manager import PortManager
        import json
        
        command = task.input_data.get("command")
        project_path = context.get("project_path") if context else os.getcwd()
        
        if not command:
            return AgentResponse(agent_name=self.name, status=TaskStatus.FAILED, output=None, logs=["No command provided."])

        is_safe, reason = self._is_safe(command)
        if not is_safe:
            self.log(f"SECURITY ALERT: Blocked command: {command}. Reason: {reason}", "error")
            return AgentResponse(
                agent_name=self.name, status=TaskStatus.FAILED,
                output={"error": f"Command rejected: {reason}", "error_category": "security"},
                logs=[f"BLOCKED: {command} - {reason}"]
            )

        start_time = time.time()
        try:
            # Handle 'cd' inherently if it's the only command, or let the shell handle it for chained commands
            if command.startswith("cd ") and "&&" not in command and ";" not in command:
                 new_dir = command[3:].strip()
                 new_cwd = os.path.abspath(os.path.join(project_path, new_dir))
                 if os.path.isdir(new_cwd):
                     # Notice: this doesn't change python's cwd permanently across tasks 
                     # but returns success so the agent thinks it worked.
                     # Real directory changes should be handled by updating task input data or state, 
                     # but for immediate compat we allow the command.
                     pass 
                 else:
                     return AgentResponse(agent_name=self.name, status=TaskStatus.FAILED, output={"error": f"Directory not found: {new_dir}"}, logs=["cd failed"])

            self.log(f"Executing: {command} (CWD: {project_path})")
            
            is_runtime_check = task.task_type == "runtime_validation"
            
            if is_runtime_check:
                # Use PortManager to safely acquire a port
                target_port = 8000
                port_match = re.search(r'--port\s+(\d+)', command)
                if port_match:
                    target_port = int(port_match.group(1))

                try:
                    final_port = PortManager.get_free_port(target_port)
                except RuntimeError as e:
                    return AgentResponse(agent_name=self.name, status=TaskStatus.FAILED, output={"error": str(e)}, logs=["Port allocation failed."])

                # Update command with new port if needed
                cmd_to_run = re.sub(r'--port\s+\d+', f'--port {final_port}', command.rstrip(" &"))
                if "--port" not in cmd_to_run and "uvicorn" in cmd_to_run:
                    cmd_to_run += f" --port {final_port}"
                
                self.log(f"Attempting runtime validation on allocated port {final_port}...")
                
                # Use the ExecutionTester for safe progressive validation
                import asyncio
                exec_result = await asyncio.to_thread(
                    ExecutionTester.run_server_safe, cmd_to_run, project_path, final_port, 20
                )
                
                PortManager.release_port(final_port)
                
                # Dump logs
                dump_dir = "logs/runtime" if exec_result.is_stable else "logs/crashes"
                dump_file = os.path.join(dump_dir, f"exec_{task.id}.json")
                with open(dump_file, "w") as f:
                    json.dump(exec_result.model_dump(), f, indent=2)

                if not exec_result.is_stable:
                    return AgentResponse(agent_name=self.name, status=TaskStatus.FAILED, output=exec_result.model_dump(), logs=[f"Runtime health check failed. Crash report saved to {dump_file}"])

                output_dict = exec_result.model_dump()
                output_dict["active_port"] = final_port
                
                return AgentResponse(
                    agent_name=self.name,
                    status=TaskStatus.COMPLETED,
                    output=output_dict,
                    logs=[f"Runtime validation passed on port {final_port}. Report saved to {dump_file}"]
                )
            else:
                # Use ExecutionTester for safe standard execution
                import asyncio
                exec_result = await asyncio.to_thread(
                    ExecutionTester.run_safe, command, project_path, 120
                )
                status = TaskStatus.COMPLETED if exec_result.is_stable else TaskStatus.FAILED

                dump_dir = "logs/runtime" if exec_result.is_stable else "logs/crashes"
                dump_file = os.path.join(dump_dir, f"exec_{task.id}.json")
                with open(dump_file, "w") as f:
                    json.dump(exec_result.model_dump(), f, indent=2)

                return AgentResponse(
                    agent_name=self.name,
                    status=status,
                    output=exec_result.model_dump(),
                    logs=[f"Execution {'succeeded' if status == TaskStatus.COMPLETED else 'failed'} in {exec_result.duration}s. Report saved to {dump_file}"]
                )
            
        except Exception as e:
            self.log(f"Terminal Crash: {str(e)}", "error")
            return AgentResponse(
                agent_name=self.name, status=TaskStatus.FAILED,
                output={"error": str(e)}, logs=[f"CRASH: {str(e)}"]
            )
