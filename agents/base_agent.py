from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from core.schema import Task, TaskStatus
from core.logger import setup_logger
import abc

class AgentResponse(BaseModel):
    agent_name: str
    status: TaskStatus
    output: Any
    logs: List[str] = []
    metadata: Dict[str, Any] = {}

class BaseAgent(abc.ABC):
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.history: List[Dict[str, Any]] = []
        self.logger = setup_logger(name)

    @abc.abstractmethod
    async def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Execute the given structured task."""
        pass

    def log(self, message: str, level: str = "info"):
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
            
        try:
            from core.runtime_state import state_manager
            state_manager.push_event("log", {"agent": self.name, "message": message, "level": level})
        except ImportError:
            pass

    def __repr__(self):
        return f"Agent(name={self.name}, role={self.role})"
