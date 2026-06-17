import os
import ast
from typing import Dict, Any
from core.logger import system_logger

class DependencyMapBuilder:
    """
    Lightweight AST-based dependency analyzer to map imports, classes, functions,
    and FastAPI routes across the project, preventing generation duplication.
    """
    
    IGNORED_DIRS = {"__pycache__", "venv", "node_modules", ".git", ".pytest_cache"}
    MAX_FILE_SIZE = 1024 * 1024  # 1MB safeguard
    MAX_DEPTH = 5

    @staticmethod
    def build(root_path: str) -> Dict[str, Any]:
        result = {
            "files": {},
            "symbols": {},
            "imports_graph": {}
        }
        
        if not os.path.exists(root_path):
            return result
            
        try:
            for current_root, dirs, files in os.walk(root_path):
                # Prune ignored directories in-place
                dirs[:] = [d for d in dirs if d not in DependencyMapBuilder.IGNORED_DIRS]
                
                depth = current_root.replace(root_path, '').count(os.sep)
                if depth > DependencyMapBuilder.MAX_DEPTH:
                    continue
                    
                for f in files:
                    if not f.endswith(".py"):
                        continue
                        
                    full_path = os.path.join(current_root, f)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    try:
                        if os.path.getsize(full_path) > DependencyMapBuilder.MAX_FILE_SIZE:
                            continue
                            
                        with open(full_path, "r", encoding="utf-8") as file_obj:
                            content = file_obj.read()
                            
                        tree = ast.parse(content)
                        file_data = DependencyMapBuilder._parse_ast(tree)
                        
                        result["files"][rel_path] = file_data
                        result["imports_graph"][rel_path] = file_data["imports"]
                        
                        # Populate global symbols map
                        for cls_name in file_data["classes"]:
                            result["symbols"][cls_name] = rel_path
                        for func_name in file_data["functions"]:
                            result["symbols"][func_name] = rel_path
                            
                    except SyntaxError:
                        system_logger.warning(f"[DEPENDENCY MAP] Syntax error in {rel_path}, skipping file.")
                    except Exception as e:
                        system_logger.warning(f"[DEPENDENCY MAP] Failed to parse {rel_path}: {str(e)}")
                        
        except Exception as e:
            system_logger.error(f"[DEPENDENCY MAP] Catastrophic failure during build: {str(e)}")
            # Gracefully fallback to the empty map skeleton
            pass
            
        return result

    @staticmethod
    def _parse_ast(tree: ast.AST) -> Dict[str, list]:
        data = {
            "imports": [],
            "classes": [],
            "functions": [],
            "routes": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    data["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    data["imports"].append(node.module)
            elif isinstance(node, ast.ClassDef):
                data["classes"].append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                data["functions"].append(node.name)
                # Naive FastAPI route decorator extraction
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in ["get", "post", "put", "delete", "patch"]:
                            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                data["routes"].append(dec.args[0].value)
                            else:
                                data["routes"].append(dec.func.attr)
                                
        # Deduplicate
        data["imports"] = list(set(data["imports"]))
        data["classes"] = list(set(data["classes"]))
        data["functions"] = list(set(data["functions"]))
        data["routes"] = list(set(data["routes"]))
        
        return data
