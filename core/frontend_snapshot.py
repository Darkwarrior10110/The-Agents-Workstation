import os
from typing import Dict, Any
from core.logger import system_logger

class FrontendSnapshotGenerator:
    """
    Lightweight helper to provide agents with read-only awareness 
    of the frontend project structure (UI components, pages, styles).
    """
    IGNORED_DIRS = {"node_modules", ".next", ".nuxt", "build", "dist", ".git", "__pycache__"}
    ALLOWED_EXTS = {".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".sass", ".json"}
    
    @staticmethod
    def generate_snapshot(root_path: str, max_depth: int = 5) -> Dict[str, Any]:
        tree = []
        if not os.path.exists(root_path):
            return {"directory_tree": tree, "status": "Directory not found"}
        
        try:
            for current_root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if d not in FrontendSnapshotGenerator.IGNORED_DIRS and not d.startswith(".")]
                depth = current_root.replace(root_path, '').count(os.sep)
                if depth > max_depth:
                    continue
                    
                rel_path = os.path.relpath(current_root, root_path)
                
                valid_files = [f for f in files if any(f.endswith(ext) for ext in FrontendSnapshotGenerator.ALLOWED_EXTS)]
                if valid_files:
                    if rel_path != ".":
                        tree.append(f"DIR: {rel_path}/")
                    for f in valid_files:
                        file_rel = os.path.join(rel_path, f) if rel_path != "." else f
                        tree.append(f"FILE: {file_rel}")
        except Exception as e:
            system_logger.error(f"[FRONTEND SNAPSHOT] Failed: {str(e)}")
            
        return {
            "directory_tree": tree,
            "note": "Read-only snapshot of frontend files to ensure UI component reuse and prevent duplication."
        }
