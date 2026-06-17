import os
import re
from typing import Dict, Any
from core.logger import system_logger

class FrontendDependencyMapBuilder:
    """
    Lightweight regex-based dependency analyzer to map imports, exports,
    and API calls across frontend files without executing or requiring heavy ASTs.
    """
    IGNORED_DIRS = {"node_modules", ".next", ".nuxt", "build", "dist", ".git", "__pycache__"}
    ALLOWED_EXTS = {".js", ".jsx", ".ts", ".tsx"}
    MAX_FILE_SIZE = 200 * 1024 # 200KB safeguard
    
    @staticmethod
    def build(root_path: str) -> Dict[str, Any]:
        result = {"files": {}}
        if not os.path.exists(root_path):
            return result
            
        import_re = re.compile(r'import\s+.*?\s+from\s+[\'"](.*?)[\'"]')
        export_re = re.compile(r'export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+([A-Za-z0-9_]+)')
        api_re = re.compile(r'(?:fetch|axios\.(?:get|post|put|delete|patch))\s*\(\s*[\'"`](.*?)[\'"`]')
        
        try:
            for current_root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if d not in FrontendDependencyMapBuilder.IGNORED_DIRS and not d.startswith(".")]
                for f in files:
                    if not any(f.endswith(ext) for ext in FrontendDependencyMapBuilder.ALLOWED_EXTS):
                        continue
                        
                    full_path = os.path.join(current_root, f)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    if os.path.getsize(full_path) > FrontendDependencyMapBuilder.MAX_FILE_SIZE:
                        continue
                        
                    try:
                        with open(full_path, "r", encoding="utf-8") as file_obj:
                            content = file_obj.read()
                            
                        imports = list(set(import_re.findall(content)))
                        exports = list(set(export_re.findall(content)))
                        api_calls = list(set(api_re.findall(content)))
                        
                        if imports or exports or api_calls:
                            result["files"][rel_path] = {
                                "imports": imports,
                                "exports": exports,
                                "api_calls": api_calls
                            }
                    except Exception as e:
                        system_logger.warning(f"[FRONTEND DEP MAP] Failed to parse {rel_path}: {str(e)}")
        except Exception as e:
            system_logger.error(f"[FRONTEND DEP MAP] Catastrophic failure: {str(e)}")
            
        return result
