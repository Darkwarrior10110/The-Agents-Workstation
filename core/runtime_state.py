import asyncio
import time
from typing import Dict, Any, List
from core.logger import system_logger

class RuntimeState:
    """
    Authoritative, read-only state manager for the workstation.
    Tracks live execution for dashboard observability. Zero simulation.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RuntimeState, cls).__new__(cls)
            cls._instance.connections = []
            cls._instance.state = {
                "goal": "Idle",
                "status": "Online",
                "uptime_start": time.time(),
                "agents": {
                    "planner": {"status": "Idle", "task": ""},
                    "backend": {"status": "Idle", "task": ""},
                    "frontend": {"status": "Idle", "task": ""},
                    "terminal": {"status": "Idle", "task": ""},
                    "supervisor": {"status": "Idle", "task": ""},
                    "debug": {"status": "Idle", "task": ""},
                    "runtime_repair": {"status": "Idle", "task": ""}
                },
                "telemetry": {
                    "artifacts_generated": 0,
                    "llm_requests": 0,
                    "repair_attempts": 0
                },
                "llm_gateway": {
                    "active_provider": "None",
                    "active_model": "None",
                    "key_index": "None",
                    "health": "Healthy"
                },
                "files": [],
                "timeline": []
            }
        return cls._instance

    def get_state(self) -> Dict[str, Any]:
        # Inject the live server time formatting into the state request
        self.state["server_time"] = time.strftime("%I:%M:%S %p", time.localtime())
        return self.state

    def push_event(self, event_type: str, data: Any):
        """Updates internal state and broadcasts to all WebSocket listeners."""
        try:
            if event_type == "goal_started":
                self.state["goal"] = data.get("goal", "")
                self.state["status"] = "Generating"
                # Clear previous mission data
                self.state["files"] = []
                self.state["timeline"] = []
                self.state["telemetry"] = {"artifacts_generated": 0, "llm_requests": 0, "repair_attempts": 0}
                for a in self.state["agents"]:
                    self.state["agents"][a] = {"status": "Idle", "task": ""}
            elif event_type == "agent_status":
                agt = data.get("agent", "").lower()
                if agt in self.state["agents"]:
                    self.state["agents"][agt]["status"] = data.get("status", "Idle")
                    self.state["agents"][agt]["task"] = data.get("task", "")
            elif event_type == "file_generated":
                path = data.get("path")
                if path and path not in self.state["files"]:
                    self.state["files"].append(path)
                self.state["telemetry"]["artifacts_generated"] += 1
            elif event_type == "increment_telemetry":
                key = data.get("key")
                if key in self.state["telemetry"]:
                    self.state["telemetry"][key] += 1
            elif event_type == "goal_completed":
                self.state["status"] = "Idle"
            elif event_type == "goal_failed":
                self.state["status"] = "Failed"
            elif event_type == "llm_status":
                self.state["llm_gateway"].update(data)
            elif event_type == "log":
                log_entry = {
                    "timestamp": time.time(),
                    "agent": data.get("agent", "SYSTEM"),
                    "message": data.get("message", ""),
                    "level": data.get("level", "info")
                }
                self.state["timeline"].append(log_entry)
                if len(self.state["timeline"]) > 100:
                    self.state["timeline"].pop(0)

            # Thread-safe queue distribution
            self.state["server_time"] = time.strftime("%I:%M:%S %p", time.localtime())
            payload = {"type": event_type, "data": data, "full_state": self.state}
            for q in self.connections:
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass
                
        except Exception as e:
            system_logger.error(f"[OBSERVABILITY] Failed to push event {event_type}: {str(e)}")

state_manager = RuntimeState()
