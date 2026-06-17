from typing import Dict, Any, List, Optional
from core.logger import system_logger
from pydantic import BaseModel

class ProjectMap(BaseModel):
    routes: List[str] = []
    models: List[str] = []
    components: List[str] = []
    dependencies: List[str] = []

class SharedMemory:
    """
    Centralized memory manager for tracking project state, architecture map,
    and repair history to make agents STATE-AWARE.
    """
    def __init__(self):
        self.project_map = ProjectMap()
        self.repair_history: List[Dict[str, Any]] = []
        self.generated_files: Dict[str, str] = {} # path -> summary
        self.unstable_agents: Dict[str, int] = {} # agent_name -> failure_count
        self.unstable_files: Dict[str, int] = {} # file_path -> failure_count
        self.failed_patches: Dict[str, List[Dict[str, str]]] = {} # file_path -> list of failed patches
        
    def record_failed_patch(self, path: str, search_block: str, replace_block: str, reason: str = "Applied but failed validation/runtime"):
        if path not in self.failed_patches:
            self.failed_patches[path] = []
        self.failed_patches[path].append({
            "search_block": search_block,
            "replace_block": replace_block,
            "reason": reason
        })
        system_logger.info(f"[MEMORY] Recorded failed patch for {path} to prevent repetition. Reason: {reason}")

    def add_generated_file(self, path: str, summary: str):
        self.generated_files[path] = summary
        system_logger.info(f"[MEMORY] Logged generated file: {path}")
        
    def record_repair(self, task_id: str, issue: str, patch_applied: bool):
        self.repair_history.append({
            "task_id": task_id,
            "issue": issue,
            "patch_applied": patch_applied
        })
        system_logger.info(f"[MEMORY] Recorded repair for task {task_id}")

    def record_failure(self, agent_name: str, file_path: Optional[str]):
        if agent_name:
            self.unstable_agents[agent_name] = self.unstable_agents.get(agent_name, 0) + 1
        if file_path:
            self.unstable_files[file_path] = self.unstable_files.get(file_path, 0) + 1
        system_logger.warning(f"[MEMORY] Logged failure for agent {agent_name} on {file_path}")

    def update_map(self, map_data: Dict[str, List[str]]):
        if "routes" in map_data:
            self.project_map.routes.extend([r for r in map_data["routes"] if r not in self.project_map.routes])
        if "components" in map_data:
            self.project_map.components.extend([c for c in map_data["components"] if c not in self.project_map.components])
            
    def get_context(self) -> Dict[str, Any]:
        return {
            "project_map": self.project_map.dict(),
            "generated_files": self.generated_files,
            "recent_repairs": self.repair_history[-5:], # Keep it lightweight
            "unstable_agents": self.unstable_agents,
            "unstable_files": self.unstable_files,
            "failed_patches": self.failed_patches
        }
