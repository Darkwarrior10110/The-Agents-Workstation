import os
from typing import Dict, Any, List

class ProjectSnapshotGenerator:
    """
    Lightweight helper to provide agents with read-only awareness 
    of the current physical project structure.
    """
    
    IGNORED_DIRS = {"__pycache__", "venv", ".git", "node_modules", ".pytest_cache"}
    
    @staticmethod
    def generate_snapshot(root_path: str, max_depth: int = 4) -> Dict[str, Any]:
        if not os.path.exists(root_path):
            return {"directory_tree": [], "status": "Directory not initialized yet"}
            
        tree: List[str] = []
        for current_root, dirs, files in os.walk(root_path):
            # Prune ignored directories in-place
            dirs[:] = [d for d in dirs if d not in ProjectSnapshotGenerator.IGNORED_DIRS]
            
            # Calculate depth relative to project root
            depth = current_root.replace(root_path, '').count(os.sep)
            if depth > max_depth:
                continue
                
            rel_path = os.path.relpath(current_root, root_path)
            if rel_path != ".":
                tree.append(f"DIR: {rel_path}/")
                
            for f in files:
                file_rel = os.path.join(rel_path, f) if rel_path != "." else f
                tree.append(f"FILE: {file_rel}")
                
        return {
            "directory_tree": tree,
            "note": "Read-only snapshot of existing files to ensure import consistency and prevent duplication."
        }
