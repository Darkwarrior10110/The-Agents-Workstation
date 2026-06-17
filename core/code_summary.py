import os
import ast
from typing import Dict, Any
from core.logger import system_logger

class CodeSummaryBuilder:
    """
    Lightweight AST-based semantic analyzer to build a read-only summary 
    of module purposes, exports, and high-level responsibilities.
    """
    
    IGNORED_DIRS = {"__pycache__", "venv", "node_modules", ".git", ".pytest_cache"}
    MAX_FILE_SIZE = 1024 * 1024  # 1MB safeguard
    MAX_DEPTH = 5

    @staticmethod
    def build(root_path: str) -> Dict[str, Any]:
        summaries = {}
        
        if not os.path.exists(root_path):
            return summaries
            
        try:
            for current_root, dirs, files in os.walk(root_path):
                # Prune ignored directories in-place
                dirs[:] = [d for d in dirs if d not in CodeSummaryBuilder.IGNORED_DIRS]
                
                depth = current_root.replace(root_path, '').count(os.sep)
                if depth > CodeSummaryBuilder.MAX_DEPTH:
                    continue
                    
                for f in files:
                    if not f.endswith(".py"):
                        continue
                        
                    full_path = os.path.join(current_root, f)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    try:
                        if os.path.getsize(full_path) > CodeSummaryBuilder.MAX_FILE_SIZE:
                            continue
                            
                        with open(full_path, "r", encoding="utf-8") as file_obj:
                            content = file_obj.read()
                            
                        tree = ast.parse(content)
                        summaries[rel_path] = CodeSummaryBuilder._summarize_ast(tree)
                            
                    except SyntaxError:
                        system_logger.warning(f"[CODE SUMMARY] Syntax error in {rel_path}, skipping file.")
                    except Exception as e:
                        system_logger.warning(f"[CODE SUMMARY] Failed to parse {rel_path}: {str(e)}")
                        
        except Exception as e:
            system_logger.error(f"[CODE SUMMARY] Catastrophic failure during build: {str(e)}")
            # Gracefully fallback to empty dictionary on unrecoverable errors
            pass
            
        return summaries

    @staticmethod
    def _summarize_ast(tree: ast.AST) -> Dict[str, Any]:
        # Extract module-level docstring to serve as the "purpose"
        purpose = ast.get_docstring(tree) or "No module docstring provided."
        if len(purpose) > 200:
            purpose = purpose[:197] + "..."
            
        exports = []
        depends_on = []
        routes = []
        
        # We only check top-level nodes for exported entities
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    depends_on.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    depends_on.append(node.module)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    exports.append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    exports.append(node.name)
                # Attempt to extract FastAPI-like route endpoints
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in ["get", "post", "put", "delete", "patch"]:
                            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                routes.append(f"{dec.func.attr.upper()} {dec.args[0].value}")
                            else:
                                routes.append(dec.func.attr.upper())

        return {
            "purpose": purpose,
            "exports": list(set(exports)),
            "depends_on": list(set(depends_on)),
            "routes": list(set(routes))
        }
